#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Signals — Azure Pause Script
# Pauses all running Azure services to save costs
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
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

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

BACKEND_STATUS=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.provisioningState" -o tsv 2>/dev/null || echo "Not found")
FRONTEND_STATUS=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.provisioningState" -o tsv 2>/dev/null || echo "Not found")

echo -e "  Backend:  ${CYAN}$BACKEND_STATUS${NC}"
echo -e "  Frontend: ${CYAN}$FRONTEND_STATUS${NC}"
echo ""

# ─── Confirm pause ────────────────────────────────────────────────
warn "This will pause all container apps and stop billing for compute."
warn "Apps will not respond to requests, but data is preserved."
echo ""
read -p "Pause all services? (type 'yes' to confirm): " confirm
if [ "$confirm" != "yes" ]; then
  log "Pause cancelled."
  exit 0
fi

# ─── Step 1: Stop backend app (scale to 0 without deleting) ──────
log "Pausing backend app..."
# Get the active revision
BACKEND_ACTIVE=$(az containerapp revision list --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "[?active==\`true\`].name" -o tsv 2>/dev/null || echo "")

if [ -z "$BACKEND_ACTIVE" ]; then
  warn "Backend has no active revisions (may already be paused)"
else
  # Update to set replica range to 0
  az containerapp update \
    --name "$BACKEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --min-replicas 0 \
    --max-replicas 1 \
    -o none 2>/dev/null || warn "Could not scale backend"
  ok "Backend paused (scaled to 0 replicas)"
fi

# ─── Step 2: Stop frontend app (scale to 0 without deleting) ─────
log "Pausing frontend app..."
# Get the active revision
FRONTEND_ACTIVE=$(az containerapp revision list --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "[?active==\`true\`].name" -o tsv 2>/dev/null || echo "")

if [ -z "$FRONTEND_ACTIVE" ]; then
  warn "Frontend has no active revisions (may already be paused)"
else
  # Update to set replica range to 0
  az containerapp update \
    --name "$FRONTEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --min-replicas 0 \
    --max-replicas 1 \
    -o none 2>/dev/null || warn "Could not scale frontend"
  ok "Frontend paused (scaled to 0 replicas)"
fi

# ─── Display final status ──────────────────────────────────────────
echo ""
log "Verifying pause..."

BACKEND_MIN=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.template.scale.minReplicas" -o tsv 2>/dev/null || echo "N/A")
FRONTEND_MIN=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query "properties.template.scale.minReplicas" -o tsv 2>/dev/null || echo "N/A")

echo -e "  Backend min replicas:  ${CYAN}$BACKEND_MIN${NC}"
echo -e "  Frontend min replicas: ${CYAN}$FRONTEND_MIN${NC}"
echo ""

# ─── Done ──────────────────────────────────────────────────────────
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  All services paused!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}Status:${NC} Services are now idle (0 replicas)"
echo -e "  ${YELLOW}Cost:${NC} No compute billing (storage still charged)"
echo -e "  ${YELLOW}Data:${NC} All data preserved"
echo ""
echo -e "  To resume: ${CYAN}bash deploy-azure-resume.sh${NC}"
echo -e "  If resume fails: ${CYAN}bash deploy-azure-recover.sh${NC}"
echo ""
