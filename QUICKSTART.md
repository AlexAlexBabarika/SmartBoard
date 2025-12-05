# Quick Start Guide

Get the AI Investment Scout DAO running in 5 minutes!

## 🚀 Super Quick Demo (No Setup Required)

```bash
# 1. Install Python dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Install frontend dependencies
cd frontend
npm install
cd ..

# 3. Start backend (Terminal 1)
cd backend
uvicorn app.main:app --reload
```

Open new terminal:

```bash
# 4. Start frontend (Terminal 2)
cd frontend
npm run dev
```

Open new terminal:

```bash
# 5. Run demo agent (Terminal 3)
source .venv/bin/activate
python spoon_agent/main.py --demo
```

**🎉 Done!** Open http://localhost:5173 in your browser.

## 📝 What Just Happened?

1. **Backend** is running at http://localhost:8000
   - API endpoints for proposals and voting
   - SQLite database created automatically
   - NEO blockchain calls are simulated

2. **Frontend** is running at http://localhost:5173
   - Beautiful dashboard to view proposals
   - Vote on proposals
   - Create new proposals (demo mode)

3. **Agent** generated a sample investment memo
   - AI analysis simulated (no API key needed)
   - PDF generation
   - IPFS upload simulated
   - Submitted to backend

## 🔧 Next Steps

### Add Real LLM Integration

Create `.env` file in root:
```bash
OPENAI_API_KEY=sk-your-actual-key
DEMO_MODE=false
```

### Add Real IPFS Storage

Get free token from https://web3.storage and add to `.env`:
```bash
WEB3_STORAGE_KEY=your-token-here
```

### Compile Smart Contract

```bash
pip install neo3-boa
cd contracts
./compile_contract.sh
```

### Run Tests

```bash
# All tests
pytest

# Specific tests
pytest backend/tests/ -v
pytest spoon_agent/tests/ -v
pytest contracts/tests/ -v
```

## 🎮 Demo Workflow

1. **View Dashboard**: http://localhost:5173
2. **Connect Wallet**: Click "Connect Wallet" (uses mock wallet)
3. **View Proposals**: See the generated proposal on dashboard
4. **Vote**: Click on proposal → Vote YES or NO
5. **Create Proposal**: Click "Create Proposal" → Fill form or "Load Example"
6. **Finalize**: Close voting on a proposal

## 📁 Key Files

- `backend/app/main.py` - API endpoints
- `spoon_agent/main.py` - AI agent
- `contracts/proposal_contract.py` - Smart contract
- `frontend/src/App.svelte` - Frontend app

## 🐛 Troubleshooting

**Backend won't start?**
```bash
cd backend
pip install -r ../requirements.txt
```

**Frontend won't start?**
```bash
cd frontend
rm -rf node_modules
npm install
```

**Agent fails?**
- It's okay! Demo mode simulates everything
- Check if backend is running at localhost:8000

**No proposals showing?**
- Run the agent: `python spoon_agent/main.py --demo`
- Or create one manually via the UI

## 💡 Tips

- Backend auto-reloads on code changes
- Frontend auto-reloads on code changes
- SQLite database file: `backend/proposals.db`
- Clear database: `rm backend/proposals.db` and restart

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

---

**Happy Hacking! 🚀**

