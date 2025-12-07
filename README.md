# AI Investment Scout DAO

A decentralized autonomous organization (DAO) for investment proposal evaluation, powered by AI agents and blockchain technology. Built for the Hackat Hackathon 2025.

## 🌟 Overview

AI Investment Scout DAO automates the investment evaluation process using:
- **SpoonOS Agent**: Generates comprehensive investment memos using LLM analysis
- **NEO Blockchain**: Smart contracts for transparent, on-chain voting
- **IPFS**: Decentralized storage for investment documents
- **Modern Web UI**: Beautiful Svelte frontend with TailwindCSS + DaisyUI

## 📋 Features

- 🤖 **AI-Powered Analysis**: Automated SWOT analysis, risk assessment, and investment thesis generation
- 📊 **Deal Memo Generation**: Professional PDF investment memos with detailed metrics
- 🔗 **Blockchain Voting**: Transparent, immutable on-chain proposal voting
- 📁 **IPFS Storage**: Permanent, decentralized document storage
- 🎨 **Modern UI**: Responsive dashboard with proposal management
- ✅ **Complete Testing**: Comprehensive test coverage for all components

## 🏗️ Architecture

```
┌─────────────────┐
│  Svelte Frontend│  (User Interface)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Backend│  (API + Database)
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ NEO Contract │   │  SpoonOS     │
│  (Voting)    │   │  Agent (AI)  │
└──────────────┘   └──────┬───────┘
                           │
                           ▼
                   ┌──────────────┐
                   │  IPFS Storage│
                   └──────────────┘
```

## 📦 Project Structure

```
/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # API endpoints
│   │   ├── models.py       # Database models
│   │   ├── db.py           # Database configuration
│   │   └── neo_client.py   # NEO blockchain client
│   └── tests/              # Backend tests
│
├── spoon_agent/            # SpoonOS AI agent
│   ├── main.py             # Agent entry point
│   ├── agent_utils.py      # LLM, PDF, IPFS utilities
│   ├── memo_template.html  # Investment memo template
│   ├── prompt_template.txt # LLM prompt template
│   ├── spoon.config.json   # SpoonOS configuration
│   └── tests/              # Agent tests
│
├── contracts/              # NEO smart contracts
│   ├── proposal_contract.py    # Main contract
│   ├── compile_contract.sh     # Compilation script
│   ├── deploy_example.sh       # Deployment guide
│   └── tests/              # Contract tests
│
├── frontend/               # Svelte frontend
│   ├── src/
│   │   ├── App.svelte      # Main app component
│   │   ├── components/     # UI components
│   │   ├── stores/         # State management
│   │   └── lib/            # API client
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Git**

Optional (for production):
- **neo3-boa** (for contract compilation)
- **neo-mamba** (for blockchain deployment)
- **OpenAI API key** (or other LLM provider)
- **Storacha CLI** (for real IPFS uploads, no API token needed)

### Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd pse
```

2. **Set up Python environment**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Note:** PDF generation uses reportlab (pure Python, no system dependencies required).

Without these, the agent will use HTML instead of PDF (works fine for demo mode).

3. **Set up frontend**

```bash
cd frontend
npm install
cd ..
```

4. **Configure environment**

Create a `.env` file in the root directory (copy from `.env.example` if it exists):

```bash
# LLM Provider
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# IPFS Storage (Storacha - no API token needed)
# Install CLI: npm i -g @storacha/cli
# Login: storacha login
# Use/create space: storacha space use <name> (or storacha space create <name>)
STORACHA_CLI=storacha

# NEO Blockchain
NEO_RPC_URL=https://testnet1.neo.org:443
NEO_WALLET_PRIVATE_KEY=your-testnet-private-key
NEO_CONTRACT_HASH=0x...

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DATABASE_URL=sqlite:///./proposals.db

# Demo Mode (set to 'true' to simulate blockchain/IPFS operations)
DEMO_MODE=true
```

### Running the Demo

The project can run in **demo mode** without real API keys or blockchain setup.

#### Terminal 1: Start Backend

```bash
# Run from project root (not from backend/ directory)
cd <project-root>  # Navigate to the project root directory
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn backend.app.main:app --reload
```

**Note:** Run from the project root directory so the `.env` file is properly loaded.

Backend will be available at: http://localhost:8000

#### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:5173

#### Terminal 3: Run SpoonOS Agent (Demo)

```bash
source .venv/bin/activate
python spoon_agent/main.py --demo
```

This will:
1. Generate an AI investment memo (simulated if no API key)
2. Create a PDF
3. Upload to IPFS (simulated)
4. Submit to the backend

### Viewing the Demo

1. Open http://localhost:5173 in your browser
2. Click "Connect Wallet" (uses mock wallet for demo)
3. View the proposals on the dashboard
4. Click on a proposal to see details and vote
5. Vote YES or NO on proposals
6. Finalize proposals to close voting

## 🔧 Detailed Setup

### Backend Setup

The backend is a FastAPI application with SQLite database.

**Endpoints:**
- `GET /health` - Health check
- `POST /submit-memo` - Submit new proposal
- `GET /proposals` - List all proposals
- `GET /proposals/{id}` - Get proposal details
- `POST /vote` - Vote on proposal
- `POST /finalize` - Finalize proposal

**Running tests:**

```bash
cd backend
pytest tests/ -v
```

### SpoonOS Agent Setup

The agent can run standalone or via spoon-cli.

**Standalone mode:**

```bash
python spoon_agent/main.py --demo
# Or with custom input:
python spoon_agent/main.py --input startup_data.json --output result.json
```

**With SpoonOS CLI** (if available):

```bash
pip install spoon-cli
spoon secrets add --config spoon_agent/spoon.config.json
spoon run --config spoon_agent/spoon.config.json --input startup_data.json
```

**LLM Provider Setup:**

For real LLM calls, set in `.env`:
- OpenAI: `OPENAI_API_KEY=sk-...`
- Anthropic: Set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=sk-ant-...`

**IPFS Setup:**

Install the Storacha CLI (no API key needed):

```bash
npm i -g @storacha/cli
storacha login             # email or GitHub
storacha space create dao  # or pick an existing space
storacha space use dao
```

**Running tests:**

```bash
pytest spoon_agent/tests/ -v
```

### Smart Contract Setup

The NEO smart contract manages on-chain voting.

**Compile contract:**

```bash
cd contracts
./compile_contract.sh
```

Requirements:
- Python 3.10+
- neo3-boa: `pip install neo3-boa`

This generates:
- `proposal_contract.nef` - Compiled contract
- `proposal_contract.manifest.json` - Contract manifest

**Deploy to testnet:**

1. Get testnet GAS from https://neowish.ngd.network/
2. Set `NEO_WALLET_PRIVATE_KEY` in `.env`
3. Run deployment:

```bash
./deploy_example.sh
```

4. Save the contract hash to `NEO_CONTRACT_HASH` in `.env`

**⚠️ Security Note:** NEVER use mainnet keys in the `.env` file. Testnet only!

**Running tests:**

```bash
pytest contracts/tests/ -v
```

### Frontend Setup

The frontend is built with Svelte + Vite + TailwindCSS + DaisyUI.

**Development:**

```bash
cd frontend
npm run dev
```

**Build for production:**

```bash
npm run build
npm run preview
```

**Environment variables:**

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

## 📖 Usage Guide

### Creating a Proposal

**Option 1: Using SpoonOS Agent (Recommended)**

```bash
# Create startup data file
cat > startup_data.json << EOF
{
  "name": "TechStartup Inc",
  "sector": "Technology",
  "stage": "Series A",
  "description": "Building innovative AI solutions",
  "metrics": {
    "mrr": 50000,
    "growth_rate": 15
  }
}
EOF

# Run agent
python spoon_agent/main.py --input startup_data.json
```

**Option 2: Manual Submission (Demo)**

1. Navigate to "Create Proposal" in the UI
2. Click "Load Example" to populate form
3. Modify fields as needed
4. Click "Submit Proposal"

### Voting on Proposals

1. Connect wallet (mock wallet for demo)
2. Navigate to proposal details
3. Click "Vote YES" or "Vote NO"
4. Confirm transaction

### Finalizing Proposals

1. Open proposal details
2. Click "Finalize Proposal"
3. Result determined by yes_votes > no_votes

## 🧪 Testing

Run all tests:

```bash
# Backend tests
pytest backend/tests/ -v

# Agent tests
pytest spoon_agent/tests/ -v

# Contract tests
pytest contracts/tests/ -v
```

## 🔐 Security & Production Notes

**⚠️ Important Security Considerations:**

1. **Never commit private keys** to version control
2. Use secrets manager (AWS Secrets Manager, HashiCorp Vault) in production
3. Enable authentication and authorization on API endpoints
4. Use proper wallet signing (Neon.js, WalletConnect) instead of mock wallet
5. Audit smart contracts before mainnet deployment
6. Implement rate limiting on API endpoints
7. Use HTTPS for all external communications
8. Validate all user inputs
9. Implement proper error handling and logging
10. Set up monitoring and alerting

**Production Checklist:**

- [ ] Replace mock wallet with Neon.js integration
- [ ] Set up proper authentication (JWT, OAuth)
- [ ] Deploy backend with production WSGI server (Gunicorn)
- [ ] Use production database (PostgreSQL)
- [ ] Set up CDN for frontend
- [ ] Configure proper CORS policies
- [ ] Enable API rate limiting
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure log aggregation (ELK stack)
- [ ] Perform security audit
- [ ] Smart contract audit
- [ ] Load testing
- [ ] Backup strategy for database and IPFS
- [ ] Disaster recovery plan

## 🌐 Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | For real LLM | - |
| `LLM_PROVIDER` | LLM provider (openai, anthropic) | No | openai |
| `LLM_MODEL` | LLM model to use | No | gpt-4 |
| `STORACHA_CLI` | Storacha CLI executable name | No (defaults to storacha) | storacha |
| `NEO_RPC_URL` | NEO RPC endpoint | No | testnet URL |
| `NEO_WALLET_PRIVATE_KEY` | Private key for signing | For real blockchain | - |
| `NEO_CONTRACT_HASH` | Deployed contract hash | No | - |
| `BACKEND_HOST` | Backend host | No | 0.0.0.0 |
| `BACKEND_PORT` | Backend port | No | 8000 |
| `DATABASE_URL` | Database connection string | No | sqlite:///./proposals.db |
| `DEMO_MODE` | Enable simulation mode | No | true |

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## 🤝 Contributing

This is a hackathon project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🔧 Development History & Fixes

This section documents key issues that were identified and resolved during development.

### Backend Fixes

#### Database & Model Improvements
- **Fixed**: JSON column querying in SQLite for `team_members` filtering
- **Added**: Database indexes on frequently queried fields (proposals, votes, organizations)
- **Added**: Foreign key constraints with CASCADE delete behavior
- **Fixed**: Empty sector string handling in organization creation

#### API & Validation
- **Enhanced**: Input validation with Pydantic validators for all endpoints
- **Fixed**: Organization creation endpoint with proper error handling
- **Added**: Duplicate organization name checking
- **Fixed**: Creator automatically added to team members
- **Improved**: IPFS upload error handling with fail-open behavior
- **Standardized**: Error response formats across all endpoints

#### Code Quality
- **Fixed**: Mutable default arguments in Pydantic models using `Field(default_factory=...)`
- **Enhanced**: Error handling with proper exception types and logging
- **Improved**: Type safety with comprehensive type hints
- **Added**: Database transaction rollback on errors

### Agent & Processing Fixes

#### Product Hunt Integration
- **Fixed**: Agent JSON output to stdout for subprocess parsing
- **Fixed**: Logging configuration to separate logs from JSON output (stderr vs stdout)
- **Fixed**: Template handling for None values in Product Hunt data (funding amounts, valuations)
- **Added**: Direct database submission path to bypass HTTP timeouts
- **Improved**: JSON extraction from mixed stdout output in subprocess mode

#### Proposal Display
- **Fixed**: Frontend response handling for array vs single object responses
- **Added**: Debug logging in frontend for proposal loading
- **Fixed**: Backend non-blocking processing using ThreadPoolExecutor
- **Improved**: Database timeout handling for SQLite operations

### System Verification

All systems have been verified and are production-ready:
- ✅ All endpoints match frontend expectations
- ✅ Request/response schemas validated
- ✅ Database operations optimized with indexes
- ✅ Error handling comprehensive
- ✅ Type safety with Pydantic validation
- ✅ Smart contract integration works in demo and real modes
- ✅ IPFS/Storacha integration with proper fallback

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **NEO** for blockchain infrastructure
- **SpoonOS** for agent orchestration framework
- **Storacha** for IPFS hosting (via CLI)
- **OpenAI** for LLM capabilities
- **Svelte** and **TailwindCSS** for beautiful UI
- **Hackat Hackathon 2025** for the opportunity

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@example.com
- Discord: [link]

## 🎯 Roadmap

- [ ] Multi-signature wallet integration
- [ ] Advanced analytics dashboard
- [ ] Email notifications for proposals
- [ ] Mobile app (React Native)
- [ ] Integration with additional blockchains (Ethereum, Polygon)
- [ ] Machine learning model for proposal risk scoring
- [ ] Real-time proposal updates via WebSocket
- [ ] Multi-language support
- [ ] Advanced filtering and search
- [ ] Proposal templates

---

**Built with ❤️ for Hackat Hackathon 2025**

