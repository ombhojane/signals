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

This project has comprehensive test suites for frontend, backend, and smart contracts.

### Backend Tests (pytest)

Located in `backend/tests/` with markers for different test categories.

```bash
cd backend
source venv/bin/activate  # or activate your Python environment

# Run all tests
pytest

# Run by marker
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m e2e               # End-to-end tests
pytest -m api               # API endpoint tests
pytest -m service           # Service layer tests

# Run specific test file
pytest tests/test_factbook.py
pytest tests/test_killswitch.py
pytest tests/test_scoring.py
pytest tests/test_services.py
pytest tests/test_social_preprocessor.py
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html
```

### Frontend Tests (Playwright)

Located in `frontend/tests/` with E2E test automation across browsers.

```bash
cd frontend
npm install  # Install dependencies

# Install Playwright browsers (first time only)
npx playwright install chromium

# Run tests (headless)
npm test

# Run tests with interactive UI
npm run test:ui

# Run tests with browser visible
npm run test:headed

# View test report
npm run test:report

# Run specific test file
npx playwright test tests/specific-test.spec.ts

# Run tests in specific browser
npx playwright test --project=chromium
npx playwright test --project='Mobile Chrome'
```

Configuration: See `frontend/playwright.config.ts` for test settings, browser options, and web server configuration.

### Smart Contract Tests (Foundry)

Located in `contracts/test/` with Solidity test files.

```bash
cd contracts

# Install dependencies (first time only)
forge install

# Run all tests
forge test

# Run with verbose output
forge test -v

# Run specific test file
forge test test/SignalsVault.t.sol

# Run specific test
forge test test/SignalsVault.t.sol --match testFunctionName

# Run tests with gas reports
forge test --gas-report

# Run tests in watch mode (re-runs on file changes)
forge test --watch

# Run all tests (headless)
npm test

# Run tests with visible browser
npm run test:headed

# Run tests with Playwright UI
npm run test:ui

# Generate HTML report
npm run test:report
```

#### Available Frontend Tests

- **Landing Page** — Hero, navigation, CTA buttons, stats, sections
- **Navigation & Routing** — Page transitions, mobile nav
- **Vault Page** — Deposit/withdraw forms, inputs, wallet connection
- **Simulation Page** — Controls, analysis panel, search palette
- **Leaderboard Page** — Rankings, time ranges, trade feed
- **Portfolio Page** — Tables, tab switching
- **Settings Page** — Theme, network settings
- **Search Command Palette** — Keyboard shortcuts, navigation
- **UI Components** — Buttons, inputs, keyboard navigation
- **Mobile Responsiveness** — Viewport, bottom nav, touch targets
- **Accessibility** — Lang attribute, focus order, alt text
- **Performance** — Load time, network requests
- **Visual Regression** — Page screenshots
- **Error Handling** — 404 pages, error recovery
- **Authentication Flow** — Wallet connection
- **Data Fetching** — Vault state, charts, tables
- **Interactions** — Hover, click, scroll effects
- **Forms** — Input validation
- **Browser Functions** — Back button, refresh

#### Run Specific Tests

```bash
# Run only Chromium tests
npx playwright test --project=chromium

# Run only mobile tests
npx playwright test --project="Mobile Chrome"

# Run specific test file
npx playwright test tests/site.spec.ts

# Run tests matching pattern
npx playwright test -g "Landing Page"

# Run with retries (CI mode)
CI=true npm test
```

---

### Backend Tests (Pytest)

Tests are located in `backend/tests/` and use pytest.

```bash
# From backend directory
cd backend

# Install test dependencies (if needed)
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Run only service tests
pytest -m service

# Run with coverage
pytest --cov=. --cov-report=html

# Run fast tests only (skip slow)
pytest -m "not slow"
```

#### Available Backend Test Markers

- `unit` — Isolated unit tests with no external dependencies
- `integration` — Integration tests exercising multiple modules
- `api` — API endpoint tests
- `service` — Service layer tests
- `e2e` — End-to-end tests hitting real services

#### Backend Test Files

| File | Tests |
|------|-------|
| `test_scoring.py` | Signal scoring algorithm, weights, action thresholds |
| `test_killswitch.py` | Kill switch triggers, safety checks |
| `test_factbook.py` | Token data caching, factbook |
| `test_social_preprocessor.py` | Tweet cleaning, filtering |
| `test_api.py` | API endpoints, validation, error handling |
| `test_services.py` | Token safety, rate limiting, cache, validators |

---

### Smart Contract Tests (Foundry)

```bash
cd contracts

# Run all tests
forge test

# Run specific test
forge test --match-test testName

# Run with verbose output
forge test -vv

# Check coverage
forge coverage
```

---

### Pre-commit Testing (Run Before Push)

Before pushing to production, run all tests:

```bash
# Frontend
cd frontend
npm run lint
npm test

# Backend
cd backend
pytest -m "unit or api or service"
pytest -m integration --ignore=tests/test_api.py  # Only if backend running

# Smart Contracts
cd contracts
forge test
```

#### Quick Test Alias (add to `.bashrc` or `.zshrc`)

```bash
# Run all tests
export function test-all {
    cd ~/Documents/coding/signals/frontend && npm run lint && npm test
    cd ~/Documents/coding/signals/backend && pytest -m unit
    cd ~/Documents/coding/signals/contracts && forge test
}

