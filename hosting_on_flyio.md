# Hosting on Fly.io

This project needs two Fly apps: one for the FastAPI backend and one for the Svelte frontend. Optionally, you can run the Spoon agent as a third app.

## Prerequisites
- Install `flyctl` and log in: `fly auth login`.
- Ensure Docker is available (Fly uses your local Docker daemon to build).
- From the project root: `/Users/alexanderbabarika/Desktop/coding/Hackat/Acquisista`.

## Backend (FastAPI)
1) Create app (no deploy yet):
```
fly launch --name acquisista-api --no-deploy
```

2) Add `Dockerfile.backend` at the repo root:
```
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=8080 \
    DATABASE_URL=sqlite:///./data/proposals.db

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend

RUN useradd -m appuser
USER appuser

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

3) Add `.dockerignore` (root) to keep images slim:
```
.git
.venv
__pycache__
frontend/node_modules
backend/proposals.db
proposals.db
```

4) Add `fly.toml` (root) for the API:
```
app = "acquisista-api"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile.backend"

[env]
  BACKEND_HOST = "0.0.0.0"
  BACKEND_PORT = "8080"
  DATABASE_URL = "sqlite:///./data/proposals.db"
  DEMO_MODE = "true"  # set to false for real mode

[[services]]
  internal_port = 8080
  protocol = "tcp"
  [[services.ports]]
    port = 80
  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
  [services.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

[[mounts]]
  source = "data"
  destination = "/app/data"
```

5) Create volume for SQLite persistence:
```
fly volumes create data --region iad --size 1
```

6) Set secrets (replace values):
```
fly secrets set OPENAI_API_KEY=... NEO_RPC_URL=... NEO_WALLET_PRIVATE_KEY=... NEO_CONTRACT_HASH=... STORACHA_CLI=storacha DEMO_MODE=false
```

7) Deploy backend:
```
fly deploy -c fly.toml
```

8) Health checks: Fly auto-adds, but you can include an HTTP check to `/health` if desired.

## Frontend (Svelte/Vite)
1) From `frontend/`, create the web app:
```
fly launch --name acquisista-web --no-deploy --path .
```

2) Add `frontend/.env.production`:
```
VITE_API_URL=https://acquisista-api.fly.dev
```

3) Add `frontend/Dockerfile`:
```
FROM node:20-slim as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
ENV PORT=8080
EXPOSE 8080
CMD ["serve", "-s", "dist", "-l", "8080"]
```

4) Add `frontend/fly.toml`:
```
app = "acquisista-web"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[[services]]
  internal_port = 8080
  protocol = "tcp"
  [[services.ports]]
    port = 80
  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
  [services.concurrency]
    type = "connections"
    hard_limit = 50
    soft_limit = 45
```

5) Deploy frontend (from `frontend/`):
```
fly deploy -c fly.toml
```

## Optional: Agent as a Worker
- Create a third Fly app (or a Machine) if you want `spoon_agent/main.py` running continuously.
- Reuse the Python base image; set the command to `python spoon_agent/main.py --demo` and supply the same secrets as the API.

## CORS and API URL
- Ensure backend CORS allows `https://acquisista-web.fly.dev` (and any custom domain you add).
- Frontend should point `VITE_API_URL` to the deployed API URL.

## Custom Domains and TLS
- Add domains: `fly certs create <domain>`.
- Point DNS A/AAAA records to Fly’s anycast as instructed by `fly certs`.

## Production Notes
- Set `DEMO_MODE=false` for real LLM/blockchain/IPFS behavior.
- SQLite is fine for small demos; for production, migrate to Postgres (Fly Postgres) and update `DATABASE_URL`.
- Storacha CLI is expected; if you move IPFS uploads server-side, ensure the binary or an HTTP-based upload path exists in the container.

