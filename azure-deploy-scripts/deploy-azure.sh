#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Signals — Azure Deployment Script
# Deploys backend (FastAPI) + frontend (Next.js) to Azure Container Apps
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

# Ensure az CLI and docker are on PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$PATH"

# ─── Configuration (edit these) ────────────────────────────────────
RESOURCE_GROUP="signals-rg"
LOCATION="centralindia"
ACR_NAME="signalsacr$(date +%s | tail -c 5)"   # must be globally unique
ENVIRONMENT="signals-env"
BACKEND_APP="signals-backend"
FRONTEND_APP="signals-frontend"

# ─── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[▸]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ─── Pre-flight checks ────────────────────────────────────────────
command -v az  >/dev/null 2>&1 || fail "Azure CLI not found. Install: https://aka.ms/installazurecli"
command -v docker >/dev/null 2>&1 || fail "Docker not found. Install Docker Desktop."

# Check login
az account show >/dev/null 2>&1 || {
  log "Not logged in to Azure. Opening browser login..."
  az login
}

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
ok "Logged in. Subscription: $SUBSCRIPTION_ID"

# ─── Step 1: Resource Group ───────────────────────────────────────
log "Creating resource group: $RESOURCE_GROUP in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none
ok "Resource group ready."

# ─── Step 2: Azure Container Registry ────────────────────────────
log "Creating Azure Container Registry: $ACR_NAME..."
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true \
  -o none
ok "ACR created: $ACR_NAME"

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

# Login to ACR
log "Logging into ACR..."
az acr login --name "$ACR_NAME"
ok "ACR login successful."

# ─── Step 3: Build & Push Backend Image ──────────────────────────
log "Building backend Docker image..."
docker build --platform linux/amd64 -t "$ACR_LOGIN_SERVER/$BACKEND_APP:latest" ./backend
docker push "$ACR_LOGIN_SERVER/$BACKEND_APP:latest"
ok "Backend image pushed."

# ─── Step 4: Build & Push Frontend Image ─────────────────────────
log "Building frontend Docker image..."

# We'll set the API URL after the backend deploys, but for now use a placeholder
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="https://$BACKEND_APP.placeholder.azurecontainerapps.io" \
  -t "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  ./frontend

docker push "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest"
ok "Frontend image pushed."

# ─── Step 5: Container Apps Environment ──────────────────────────
log "Creating Container Apps environment..."
az containerapp env create \
  --name "$ENVIRONMENT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  -o none
ok "Container Apps environment ready."

# ─── Step 6: Deploy Backend ──────────────────────────────────────
log "Deploying backend container app..."

# Read env vars from .env file (skip comments and empty lines)
ENV_ARGS=""
if [ -f ".env" ]; then
  while IFS= read -r line; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" == \#* ]] && continue
    # Extract key and value
    key="${line%%=*}"
    value="${line#*=}"
    ENV_ARGS="$ENV_ARGS $key=$value"
  done < .env
fi

az containerapp create \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$ACR_LOGIN_SERVER/$BACKEND_APP:latest" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --registry-username "$ACR_NAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars $ENV_ARGS \
  -o none

BACKEND_URL=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
BACKEND_URL="https://$BACKEND_URL"
ok "Backend deployed at: $BACKEND_URL"

# ─── Step 7: Rebuild Frontend with real backend URL ──────────────
log "Rebuilding frontend with backend URL: $BACKEND_URL ..."
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="$BACKEND_URL" \
  -t "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  ./frontend

docker push "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest"
ok "Frontend image rebuilt with correct API URL."

# ─── Step 8: Deploy Frontend ─────────────────────────────────────
log "Deploying frontend container app..."
az containerapp create \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --registry-username "$ACR_NAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  -o none

FRONTEND_URL=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
FRONTEND_URL="https://$FRONTEND_URL"
ok "Frontend deployed at: $FRONTEND_URL"

# ─── Step 9: Update Backend CORS to allow frontend ───────────────
log "Updating backend CORS to allow frontend origin..."
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --set-env-vars "FRONTEND_URL=$FRONTEND_URL" \
  -o none
ok "Backend CORS updated."

# ─── Done ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Signals deployed successfully to Azure!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Frontend:  ${CYAN}$FRONTEND_URL${NC}"
echo -e "  Backend:   ${CYAN}$BACKEND_URL${NC}"
echo -e "  API Docs:  ${CYAN}$BACKEND_URL/docs${NC}"
echo ""
echo -e "  Resource Group: $RESOURCE_GROUP"
echo -e "  ACR:            $ACR_NAME.azurecr.io"
echo ""
echo -e "  To tear down:   ${RED}az group delete --name $RESOURCE_GROUP --yes${NC}"
echo ""
