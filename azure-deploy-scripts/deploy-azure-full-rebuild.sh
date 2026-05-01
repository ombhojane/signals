#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Signals — Azure Full Cleanup & Rebuild Script
# Deletes all containers, registries, and container apps, then redeploys
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

# Ensure az CLI and docker are on PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$PATH"

# ─── Configuration ────────────────────────────────────────────────
RESOURCE_GROUP="signals-rg"
LOCATION="centralindia"
ACR_NAME="signalsacr$(date +%s | tail -c 5)"   # must be globally unique
ENVIRONMENT="signals-env"
BACKEND_APP="signals-backend"
FRONTEND_APP="signals-frontend"

# ─── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[▸]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
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

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: CLEANUP
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
echo -e "${RED}  PHASE 1: CLEANING UP EXISTING RESOURCES${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if resource group exists
if az group exists --name "$RESOURCE_GROUP" --query value -o tsv | grep -q "true"; then
  warn "Resource group '$RESOURCE_GROUP' exists."
  echo ""
  log "Showing current resources in $RESOURCE_GROUP:"
  echo ""
  
  # List all container apps
  CONTAINER_APPS=$(az containerapp list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || true)
  if [ -n "$CONTAINER_APPS" ]; then
    warn "Container Apps found:"
    echo "$CONTAINER_APPS" | while read -r app; do
      echo -e "  ${RED}×${NC} $app"
    done
  fi
  
  # List all ACRs
  ACRS=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || true)
  if [ -n "$ACRS" ]; then
    warn "Container Registries found:"
    echo "$ACRS" | while read -r acr; do
      echo -e "  ${RED}×${NC} $acr"
    done
  fi
  
  echo ""
  read -p "Delete the ENTIRE resource group '$RESOURCE_GROUP' and redeploy fresh? (type 'DELETE' to confirm): " confirm
  if [ "$confirm" != "DELETE" ]; then
    log "Cleanup cancelled. Exiting."
    exit 0
  fi
  
  log "Deleting resource group $RESOURCE_GROUP (this may take a few minutes)..."
  az group delete --name "$RESOURCE_GROUP" --yes --no-wait
  ok "Resource group deletion started."
  
  log "Waiting for deletion to complete..."
  for i in {1..60}; do
    if ! az group exists --name "$RESOURCE_GROUP" --query value -o tsv | grep -q "true"; then
      ok "Resource group deleted successfully."
      break
    fi
    echo -ne "  ${CYAN}Wait: ${i}/60${NC}\r"
    sleep 5
  done
else
  ok "No existing resource group found."
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: FRESH DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  PHASE 2: DEPLOYING FRESH INFRASTRUCTURE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Step 1: Resource Group ───────────────────────────────────────
log "Creating resource group: $RESOURCE_GROUP in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none
ok "Resource group created."

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
ok "Backend image pushed to ACR."

# ─── Step 4: Build & Push Frontend Image (placeholder) ───────────
log "Building frontend Docker image..."
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="https://$BACKEND_APP.placeholder.azurecontainerapps.io" \
  -t "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  ./frontend

docker push "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest"
ok "Frontend image pushed to ACR."

# ─── Step 5: Container Apps Environment ──────────────────────────
log "Creating Container Apps environment..."
az containerapp env create \
  --name "$ENVIRONMENT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  -o none
ok "Container Apps environment created."

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
log "Rebuilding frontend with real backend URL..."
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="$BACKEND_URL" \
  -t "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  ./frontend

docker push "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest"
ok "Frontend image rebuilt and pushed to ACR."

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
echo -e "${GREEN}  ✓ FULL REBUILD COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Frontend:  ${CYAN}$FRONTEND_URL${NC}"
echo -e "  Backend:   ${CYAN}$BACKEND_URL${NC}"
echo -e "  API Docs:  ${CYAN}$BACKEND_URL/docs${NC}"
echo ""
echo -e "  Resource Group: $RESOURCE_GROUP"
echo -e "  ACR:            $ACR_NAME.azurecr.io"
echo ""
echo -e "  To tear down again: ${RED}az group delete --name $RESOURCE_GROUP --yes${NC}"
echo ""
