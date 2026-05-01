#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Signals — Azure Update/Redeploy Script
# Updates existing backend (FastAPI) + frontend (Next.js) without recreating resources
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

# Ensure az CLI and docker are on PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$PATH"

# ─── Configuration ────────────────────────────────────────────────
RESOURCE_GROUP="signals-rg"
LOCATION="centralindia"
ACR_NAME="signalsacr9755"  # Use existing ACR (change if different)
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
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

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

# ─── Verify existing resources ────────────────────────────────────
log "Verifying existing Azure resources..."

if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Resource group '$RESOURCE_GROUP' not found. Please run deploy-azure.sh first."
fi
ok "Resource group exists: $RESOURCE_GROUP"

if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Container registry '$ACR_NAME' not found in $RESOURCE_GROUP"
fi
ok "Container registry exists: $ACR_NAME"

if ! az containerapp env show --name "$ENVIRONMENT" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Container Apps environment '$ENVIRONMENT' not found"
fi
ok "Container Apps environment exists: $ENVIRONMENT"

if ! az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Backend app '$BACKEND_APP' not found. Please run deploy-azure.sh first."
fi
ok "Backend app exists: $BACKEND_APP"

if ! az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Frontend app '$FRONTEND_APP' not found. Please run deploy-azure.sh first."
fi
ok "Frontend app exists: $FRONTEND_APP"

# ─── Get ACR credentials ─────────────────────────────────────────
log "Retrieving ACR credentials..."
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)
ok "ACR credentials retrieved"

# ─── Login to ACR ────────────────────────────────────────────────
log "Logging into ACR: $ACR_LOGIN_SERVER..."
echo "$ACR_PASSWORD" | docker login --username "$ACR_NAME" --password-stdin "$ACR_LOGIN_SERVER" >/dev/null 2>&1
ok "ACR login successful"

# ─── Step 1: Rebuild & Push Backend Image ────────────────────────
log "Building backend Docker image..."
docker build --platform linux/amd64 -t "$ACR_LOGIN_SERVER/$BACKEND_APP:latest" ./backend || fail "Backend build failed"
log "Pushing backend image to ACR..."
docker push "$ACR_LOGIN_SERVER/$BACKEND_APP:latest" || fail "Backend push failed"
ok "Backend image updated"

# ─── Step 2: Update Backend Container App ────────────────────────
log "Updating backend container app..."
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --image "$ACR_LOGIN_SERVER/$BACKEND_APP:latest" \
  -o none || fail "Backend update failed"
ok "Backend updated and redeployed"

# Get updated backend URL
BACKEND_URL=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
BACKEND_URL="https://$BACKEND_URL"
log "Backend URL: $BACKEND_URL"

# ─── Step 3: Rebuild & Push Frontend Image ───────────────────────
log "Building frontend Docker image with backend URL: $BACKEND_URL..."
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="$BACKEND_URL" \
  -t "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  ./frontend || fail "Frontend build failed"

log "Pushing frontend image to ACR..."
docker push "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" || fail "Frontend push failed"
ok "Frontend image updated"

# ─── Step 4: Update Frontend Container App ───────────────────────
log "Updating frontend container app..."
az containerapp update \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --image "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  -o none || fail "Frontend update failed"
ok "Frontend updated and redeployed"

# Get updated frontend URL
FRONTEND_URL=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
FRONTEND_URL="https://$FRONTEND_URL"
log "Frontend URL: $FRONTEND_URL"

# ─── Step 5: Update Backend CORS ──────────────────────────────────
log "Updating backend CORS to allow frontend origin..."
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --set-env-vars "FRONTEND_URL=$FRONTEND_URL" \
  -o none || warn "CORS update failed (non-critical)"
ok "Backend CORS updated"

# ─── Done ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Signals updated successfully on Azure!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Frontend:  ${CYAN}$FRONTEND_URL${NC}"
echo -e "  Backend:   ${CYAN}$BACKEND_URL${NC}"
echo -e "  API Docs:  ${CYAN}$BACKEND_URL/docs${NC}"
echo ""
echo -e "  Resource Group: $RESOURCE_GROUP"
echo -e "  Container Registry: $ACR_NAME.azurecr.io"
echo -e "  Environment: $ENVIRONMENT"
echo ""
echo -e "  ℹ️  Apps are restarting. Check status in 1-2 minutes."
echo ""
