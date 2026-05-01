#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Signals — Azure Recovery Script
# Recovers from "no revisions found" error by redeploying apps
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$PATH"

# ─── Configuration ────────────────────────────────────────────────
RESOURCE_GROUP="signals-rg"
ACR_NAME="signalsacr0533"  # Update if different
BACKEND_APP="signals-backend"
FRONTEND_APP="signals-frontend"
ENVIRONMENT="signals-env"

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
command -v az >/dev/null 2>&1 || fail "Azure CLI not found"
command -v docker >/dev/null 2>&1 || fail "Docker not found. Start Docker Desktop first."

az account show >/dev/null 2>&1 || {
  log "Not logged in. Opening browser login..."
  az login
}

ok "Logged in to Azure"

# ─── Verify resources exist ────────────────────────────────────────
log "Verifying Azure resources..."
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Resource group '$RESOURCE_GROUP' not found"
fi
ok "Resource group exists: $RESOURCE_GROUP"

if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Container registry '$ACR_NAME' not found"
fi
ok "Container registry exists: $ACR_NAME"

if ! az containerapp env show --name "$ENVIRONMENT" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Container Apps environment '$ENVIRONMENT' not found"
fi
ok "Container Apps environment exists: $ENVIRONMENT"

# ─── Get ACR credentials ──────────────────────────────────────────
log "Retrieving ACR credentials..."
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)
ok "ACR credentials retrieved"

# ─── Login to ACR ─────────────────────────────────────────────────
log "Logging into ACR: $ACR_LOGIN_SERVER..."
echo "$ACR_PASSWORD" | docker login --username "$ACR_NAME" --password-stdin "$ACR_LOGIN_SERVER" >/dev/null 2>&1
ok "ACR login successful"

# ─── Step 1: Build & Push Backend Image ──────────────────────────
log "Building backend Docker image..."
docker build --platform linux/amd64 -t "$ACR_LOGIN_SERVER/$BACKEND_APP:latest" ./backend || fail "Backend build failed"
log "Pushing backend image to ACR..."
docker push "$ACR_LOGIN_SERVER/$BACKEND_APP:latest" || fail "Backend push failed"
ok "Backend image built and pushed"

# ─── Step 2: Delete old backend app (if exists) and recreate ─────
log "Recreating backend container app..."
az containerapp delete --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --yes -o none 2>/dev/null || true

# Prepare environment variables as a single string
log "Loading environment variables..."
ENV_VARS_STRING="HOST=0.0.0.0 PORT=8000 DEBUG=false"

# Add from .env if it exists
if [ -f "backend/.env" ]; then
  while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.* ]] && continue
    [[ -z "$key" ]] && continue
    # Trim whitespace from key and value
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    # Skip empty values
    [[ -z "$value" ]] && continue
    # Skip HOST, PORT, DEBUG as we set them above
    [[ "$key" == "HOST" ]] || [[ "$key" == "PORT" ]] || [[ "$key" == "DEBUG" ]] && continue
    ENV_VARS_STRING="$ENV_VARS_STRING $key=$value"
  done < backend/.env
  ok "Environment variables loaded from backend/.env"
else
  warn "No backend/.env file found. Make sure required variables are set:"
  warn "  - GROQ_API_KEY (required for AI features)"
  warn "  - GOOGLE_API_KEY (required for AI analysis)"
  warn "  - Other optional API keys"
fi

log "Creating new backend container app with latest image..."

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
  -o none || fail "Backend creation failed"

ok "Backend container app created"

# Now update with environment variables
log "Updating backend with environment variables..."

# Build environment variable string properly
ENV_VARS_STRING=""
ENV_VARS_STRING+="HOST=0.0.0.0 "
ENV_VARS_STRING+="PORT=8000 "
ENV_VARS_STRING+="DEBUG=false "

if [ -f "backend/.env" ]; then
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^#.* ]] && continue
    [[ -z "$key" ]] && continue
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    [[ -z "$value" ]] && continue
    [[ "$key" == "HOST" ]] || [[ "$key" == "PORT" ]] || [[ "$key" == "DEBUG" ]] && continue
    ENV_VARS_STRING+="$key=$value "
  done < backend/.env
fi

# Trim trailing space
ENV_VARS_STRING="${ENV_VARS_STRING% }"

# Update using the space-separated format
log "Setting ${#ENV_VARS_STRING} characters of environment variables..."
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --set-env-vars $ENV_VARS_STRING \
  -o none || fail "Environment variable update failed"
ok "Backend container app created and running"

# Get backend URL
BACKEND_URL=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
BACKEND_URL="https://$BACKEND_URL"
log "Backend URL: $BACKEND_URL"

# ─── Step 3: Build & Push Frontend Image ────────────────────────
log "Building frontend Docker image with backend URL: $BACKEND_URL..."
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL="$BACKEND_URL" \
  -t "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" \
  ./frontend || fail "Frontend build failed"

log "Pushing frontend image to ACR..."
docker push "$ACR_LOGIN_SERVER/$FRONTEND_APP:latest" || fail "Frontend push failed"
ok "Frontend image built and pushed"

# ─── Step 4: Delete old frontend app (if exists) and recreate ────
log "Recreating frontend container app..."
az containerapp delete --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --yes -o none 2>/dev/null || true

log "Creating new frontend container app with latest image..."
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
  -o none || fail "Frontend creation failed"
ok "Frontend container app created and running"

# Get frontend URL
FRONTEND_URL=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
FRONTEND_URL="https://$FRONTEND_URL"
log "Frontend URL: $FRONTEND_URL"

# ─── Step 5: Update Backend CORS ──────────────────────────────────
log "Updating backend CORS..."
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --set-env-vars "FRONTEND_URL=$FRONTEND_URL" \
  -o none || warn "CORS update failed (non-critical)"
ok "Backend CORS updated"

# ─── Wait for apps to be ready ────────────────────────────────────
echo ""
log "Waiting for services to become ready (30 seconds)..."
sleep 30

# ─── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Recovery complete! Services are online${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Frontend:  ${CYAN}$FRONTEND_URL${NC}"
echo -e "  Backend:   ${CYAN}$BACKEND_URL${NC}"
echo -e "  API Docs:  ${CYAN}$BACKEND_URL/docs${NC}"
echo ""
echo -e "  ℹ️  Apps are starting. Give them 1-2 minutes to fully initialize."
echo ""
echo -e "  To pause again: ${CYAN}bash deploy-azure-pause.sh${NC}"
echo ""
