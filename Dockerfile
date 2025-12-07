FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# Install frontend deps and build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_API_URL=https://smartboard.fly.dev
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM python:3.12.12 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=8080
WORKDIR /app

RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.12.12-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .
# Bring in the built frontend assets
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Install Storacha CLI (requires Node) for real IPFS uploads
RUN apt-get update && \
    apt-get install -y curl ca-certificates gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g @storacha/cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
ENV STORACHA_CLI=/usr/local/bin/storacha

CMD ["/app/.venv/bin/uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
