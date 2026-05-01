#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Signals — Azure Resume Script
# Resumes paused Azure services
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$PATH"

# ─── Configuration ────────────────────────────────────────────────
RESOURCE_GROUP="signals-rg"
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

# ─── Pre-flight checks ────────────────────────────────────────────
command -v az >/dev/null 2>&1 || fail "Azure CLI not found. Install: https://aka.ms/installazurecli"

az account show >/dev/null 2>&1 || {
  log "Not logged in to Azure. Opening browser login..."
  az login
}

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
ok "Logged in. Subscription: $SUBSCRIPTION_ID"

# ─── Verify resource group exists ─────────────────────────────────
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  fail "Resource group '$RESOURCE_GROUP' not found."
fi
ok "Resource group found: $RESOURCE_GROUP"

# ─── Display current status ────────────────────────────────────────
echo ""
log "Checking app statuses..."

BACKEND_REPLICAS=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.template.scale.minReplicas" -o tsv 2>/dev/null || echo "0")
FRONTEND_REPLICAS=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.template.scale.minReplicas" -o tsv 2>/dev/null || echo "0")

echo -e "  Backend replicas:  ${CYAN}$BACKEND_REPLICAS${NC}"
echo -e "  Frontend replicas: ${CYAN}$FRONTEND_REPLICAS${NC}"
echo ""

# ─── Step 1: Resume backend app ───────────────────────────────────
log "Resuming backend app..."
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --min-replicas 1 \
  --max-replicas 3 \
  -o none || fail "Failed to resume backend. Try: bash deploy-azure-recover.sh"
ok "Backend resumed (scaling to 1-3 replicas)"

# ─── Step 2: Resume frontend app ───────────────────────────────────
log "Resuming frontend app..."
az containerapp update \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --min-replicas 1 \
  --max-replicas 3 \
  -o none || fail "Failed to resume frontend. Try: bash deploy-azure-recover.sh"
ok "Frontend resumed (scaling to 1-3 replicas)"

# ─── Wait for apps to start ────────────────────────────────────────
echo ""
log "Waiting for services to become ready (60 seconds)..."
sleep 60

# ─── Get app URLs ─────────────────────────────────────────────────
BACKEND_URL=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "N/A")
FRONTEND_URL=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "N/A")

# ─── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  All services resumed!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}Status:${NC} Services are coming online"
echo -e "  ${YELLOW}Time to ready:${NC} ~1-2 minutes"
echo -e "  ${YELLOW}Cost:${NC} Compute billing resumed"
echo ""
echo -e "  Frontend:  ${CYAN}https://$FRONTEND_URL${NC}"
echo -e "  Backend:   ${CYAN}https://$BACKEND_URL${NC}"
echo -e "  API Docs:  ${CYAN}https://$BACKEND_URL/docs${NC}"
echo ""
echo -e "  To pause: ${CYAN}bash deploy-azure-pause.sh${NC}"
echo ""
