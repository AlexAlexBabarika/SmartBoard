# Running in Production Mode

## ✅ Current Configuration

Your `.env` file is already set to production mode:
- `DEMO_MODE=false` ✅
- `OPENAI_API_KEY` is set ✅
- Storacha CLI installed and logged in ⚠️

## 🔧 Setup Steps

### 1. Set up Storacha (no API keys)

Storacha now uses local keys + delegations (no API tokens).

```bash
npm i -g @storacha/cli
storacha login             # email or GitHub
storacha space create dao  # or use an existing space name
storacha space use dao     # set the active space for uploads
```

### 2. Verify OpenAI API Key

Your OpenAI key is set. Make sure it's valid and has credits.

### 3. Restart Services

**IMPORTANT:** Restart all services after changing `.env`:

```bash
# Stop current backend (Ctrl+C)
# Then restart:
cd /Users/alexanderbabarika/Desktop/coding/Hackat/Acquisista
source .venv/bin/activate
uvicorn backend.app.main:app --reload
```

### 4. Run Agent in Production Mode

```bash
cd /Users/alexanderbabarika/Desktop/coding/Hackat/Acquisista
source .venv/bin/activate
python spoon_agent/main.py --demo
```

**Note:** Even with `--demo`, if `DEMO_MODE=false`, it will use real APIs.

## 🎯 What Will Happen in Production Mode

### ✅ Real Operations:
- **LLM**: Real OpenAI API calls (costs money)
- **PDF**: Real PDF generation using reportlab (pure Python, no system dependencies)
- **IPFS**: Real uploads to Storacha via CLI (if configured)
- **Blockchain**: Real NEO transactions (if keys valid)

### ⚠️ What to Watch:
- **OpenAI costs**: Each memo generation costs ~$0.01-0.10
- **IPFS uploads**: Free tier has limits
- **NEO transactions**: Requires testnet GAS

## 🧪 Test Production Mode

1. **Check environment is loaded:**
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DEMO_MODE:', os.getenv('DEMO_MODE'))"
   ```

2. **Run agent and watch logs:**
   - Should see "Uploaded to IPFS: [real CID]" instead of "[SIMULATED]"
   - Should see real OpenAI API calls (check your OpenAI dashboard)

3. **Verify in frontend:**
   - Real IPFS CIDs should load PDFs from https://storacha.link/ipfs/<cid>
   - Proposals should have real data from OpenAI

## 🔍 Troubleshooting

### If IPFS upload fails:
- Ensure Storacha CLI is installed (`storacha --version`)
- Run `storacha login` and `storacha space use <space>`
- Re-run with `DEMO_MODE=false` and check logs for CLI output

### If OpenAI fails:
- Verify API key is valid
- Check you have credits
- Verify model name (gpt-4 vs gpt-3.5-turbo)

### If still using simulation:
- Make sure `.env` is in project root
- Restart backend after changing `.env`
- Check logs for "DEMO_MODE" messages

## 💡 Quick Test

Run this to verify production mode:

```bash
python -c "
from dotenv import load_dotenv
from pathlib import Path
import os
import shutil

env_path = Path('.env')
load_dotenv(env_path)

print('DEMO_MODE:', os.getenv('DEMO_MODE'))
print('Has OpenAI Key:', bool(os.getenv('OPENAI_API_KEY')))
print('Storacha CLI present:', bool(shutil.which(os.getenv('STORACHA_CLI','storacha'))))
"
```

Expected output:
```
DEMO_MODE: false
Has OpenAI Key: True
Storacha CLI present: True
```

