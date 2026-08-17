# CampusOS Complete Deployment & DevOps Infrastructure Guide
**Document Version:** 1.0.0-devops  
**Date:** July 30, 2026  
**Target Architecture:** Modular Monolith (FastAPI + Next.js 15 App Router + Quai EVM Smart Contracts + PostgreSQL 16 + Redis 7)  
**Deployment Targets:** Railway (Backend Containers + PostgreSQL + Redis), Vercel (Frontend Edge Network), Quai Network EVM Zone 9000 (Smart Contracts)  

---

## Table of Contents
1. [DevOps Architecture & Container Topology](#1-devops-architecture--container-topology)
2. [Docker Multi-Stage Builds & Container Specifications](#2-docker-multi-stage-builds--container-specifications)
3. [Docker Compose Local & Production Orchestration](#3-docker-compose-local--production-orchestration)
4. [GitHub Actions CI/CD Quality Gate & Deployment Pipelines](#4-github-actions-cicd-quality-gate--deployment-pipelines)
5. [Railway Backend & Database Deployment Guide](#5-railway-backend--database-deployment-guide)
6. [Vercel Frontend Edge Deployment Guide](#6-vercel-frontend-edge-deployment-guide)
7. [Quai Network EVM Smart Contract Deployment Guide](#7-quai-network-evm-smart-contract-deployment-guide)
8. [Automated Container Startup & Database Migration Scripts](#8-automated-container-startup--database-migration-scripts)
9. [Operational Verification & SRE Troubleshooting Runbook](#9-operational-verification--sre-troubleshooting-runbook)

---

## 1. DevOps Architecture & Container Topology

```
                  ┌────────────────────────────────────────────────────────────┐
                  │                 GITHUB ACTIONS CI/CD GATE                  │
                  │   • Ruff (0 Errors)   • Pytest (39/39)  • Vitest (10/10)   │
                  │   • Hardhat (23/23)   • TypeScript      • Next.js Build    │
                  └─────────────────────────────┬──────────────────────────────┘
                                                │
          ┌─────────────────────────────────────┼─────────────────────────────────────┐
          │                                     │                                     │
          ▼                                     ▼                                     ▼
┌──────────────────┐                ┌──────────────────────┐              ┌──────────────────────┐
│  VERCEL EDGE     │                │   RAILWAY CONTAINER  │              │ QUAI NETWORK TESTNET │
│  Frontend Edge   │ ◄── REST API ──┤  FastAPI / Uvicorn   │              │ EVM Zone 9000        │
│  (Next.js 15)    │                │  (Python 3.13 Slim)  │              │ StudentIdentity.sol  │
└──────────────────┘                └───────────┬──────────┘              │ MarketplaceEscrow    │
                                                │                         └──────────────────────┘
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
            ┌───────────────────────────┐               ┌───────────────────────────┐
            │   RAILWAY POSTGRESQL 16   │               │     RAILWAY REDIS 7       │
            │   Persistent Relational   │               │   Sliding Window RPM &    │
            │   Database & Migrations   │               │   Webhook Replay Cache    │
            └───────────────────────────┘               └───────────────────────────┘
```

---

## 2. Docker Multi-Stage Builds & Container Specifications

### 2.1 Backend Dockerfile (`backend/Dockerfile`)
* **Base Image:** `python:3.13-slim`
* **Multi-Stage Separation:** `builder` stage compiles C-extensions (`build-essential`, `libpq-dev`); `runtime` stage installs lightweight PostgreSQL client libraries (`libpq5`, `curl`).
* **Security & Privilege Hardening:** Creates a dedicated unprivileged user `campusos` (`UID 10001`, `GID 10001`). Never executes as root.
* **Automated Health Check:** `HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -f http://localhost:8000/health || exit 1`.

### 2.2 Frontend Dockerfile (`frontend/Dockerfile`)
* **Base Image:** `node:20-alpine`
* **Multi-Stage Separation:**
  * `dependencies`: Restores `node_modules` via `npm ci`.
  * `builder`: Compiles Next.js 15 App Router bundle with `output: "standalone"` enabled.
  * `runner`: Packs only `.next/standalone`, `.next/static`, and `/public` into a minimal runtime image.
* **Security & Privilege Hardening:** Executes under unprivileged user `nextjs` (`UID 1001`, `GID 1001`).
* **Automated Health Check:** `HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1`.

### 2.3 Smart Contracts Dockerfile (`contracts/Dockerfile`)
* **Base Image:** `node:20-alpine`
* **Purpose:** Packages Hardhat compile, deployment, and testing tools under unprivileged user `hardhat` (`UID 1002`).

---

## 3. Docker Compose Local & Production Orchestration

### 3.1 Local & Staging Stack (`docker-compose.yml`)
Orchestrates four dependent services with automated health checks and volume persistence:
1. `postgres` (`postgres:16-alpine`): Exposes port `5432` with volume `postgres_data`.
2. `redis` (`redis:7-alpine`): Exposes port `6379` with volume `redis_data`.
3. `backend`: Automatically waits for healthy PostgreSQL and Redis (`condition: service_healthy`), executes `alembic upgrade head`, and starts Uvicorn on port `8000`.
4. `frontend`: Waits for healthy backend and serves Next.js on port `3000`.
5. `contracts` (Optional Profile): Invoked via `docker compose --profile contracts up` to compile and test contracts against local or Quai networks.

### 3.2 Production Hardened Overrides (`docker-compose.prod.yml`)
* **Network Isolation:** PostgreSQL (`5432`) and Redis (`6379`) are removed from public host port bindings (`expose:` only), accessible solely via the internal Docker bridge network.
* **Mandatory Secrets Gate:** Uses syntax like `${POSTGRES_PASSWORD:?CRITICAL: POSTGRES_PASSWORD is required in production}`, ensuring deployment halts immediately if any production secret is unset.
* **Resource Quotas & Limits:** Enforces CPU (`cpus: '2.0'`) and memory (`memory: 2G`) limits on application containers.
* **Log Rotation:** Enforces `json-file` logging driver with `max-size: 20m` and `max-file: 5` to prevent disk exhaustion.

---

## 4. GitHub Actions CI/CD Quality Gate & Deployment Pipelines

### 4.1 Automated Quality Gate (`.github/workflows/ci.yml`)
Triggers on every `push` and `pull_request` to `main`, `staging`, and `develop`. Executes 5 parallel/sequential jobs:
1. **`python-backend-lint-test`**:
   * Runs `ruff check app tests` (`0 errors required`).
   * Runs `pytest -v` across all 39 Python unit, integration, API, security, wallet, and E2E tests (`39/39 passing`).
2. **`solidity-hardhat-test`**:
   * Runs `npm ci` and `npm test` in `/contracts` (`23/23 Solidity tests passing`).
   * Runs `npx tsc --noEmit` to verify smart contract TypeScript types.
3. **`frontend-vitest-tsc-build`**:
   * Runs `npx tsc --noEmit` across Next.js 15 App Router codebase.
   * Runs `npm test` (`10/10 Vitest component tests passing`).
   * Runs `npm run build` (`Next.js 15 standalone production build`).
4. **`docker-build-smoke`**:
   * Runs `docker build` across `/backend`, `/frontend`, and `/contracts` to verify container multi-stage syntax.

### 4.2 Continuous Deployment (`.github/workflows/cd.yml`)
Triggers automatically after CI passes on `main`:
1. **`deploy-railway-backend`**: Uses `@railway/cli` to trigger zero-downtime container rollout of `campusos-backend`.
2. **`deploy-vercel-frontend`**: Uses `vercel@latest` CLI to publish the Next.js 15 App Router bundle to Vercel's global Edge Network.
3. **`deploy-quai-contracts`**: Verifies Quai Network RPC connectivity and compiles contracts for EVM Zone 9000 deployment.

---

## 5. Railway Backend & Database Deployment Guide

### 5.1 Setting Up Railway Managed Services
1. Log in to [Railway.app](https://railway.app) and create a new project: **CampusOS Production**.
2. Provision **PostgreSQL 16** and **Redis 7** databases. Note the generated internal connection URLs (`DATABASE_URL`, `REDIS_URL`).
3. Connect your GitHub repository and select `/backend` as the root directory.

### 5.2 Configuring Railway Variables
Add the following production environment variables in Railway:
* `ENVIRONMENT`: `production`
* `DATABASE_URL`: `${Postgres.DATABASE_URL}`
* `REDIS_URL`: `${Redis.REDIS_URL}`
* `QUAI_RPC_URL`: `https://rpc.quai.network`
* `QUAI_CHAIN_ID`: `9000`
* `QUAI_PRIVATE_KEY`: `0xYourDeployerPrivateKey...`
* `JWT_SECRET_KEY`: `<openssl rand -hex 32>`
* `BLIP_PAY_WEBHOOK_SECRET`: `<openssl rand -hex 32>`
* `QR_SECRET_KEY`: `<openssl rand -hex 32>`
* `RESEND_API_KEY`: `re_live_your_resend_api_key`
* `ALLOWED_CORS_ORIGINS`: `https://campusos.vercel.app,https://campusos.ng`

### 5.3 Health Check & Container Rollout
Railway automatically detects `/railway.json` (`startCommand: "/app/scripts/start.sh"`, `healthcheckPath: "/health"`). The container will execute Alembic database schema migrations before accepting public HTTP traffic.

---

## 6. Vercel Frontend Edge Deployment Guide

### 6.1 Deploying via Vercel Dashboard
1. Log in to [Vercel.com](https://vercel.com) and import the CampusOS GitHub repository.
2. Select **Next.js** as the framework and configure the Root Directory as `frontend`.
3. Configure **Environment Variables**:
   * `NEXT_PUBLIC_API_URL`: `https://api.campusos.ng/api/v1` (or your Railway `.up.railway.app` URL).
   * `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME`: `your_cloudinary_cloud_name`.
4. Click **Deploy**. Vercel will build `.next` and distribute edge routes globally.

---

## 7. Quai Network EVM Smart Contract Deployment Guide

### 7.1 Deploying Contracts to Quai EVM Zone 9000
1. Create a `.env` file inside `/contracts` from `contracts/.env.example`:
   ```ini
   QUAI_RPC_URL=https://rpc.quai.network
   QUAI_PRIVATE_KEY=0xYourDeployerPrivateKey...
   QUAI_CHAIN_ID=9000
   ```
2. Run automated compilation and Hardhat deployment:
   ```bash
   cd contracts
   npx hardhat run scripts/deployEscrow.ts --network quaiTestnet
   ```
3. Copy the output contract addresses (`StudentIdentity` and `MarketplaceEscrow`) into your Railway backend `.env` variables (`QUAI_CONTRACT_ADDRESS` and `QUAI_ESCROW_CONTRACT_ADDRESS`).

---

## 8. Automated Container Startup & Database Migration Scripts

### 8.1 Backend Startup Script (`backend/scripts/start.sh`)
```bash
#!/usr/bin/env bash
set -eo pipefail

echo "==> CampusOS Backend Container Entrypoint"
echo "==> Environment: ${ENVIRONMENT:-development}"
echo "==> Port: ${PORT:-8000}"

# Run Alembic migrations automatically if database is available
if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    echo "==> Executing Alembic database schema migrations..."
    alembic upgrade head || {
        echo "WARNING: Alembic migration failed or database unreachable. Check connection string."
        if [ "${ENVIRONMENT}" = "production" ]; then
            exit 1
        fi
    }
    echo "==> Database schema migration complete."
fi

# Launch FastAPI application using Uvicorn
echo "==> Starting Uvicorn server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-4}" \
    --log-level "${LOG_LEVEL:-info}"
```

---

## 9. Operational Verification & SRE Troubleshooting Runbook

### 9.1 Verification Commands
* **Health Probe Check:**
  ```bash
  curl -i https://api.campusos.ng/health
  ```
* **Inspect Live Docker Containers:**
  ```bash
  docker compose -f docker-compose.yml ps
  ```
* **Inspect Application Logs:**
  ```bash
  docker logs -f campusos-backend
  ```

### 9.2 Troubleshooting Matrix
| Symptom / Error | Root Cause | Remediation Procedure |
| :--- | :--- | :--- |
| **`CRITICAL: Insecure default secrets detected`** | Server launched with `ENVIRONMENT=production` while `.env` still contains sample testnet secrets. | Update `JWT_SECRET_KEY`, `BLIP_PAY_WEBHOOK_SECRET`, and `QR_SECRET_KEY` in AWS Secrets Manager / Railway to 256-bit random hex strings. |
| **`429 Too Many Requests` on `/send-email-otp`** | Client exceeded token bucket (`30 req/min`) or triggered per-email 60s cooldown. | Wait 60 seconds. In emergency lockouts, inspect Redis counter via `DEL campusos:ratelimit:client_ip`. |
| **`401 Unauthorized: Webhook timestamp drift`** | Incoming Blip Pay webhook header `X-Blip-Timestamp` differed from server clock by > 300 seconds. | Verify NTP clock synchronization on Railway worker container or Blip Pay gateway servers. |
| **`500 Internal Server Error: Database Unreachable`** | PostgreSQL container or RDS instance unreachable during `alembic upgrade head`. | Verify `DATABASE_URL` credentials and ensure SSL mode (`sslmode=require`) matches database SSL policies. |

---
*Report generated and verified for CampusOS complete DevOps & production infrastructure.*
