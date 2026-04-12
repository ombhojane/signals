# 🚀 Signals: Web3 Intelligence Platform

> Intelligent Web3 signal analysis, RL-based trading, and vault management for decentralized finance.

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Demo Steps](#demo-steps)
- [Tech Stack](#tech-stack)

---

## 🔴 Problem Statement

### The Challenge in Web3

The cryptocurrency and DeFi ecosystem faces critical pain points:

1. **Information Overload**: Millions of tokens and trading signals, impossible to filter manually
2. **Signal Quality**: Existing alert systems produce too many false positives with low accuracy
3. **Manual Trading**: Retail traders lack sophisticated tools for optimal trade execution
4. **Vault Fragmentation**: Capital scattered across multiple protocols with no unified management
5. **Risk Assessment**: Hard to evaluate token safety and project legitimacy at scale
6. **Slow Execution**: Traditional analysis takes minutes to hours; markets move in seconds

### Target Users

- **Retail Traders**: Need high-quality, actionable signals without noise
- **DeFi Participants**: Want safer vault strategies and capital management
- **Professional Traders**: Require real-time data and automated execution
- **Risk Managers**: Need comprehensive token safety scoring

---

## ✅ Solution

### Core Features

**1. Intelligent Signal Generation**
- Multi-source analysis: Twitter sentiment, on-chain metrics, DEX activity
- AI-powered signal refinement using DeepSeek and Crew AI agents
- Real-time token safety scoring with kill-switch mechanism
- Customizable alert thresholds

**2. RL-Based Agentic Trading**
- Reinforcement learning agent trained on market simulation data
- Autonomous trade execution with risk management
- Portfolio optimization and rebalancing
- Real-time market adapter for live trading

**3. Unified Vault Management**
- Multi-protocol vault support (Ethereum, Solana, cross-chain)
- Unified dashboard for position tracking
- Smart contract integration for secure transactions
- Historical activity and performance analytics

**4. Safety & Compliance**
- Token risk assessment framework
- Kill-switch for emergency stops
- Rate limiting and resilience mechanisms
- Comprehensive logging and audit trails

**5. User-Friendly Interface**
- Real-time dashboard with analytics
- Smooth page transitions with Rubik's cube loading animation
- Mobile-responsive design
- Dark theme optimized for long trading sessions

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Dashboard | Vault | Signals | Leaderboard       │   │
│  │  Collapsible Sidebar | Real-time Charts          │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────▼────────────────────────────────┐
│              Backend (FastAPI - Python)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Orchestrator │ AI Agents │ Signal Processor       │   │
│  │ Rate Limiter │ Resilience │ Caching               │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Services Layer                                    │   │
│  │ ┌─────────────┬──────────────┬─────────────────┐ │   │
│  │ │ DeepSeek AI │ Crew Agents  │ Token Safety    │ │   │
│  │ └─────────────┴──────────────┴─────────────────┘ │   │
│  │ ┌─────────────┬──────────────┬─────────────────┐ │   │
│  │ │ Twitter API │ GMGN API     │ Moralis API     │ │   │
│  │ └─────────────┴──────────────┴─────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────────┐ ┌─────▼──────┐ ┌──────▼──────────┐
│   Smart Contracts   │ Database  │ External APIs   │
│ (SignalsVault)  │ (Reasoning) │ (DEX, Twitter)  │
└─────────────────┘ └───────────┘ └─────────────────┘
```

### Key Components

#### Frontend Layer
- **Framework**: Next.js 16.1.3 with React 19
- **Styling**: Tailwind CSS + custom components
- **Animation**: Lottie (Rubik's cube loader) + smooth transitions
- **State Management**: React hooks + Context API
- **Web3**: ethers.js / wagmi for blockchain interaction

#### Backend Layer
- **Framework**: FastAPI (async Python)
- **AI**: DeepSeek, Crew AI (multi-agent reasoning)
- **Caching**: Redis-backed caching layer
- **Rate Limiting**: Token bucket algorithm
- **Resilience**: Circuit breaker, exponential backoff, fallback strategies

#### Data Layer
- **SQLite**: Reasoning store for analysis history
- **External**: Twitter API, GMGN API, Moralis, CoinGecko
- **Blockchain**: Direct smart contract interaction

#### Contract Layer
- **SignalsVault**: ERC-4626 compliant vault contract (Solidity)
- **Deployment**: Foundry framework
- **Networks**: Ethereum, Sepolia testnet

### Data Flow

1. **Signal Generation**
   - Fetch token data from multiple sources (parallel API calls)
   - Run through safety validators and kill-switch checks
   - Process with AI agents (Crew AI) for reasoning
   - Generate ranked signals with confidence scores

2. **User Action**
   - User views signal in dashboard
   - Triggers trade execution or vault deposit
   - Smart contract processes transaction
   - Updated portfolio reflected in real-time

3. **RL Trading Loop**
   - Market adapter feeds live data to RL agent
   - Agent makes autonomous decisions based on trained policy
   - Risk management checks (position sizing, stop-loss)
   - Execution via smart contract or DEX
   - Reward signal updates agent policy

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ (Frontend)
- **Python** 3.11+ (Backend)
- **Solidity** (Smart contracts)
- **Docker** (Optional, for services)

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/ombhojane/hackx.git
cd hackx
```

#### 2. Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys (DeepSeek, Twitter, GMGN, etc.)

# Run backend
uvicorn main:app --reload
# Backend available at http://localhost:8000
```

#### 3. Setup Frontend
```bash
cd frontend
npm install
npm run dev
# Frontend available at http://localhost:3000
```

#### 4. Setup Smart Contracts
```bash
cd contracts
forge install
forge build
forge test

# Deploy to Sepolia testnet
forge script script/Deploy.s.sol --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY --broadcast
```

### Environment Variables

Create `.env` files in `backend/` and `frontend/`:

**Backend** (`backend/.env`):
```
DEEPSEEK_API_KEY=your_key
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
GMGN_API_KEY=your_key
MORALIS_API_KEY=your_key
COINAPI_KEY=your_key
DATABASE_URL=sqlite:///./reasoning.db
```

**Frontend** (`frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_key
NEXT_PUBLIC_VAULT_ADDRESS=0x...
```

---

## 📺 Demo Steps

### Step 1: Start Services
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Optional - Smart contracts
cd contracts
forge test
```

### Step 2: Access Dashboard
- Open `http://localhost:3000` in your browser
- You'll see the **Rubik's cube loading animation** during page transitions
- **Collapsible sidebar** on desktop (click hamburger icon to collapse/expand)

### Step 3: Explore Features

#### 3a. View Signals
1. Navigate to **Signals** tab in sidebar
2. View AI-generated trading signals with safety scores
3. Signals refresh every 60 seconds with latest on-chain data
4. Interact with signal details to see reasoning

#### 3b. Manage Vault
1. Go to **Vault** section
2. Connect wallet using the button in sidebar
3. View current positions and performance
4. Execute deposit/withdraw transactions
5. Check historical activity

#### 3c. RL Trading Simulation
1. Open **Explore** (Simulation) tab
2. Run RL agent in simulated market environment
3. Observe autonomous trading decisions
4. View agent performance metrics

#### 3d. Leaderboard
1. Navigate to **Proof** tab
2. See top-performing traders
3. View verified vault returns
4. Compare strategies

### Step 4: Test Page Transitions
1. Click between different pages (Vault → Explore → Leaderboard, etc.)
2. Observe **smooth fade-in animation** with Rubik's cube loader
3. Notice **collapsible sidebar** behavior:
   - On desktop: Click the menu icon to collapse/expand
   - On mobile: Bottom navigation bar appears automatically

### Step 5: Mobile Experience
1. Resize browser to mobile viewport (< 768px)
2. Sidebar hides automatically
3. Bottom navigation bar appears with all main actions
4. All animations remain smooth and responsive

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 16.1.3
- **Runtime**: React 19.2.3
- **Language**: TypeScript
- **Styling**: Tailwind CSS, Material Symbols Icons
- **Animation**: Lottie React (Rubik's cube)
- **State**: React Hooks + Context API
- **Web3**: ethers.js, wagmi
- **Charts**: Recharts
- **UI Components**: Custom + shadcn/ui

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **AI**: DeepSeek API, Crew AI
- **Async**: asyncio, httpx
- **Caching**: In-memory cache with TTL
- **Database**: SQLite (reasoning store)
- **API Clients**: Twitter API v2, GMGN, Moralis, CoinGecko
- **RL Framework**: Stable-baselines3 (trading agent)

### Smart Contracts
- **Language**: Solidity 0.8.20
- **Framework**: Foundry
- **Standards**: ERC-4626 (vault), ERC-20 (tokens)
- **Testing**: Foundry tests
- **Deployment**: Foundry scripts

### DevOps
- **Version Control**: Git
- **Package Managers**: npm (Node), pip (Python)
- **Environment**: Docker (optional)
- **Testing**: pytest (Python), jest (Node)

---

## 📊 Performance Metrics

- **Signal Generation**: < 5 seconds from API call to ranked signals
- **Page Load**: < 2 seconds with smooth 1.5s loader animation
- **API Responses**: Cached with 60s TTL to reduce redundant calls
- **RL Agent**: Trained on 10,000+ market simulation steps
- **Smart Contract**: Gas optimized, estimated 200k-500k gas per vault operation

---

## 🔒 Security

- **Kill-Switch**: Emergency stop mechanism for tokens flagged as unsafe
- **Rate Limiting**: 100 requests/min per user across all APIs
- **Input Validation**: Comprehensive data validation and sanitization
- **Smart Contract Audit**: Ready for external security review
- **API Keys**: Never exposed in frontend; all sensitive calls through backend

---

## 📝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Support

- **Documentation**: See `/docs` folder for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join our community discussions
- **Contact**: ombhojane@github.com

---

**Built with ❤️ for the Web3 community** | Live on Ethereum & Sepolia Testnet
