# Contributing Guide

This file maps every part of the codebase so you can quickly find where to make changes.

## Directory Structure

```
signals/
├── backend/           # FastAPI Python backend
├── frontend/          # Next.js React frontend
├── contracts/         # Solidity smart contracts (Foundry)
├── research/          # Notes and research files
└── README.md          # Project overview
```

---

## Backend (`backend/`)

### Entry Point
- **`main.py`** — FastAPI app, router registration, CORS setup

### Core Logic (`backend/core/`)
| File | Purpose |
|------|---------|
| `orchestrator.py` | Main signal processing pipeline (fetch → validate → kill-switch → agents → score) |
| `scoring.py` | Signal scoring algorithm |
| `killswitch.py` | Token safety kill-switch logic |
| `factbook.py` | Token data aggregation |
| `rate_limiter.py` | API rate limiting |
| `cache.py` | In-memory caching |
| `resilience.py` | Circuit breaker, retry logic |
| `parallel.py` | Async parallel execution helpers |
| `config.py` | Environment settings |

### Services (`backend/services/`)
| File | Purpose |
|------|---------|
| `deepseek.py` | DeepSeek LLM integration |
| `crewat.py` | Crew AI multi-agent orchestration |
| `token_safety_service.py` | Token safety scoring |
| `gmgn_apify_service.py` | GMGN API for trading data |
| `dex_api.py` | DEX market data |
| `moralisapi.py` | Moralis blockchain data |
| `coin_api.py` | CoinGecko prices |
| `twitter_api_v2.py` | Twitter/X sentiment data |
| `vault_service.py` | Vault interactions |
| `reasoning_store.py` | SQLite storage for analysis history |
| `x402_middleware.py` | Payment middleware |

### AI Agents (`backend/services/agents/`)
| File | Purpose |
|------|---------|
| `base.py` | Base agent class |
| `market.py` | Market analysis agent |
| `rug_check.py` | Token rug-pull detection |
| `social.py` | Social media sentiment agent |
| `prediction.py` | Final signal prediction agent |

### Routers (`backend/routers/`)
| File | Endpoints |
|------|-----------|
| `signal.py` | `/signal/*` — Get trading signals |
| `token_scan.py` | `/token/*` — Token analysis |
| `gmgn.py` | `/gmgn/*` — GMGN data |
| `dex.py` | `/dex/*` — DEX data |
| `vault.py` | `/vault/*` — Vault operations |
| `wallet.py` | `/wallet/*` — Wallet info |
| `ai_analysis.py` | `/ai/*` — AI analysis |
| `chat.py` | `/chat/*` | 
| `rl_trade.py` | `/rl/*` — RL trading |
| `cron.py` | `/cron/*` — Scheduled tasks |

### RL Trading Agent (`backend/rl_agent/`)
| File | Purpose |
|------|---------|
| `agentic_trader.py` | Main RL trading agent |
| `strategies.py` | Trading strategies |
| `synthetic_market.py` | Market simulation |
| `real_market_adapter.py` | Live market data |
| `run_simulation.py` | Run backtest |
| `run_buy_vault.py` | Execute vault trades |

### Models (`backend/models/`)
| File | Purpose |
|------|---------|
| `schemas.py` | Pydantic request/response models |
| `agent_responses.py` | Agent output schemas |

### Scripts (`backend/scripts/`)
- `run_auto_cycle.py` — Auto trading cycle
- `run_rl_trade.py` — Run RL trades
- `smoke_test_orchestrator.py` — Test orchestrator

---

## Frontend (`frontend/`)

### Pages (`frontend/app/`)
```
app/
├── (dashboard)/           # Main dashboard routes
│   ├── page.tsx            # Home (signals overview)
│   ├── leaderboard/page.tsx
│   ├── simulation/page.tsx
│   ├── portfolio/page.tsx
│   └── settings/page.tsx
└── dashboard/             # Alternate dashboard routes
    ├── vault/page.tsx
    ├── scan/page.tsx
    ├── research/page.tsx
    └── simulation/page.tsx
```

### Components (`frontend/components/`)
| Directory | Contents |
|-----------|----------|
| `layout/` | `Sidebar.tsx`, `Header.tsx` |
| `dashboard/` | Tables for orders, trades, positions, decisions, agent details |
| `web3/` | Vault stats, deposit/withdraw, trade history, volume chart |
| `simulation/` | RL simulation UI, signal history, analysis panel |
| `charts/` | Performance and market charts |
| `modals/` | Wallet modal, add agent modal |
| `ui/` | Reusable UI components (shadcn/ui) |

### Key Files
- **`frontend/app/(dashboard)/layout.tsx`** — Main layout with sidebar
- **`frontend/components/layout/Sidebar.tsx`** — Navigation
- **`frontend/package.json`** — Dependencies (Next.js 16, React 19, wagmi, ethers)

---

## Smart Contracts (`contracts/`)

### Main Contract
- **`contracts/src/SignalsVault.sol`** — ERC-4626 vault with AI trading

### Files
| File | Purpose |
|------|---------|
| `src/SignalsVault.sol` | Main vault contract |
| `script/Deploy.s.sol` | Deployment script |
| `test/SignalsVault.t.sol` | Tests |

### Commands
```bash
cd contracts
forge install    # Install dependencies
forge build     # Compile
forge test      # Run tests
```

---

## How to Add Features

### 1. Add a New API Endpoint
1. Create/edit router in `backend/routers/`
2. Register in `backend/main.py`
3. Add tests in `backend/tests/`

### 2. Add a New Frontend Page
1. Create route in `frontend/app/`
2. Add components in `frontend/components/`
3. Update `Sidebar.tsx` for navigation

### 3. Add a New AI Agent
1. Create agent class in `backend/services/agents/`
2. Register in `backend/core/orchestrator.py` (Stage 2 or 4)

### 4. Modify Signal Processing
1. Main flow: `backend/core/orchestrator.py`
2. Data fetching: services in `backend/services/`
3. Scoring: `backend/core/scoring.py`
4. Kill-switch: `backend/core/killswitch.py`

---

## Running the Project

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Contracts
cd contracts
forge install
forge build
```

---

## Common Tasks

| Task | File to Edit |
|------|---------------|
| Change signal refresh interval | `backend/core/orchestrator.py` |
| Add new token source | `backend/services/` + `backend/core/factbook.py` |
| Modify vault logic | `contracts/src/SignalsVault.sol` |
| Add UI component | `frontend/components/ui/` + use in page |
| Change scoring weights | `backend/core/scoring.py` |

---

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend lint
cd frontend
npm run lint

# Contract tests
cd contracts
forge test
```