# CampusOS — Complete Project Walkthrough & User Journey Guide
**Senior Full-Stack Engineer & QA Tester Technical Walkthrough (Milestones 1–6 Complete)**

> **Project:** CampusOS — *"The trusted digital operating system for African universities."*  
> **Buildathon Target:** Quai × Blip Buildathon  
> **Documentation Date:** July 31, 2026 (Africa/Lagos)  
> **Scope:** End-to-End User Journey, Architectural Deep-Dive, API Mapping & Database Schema Guide  
> **Verification Status:** 100% Automated Test Suite Passage (81/81 Tests Passing across Solidity, Python & Next.js)  

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture & System Design](#2-architecture--system-design)
3. [Folder Structure](#3-folder-structure)
4. [Complete End-to-End User Journey](#4-complete-end-to-end-user-journey)
5. [Complete Screen-by-Screen Walkthrough](#5-complete-screen-by-screen-walkthrough)
6. [Comprehensive API Reference Guide](#6-comprehensive-api-reference-guide)
7. [Database Schema & Entity Relationship Mapping](#7-database-schema--entity-relationship-mapping)
8. [Known Bugs & Edge Cases](#8-known-bugs--edge-cases)
9. [Missing Features & Planned Enhancements](#9-missing-features--planned-enhancements)
10. [Suggestions for Architectural Improvement](#10-suggestions-for-architectural-improvement)

---

## 1. Project Overview

**CampusOS** is a specialized digital operating system designed to solve chronic trust deficits, anonymous vendor scams, and payment fraud across African university campuses (starting with Nigerian institutions such as University of Nigeria, Nsukka, University of Jos, and University of Lagos).

### The Core Problem Solved
African university campuses suffer from:
1. **WhatsApp Marketplace Scams:** Anonymous buyers and sellers trading textbooks, electronics, and hostel leases with zero identity accountability.
2. **Fake Payment Screenshots:** Fraudulent bank transfers and receipt manipulation.
3. **Sybil Identity Abuse:** Unverified external actors posing as students.

### The CampusOS Solution
* **Cryptographic Identity Verification:** Institutional email attestation (`.edu.ng`) and student ID document upload verified and anchored to **Quai Network EVM Testnet smart contracts** (`StudentIdentity.sol`) via 32-byte SHA-256 digests. Zero Personally Identifiable Information (PII) is stored on-chain.
* **Quai Campus Wallet:** An EVM-compatible campus wallet supporting off-chain signature challenge binding, an onboarding **+25.0 QUAI welcome faucet deposit**, live NGN fiat conversion (`1 QUAI ≈ 1,500 NGN`), and instant P2P transfers via institutional email, student UUID, or EVM address.
* **Trusted Campus Marketplace & Escrow:** A student-exclusive commerce layer where listings are gated by verified student status and checkout is protected by **Blip Pay checkout APIs** and on-chain **Quai Network Smart Contract Escrow** (`MarketplaceEscrow.sol`).
* **Campus Trust Score Engine (Milestone 6):** A bounded `0–100` reputation score starting at baseline `50`, backed by an immutable PostgreSQL audit trail (`TrustHistory`). Scores increase via positive commerce and peer reviews and decrease via confirmed fraud reports.

---

## 2. Architecture & System Design

CampusOS is engineered as a **Modular Monolith**, segregating domain logic cleanly without premature microservice fragmentation:

```
   +-----------------------------------------------------------------------------+
   |                       NEXT.JS 15.1 APP ROUTER FRONTEND                      |
   |   (React 19, TailwindCSS, shadcn/ui, TanStack Query, Dynamic Lazy Modals)   |
   +-----------------------------------------------------------------------------+
                                      |   (REST HTTP JSON Envelopes / Bearer JWT)
                                      v
   +-----------------------------------------------------------------------------+
   |                        FASTAPI 0.115+ BACKEND API                           |
   |   (/api/v1/users, /verification, /wallet, /marketplace, /orders, /trust...) |
   +-----------------------------------------------------------------------------+
                                      |   (Pydantic v2 DTO Validation)
                                      v
   +-----------------------------------------------------------------------------+
   |                         SERVICE ORCHESTRATION LAYER                         |
   |   (UserService, VerificationService, WalletService, MarketplaceService,     |
   |    PaymentService [with_for_update], OrderService, TrustScoreService)       |
   +-----------------------------------------------------------------------------+
                   |                                           |
                   v (SQLAlchemy 2.0 ORM)                      v (Async Worker Threads)
   +-------------------------------+         +-----------------------------------+
   |       REPOSITORY LAYER        |         |     BLOCKCHAIN & EXTERNAL APIS    |
   |   app.repositories            |         |   QuaiBlockchainService (Web3.py) |
   |   (UserRepo, VerificationRepo,|         |   PaymentService (Blip Pay API)   |
   |    MarketplaceRepo, Trust...) |         |   StorageService (Cloudinary API) |
   +-------------------------------+         +-----------------------------------+
                   |
                   v (Alembic Migrations 0001–0006)
   +-----------------------------------------------------------------------------+
   |              RELATIONAL DATABASE LAYER (PostgreSQL / SQLite StaticPool)     |
   |   13 Normalized Tables (users, trust_history, fraud_reports, orders...)     |
   +-----------------------------------------------------------------------------+
```

---

## 3. Folder Structure

```
/home/user/
├── backend/                       # Python 3.13 FastAPI Backend
│   ├── alembic/                   # SQLAlchemy 2.0 Database Migrations
│   │   └── versions/              # 0001_initial to 0006_create_milestone6_trust_and_fraud_tables
│   ├── app/                       # Application Package
│   │   ├── api/v1/                # REST Controllers (users, verification, wallet, qr, marketplace...)
│   │   ├── contracts/             # Seeded ABI JSONs for Quai EVM Testnet Contracts
│   │   ├── core/                  # Database, Config, Cache, Exceptions, JSON Logger
│   │   ├── middleware/            # Rate Limiting (Redis Lua), Security Headers, Correlation ID
│   │   ├── models/                # 13 SQLAlchemy 2.0 ORM Declarative Models
│   │   ├── repositories/          # Repository Layer Encapsulating SQL Operations
│   │   ├── schemas/               # Pydantic v2 DTO Request/Response Schemas
│   │   ├── scripts/               # Idempotent Demo Seeder (seed_demo.py)
│   │   └── services/              # Domain Business Logic Orchestration
│   ├── scripts/                   # Startup Entrypoint (start.sh) with Auto-Seeding
│   ├── tests/                     # 44 / 44 Passing Pytest Unit, Integration & E2E Suites
│   └── Dockerfile                 # Multi-Stage Non-Root Docker Image
├── frontend/                      # Next.js 15.1 App Router Frontend
│   ├── app/                       # Routes (/, /marketplace, /orders, /wallet, /trust, /verification...)
│   ├── components/                # Atomic UI Components (marketplace, wallet, trust, verification)
│   ├── test/                      # 14 / 14 Passing Vitest Component Tests
│   └── Dockerfile                 # Standalone Node 20 Alpine Docker Image
├── contracts/                     # Solidity 0.8.20 / OpenZeppelin 5.2.0 Contracts
│   ├── contracts/                 # StudentIdentity.sol & MarketplaceEscrow.sol
│   └── test/                      # 23 / 23 Passing Hardhat Solidity Test Suites
├── docker-compose.yml             # Local Development & Staging Compose Stack
├── docker-compose.prod.yml        # Enterprise Production Compose Stack (Memory Limits, Log Rotation)
└── PROJECT_WALKTHROUGH.md         # Master Walkthrough Documentation (This Document)
```

---

## 4. Complete End-to-End User Journey

The following flow illustrates the life of a student onboarding onto CampusOS and executing a secure campus commerce transaction:

```
[1. Student Registration] ---------> POST /api/v1/users (Creates User, Baseline Score = 50)
        |
[2. Submit KYC Documents] ---------> POST /api/v1/verification/upload (Cloudinary + OWASP Magic Bytes)
        |
[3. Admin KYC Approval] -----------> POST /api/v1/verification/admin/{id}/approve
        |                            (+10 Trust Score -> Score = 60, Silver Tier)
        v
[4. Connect Quai Wallet] ----------> POST /api/v1/wallet/connect (Checksummed EVM Address Bound)
        |
[5. Receive Faucet Deposit] -------> POST /api/v1/wallet/faucet (+25.0 QUAI / 37,500 NGN)
        |
[6. Create Verified Listing] ------> POST /api/v1/marketplace/listings (Verified Student Gate Pass)
        |
[7. Buyer Checkout Session] -------> POST /api/v1/payments/checkout-session (Row-Level DB Lock)
        |
[8. Blip Pay Webhook Settlement] --> POST /api/v1/payments/webhook (RFC 2104 HMAC Verified)
        |
[9. Quai Smart Escrow Created] ----> POST /api/v1/escrow (MarketplaceEscrow.sol -> State: FUNDED)
        |
[10. Confirm Delivery & Release] --> POST /api/v1/escrow/{id}/release (State: COMPLETED)
        |                            (+5 Trust Score Awarded to Both Buyer & Seller)
        v
[11. Submit Review] ---------------> POST /api/v1/reviews (Rating >= 4* -> +2 Trust Score)
        |
[12. Leaderboard & Analytics] -----> GET /api/v1/trust/leaderboard (User Ranks Top 5 on Campus)
```

---

## 5. Complete Screen-by-Screen Walkthrough

### 1. Landing & Home (`/`)
* **Purpose:** Introduces CampusOS value proposition, displays flagship statistics, and provides navigation to Marketplace, Wallet, Verification, and Trust dashboards.
* **API Calls:** `GET /health` (status check).

### 2. Marketplace Catalog (`/marketplace`)
* **Purpose:** Displays live P2P campus product listings (textbooks, laptops, hostel leases, tutoring services). Supports filtering by category, search query, condition, and sorting (`newest`, `price_asc`, `price_desc`).
* **API Calls:** `GET /api/v1/marketplace/categories` (60s Redis cache), `GET /api/v1/marketplace/listings` (30s Redis cache, enriched with seller verification badges in 2 SQL queries).
* **Key Components:** `ListingGrid.tsx`, `ListingCard.tsx`, `CategoryCards.tsx`.

### 3. Listing Details & Checkout (`/marketplace/[id]` & `/checkout/[id]`)
* **Purpose:** Shows complete item description, Cloudinary photo gallery, seller trust badge, and stock availability. Clicking **Buy Now** opens the dynamically loaded `CheckoutModal.tsx`.
* **API Calls:** `GET /api/v1/marketplace/listings/{id}`, `POST /api/v1/payments/checkout-session` (applies SQLAlchemy `.with_for_update()` pessimistic lock to prevent overselling when stock=1).

### 4. My Orders & Escrow Management (`/orders` & `/orders/[id]`)
* **Purpose:** Lists active buyer and seller orders. Displays real-time escrow states (`CREATED`, `FUNDED`, `COMPLETED`, `REFUNDED`, `DISPUTED`).
* **API Calls:** `GET /api/v1/orders/buyer/{userId}`, `GET /api/v1/orders/seller/{userId}`, `POST /api/v1/escrow/{id}/release`, `POST /api/v1/reviews/`.
* **Key Components:** `EscrowActions.tsx` (1-click release or dispute initiation).

### 5. Campus Wallet (`/wallet`)
* **Purpose:** Manages Quai Network EVM wallet connection, displays dual-currency balances (`25.5 QUAI` / `38,250 NGN`), provides 1-click testnet faucet claims, and supports P2P token transfers.
* **API Calls:** `POST /api/v1/wallet/connect`, `GET /api/v1/wallet/balance`, `GET /api/v1/wallet/history`, `POST /api/v1/wallet/send`, `POST /api/v1/wallet/faucet`.
* **Key Components:** `BalanceCard.tsx`, `SendModal.tsx`, `DepositModal.tsx`, `WithdrawModal.tsx`, `TransactionList.tsx`.

### 6. Student Verification & QR Card (`/verification/upload` & `/verification/status`)
* **Purpose:** Student KYC document upload and live verification status. Renders the permanent HMAC-SHA256 signed **Campus Identity QR Card**.
* **API Calls:** `POST /api/v1/verification/upload`, `GET /api/v1/verification/status/{id}`, `GET /api/v1/verification/history/{id}`.
* **Key Components:** `UploadForm.tsx`, `CampusIdentityQR.tsx`, `BlockchainStatusMonitor.tsx` (adaptive status polling).

### 7. Trust Score Dashboard & Leaderboard (`/trust` & `/trust/[id]`)
* **Purpose:** Interactive dashboard showing student Trust Score (0–100), reputation tier badge (`Platinum`, `Gold`, `Silver`, `Bronze`, `At-Risk`), immutable audit trail timeline, campus leaderboard, and fraud reporting modal.
* **API Calls:** `GET /api/v1/trust/dashboard/{userId}`, `GET /api/v1/trust/leaderboard`, `GET /api/v1/trust/analytics`, `POST /api/v1/fraud/reports`.
* **Key Components:** `TrustScoreGauge.tsx`, `TrustHistoryTimeline.tsx`, `TrustLeaderboard.tsx`, `PeerReviewModal.tsx`, `FraudReportModal.tsx`.

### 8. Admin Verification Queue (`/admin/verifications`)
* **Purpose:** Administrative interface for reviewing student KYC document submissions, inspecting OWASP-validated Cloudinary URLs, and approving/rejecting verifications.
* **API Calls:** `GET /api/v1/verification/admin/queue`, `POST /api/v1/verification/admin/{id}/approve`, `POST /api/v1/verification/admin/{id}/reject`.

---

## 6. Comprehensive API Reference Guide

All 72 endpoints across 63 documented OpenAPI paths return standardized JSON envelopes:

### Core Users & Authentication (`/api/v1/users` & `/api/v1/auth`)
* `POST /api/v1/users/` — Register a new student account (creates user with starting trust score 50).
* `GET /api/v1/users/{user_id}` — Get user profile and verification status.
* `GET /api/v1/users/email/{email}` — Retrieve user profile by institutional email.

### Institutional Verification & KYC (`/api/v1/verification`)
* `POST /api/v1/verification/send-email-otp` — Dispatch 6-digit email OTP (10-min expiry, 60s cooldown).
* `POST /api/v1/verification/verify-email-otp` — Validate email OTP (enforces 3-attempt brute-force lockout).
* `POST /api/v1/verification/upload` — Submit student ID document (OWASP magic bytes check + Cloudinary URL).
* `GET /api/v1/verification/status/{user_id}` — Get current verification state (`pending`, `approved`, `rejected`).
* `GET /api/v1/verification/history/{user_id}` — Get chronological verification audit trail.
* `GET /api/v1/verification/admin/queue` — Admin endpoint to fetch pending student verifications.
* `POST /api/v1/verification/admin/{id}/approve` — Admin approve verification (`+10` trust score awarded).
* `POST /api/v1/verification/admin/{id}/reject` — Admin reject verification with reason.

### Quai Campus Wallet (`/api/v1/wallet`)
* `POST /api/v1/wallet/connect` — Bind EVM checksummed address via off-chain signature challenge.
* `GET /api/v1/wallet/balance` — Get live QUAI testnet balance and NGN fiat equivalent (`1 QUAI ≈ 1500 NGN`).
* `GET /api/v1/wallet/history` — Get paginated financial ledger transactions.
* `POST /api/v1/wallet/send` — Send P2P transfer by email, user UUID, or EVM address (`+5` trust score reward).
* `POST /api/v1/wallet/faucet` — Claim onboarding welcome faucet deposit (`+25.0 QUAI`).

### Trusted Campus Marketplace (`/api/v1/marketplace`)
* `GET /api/v1/marketplace/categories` — Fetch campus categories (Redis 60s TTL cache).
* `GET /api/v1/marketplace/listings` — Fetch paginated listings (bulk seller enrichment, -90.5% DB queries).
* `POST /api/v1/marketplace/listings` — Create listing (**RBAC Gate:** requires `is_verified_student = True`).
* `GET /api/v1/marketplace/listings/{id}` — Fetch specific listing details.
* `PATCH /api/v1/marketplace/listings/{id}` — Update listing details or inventory count.

### Payments, Orders & Escrow (`/api/v1/payments`, `/api/v1/orders`, `/api/v1/escrow`)
* `POST /api/v1/payments/checkout-session` — Initiate Blip Pay checkout (applies `.with_for_update()` inventory lock).
* `POST /api/v1/payments/webhook` — Blip Pay webhook receiver (RFC 2104 HMAC-SHA256 signature check, $\pm 300\text{s}$ timestamp drift check, 24h Redis nonce replay deduplication).
* `POST /api/v1/orders/` — Create new order linking buyer, seller, and listing.
* `GET /api/v1/orders/buyer/{user_id}` & `/seller/{user_id}` — Get user order histories.
* `POST /api/v1/escrow/` — Create on-chain smart contract escrow (`MarketplaceEscrow.sol`).
* `POST /api/v1/escrow/{id}/deposit` — Buyer deposit funds into escrow (`State: FUNDED`).
* `POST /api/v1/escrow/{id}/release` — Release escrow to seller (`State: COMPLETED`, `+5` trust score).

### Campus Trust Engine, Reviews & Fraud (`/api/v1/trust`, `/api/v1/reviews`, `/api/v1/fraud`)
* `GET /api/v1/trust/dashboard/{user_id}` — Get trust score (0–100), tier badge, and verification status.
* `GET /api/v1/trust/leaderboard` — Get top campus students sorted by `trust_score DESC`.
* `GET /api/v1/trust/history/{user_id}` — Get immutable score change audit trail.
* `POST /api/v1/reviews/` — Submit marketplace or peer review (`+2` / `+1` trust score bonus).
* `POST /api/v1/reviews/{id}/moderate` — Admin review moderation (`approve`, `flag`, `remove` with score rollback).
* `POST /api/v1/fraud/reports` — Submit scam or identity fraud report with Cloudinary evidence URLs.
* `POST /api/v1/fraud/reports/{id}/resolve` — Admin confirm fraud report (`-20` trust score penalty).

---

## 7. Database Schema & Entity Relationship Mapping

```
+------------------+         +-------------------------+         +------------------------+
|      users       |1       *|  student_verifications  |1       *|  verification_history  |
|------------------|---------|-------------------------|---------|------------------------|
| id (UUID PK)     |         | id (UUID PK)            |         | id (UUID PK)           |
| email (Unique)   |         | user_id (FK -> users)   |         | verification_id (FK)   |
| wallet_address   |         | document_url            |         | old_status / new_status|
| trust_score (50) |         | status (pending/appr)   |         | changed_by (FK)        |
+------------------+         +-------------------------+         +------------------------+
        | 1
        |
        +-----------------------------------+-----------------------------------+
        | 1                                 | 1                                 | 1
        | *                                 | *                                 | *
+------------------+         +-------------------------+         +------------------------+
|   transactions   |         |  marketplace_listings   |         |     trust_history      |
|------------------|         |-------------------------|         |------------------------|
| id (UUID PK)     |         | id (UUID PK)            |         | id (UUID PK)           |
| user_id (FK)     |         | seller_id (FK -> users) |         | user_id (FK -> users)  |
| amount / type    |         | category (FK -> cat.id) |         | delta (+10, +5, -20)   |
| tx_hash (Unique) |         | price / stock (locked)  |         | event_type / reason    |
+------------------+         +-------------------------+         +------------------------+
                                        | 1                                 |
                                        | *                                 |
                             +-------------------------+                    |
                             |         orders          |                    |
                             |-------------------------|                    |
                             | id (UUID PK)            |                    |
                             | listing_id (FK)         |                    |
                             | buyer_id / seller_id    |                    |
                             | status / escrow_id      |                    |
                             +-------------------------+                    |
                                        | 1                                 |
                                        | *                                 |
                             +-------------------------+         +------------------------+
                             |     escrow_records      |         |     fraud_reports      |
                             |-------------------------|         |------------------------|
                             | id (UUID PK)            |         | id (UUID PK)           |
                             | order_id (FK -> orders) |         | reported_user_id (FK)  |
                             | onchain_escrow_id       |         | reporter_id (FK)       |
                             | state (CREATED..COMPL)  |         | status (resolved_conf) |
                             +-------------------------+         +------------------------+
```

---

## 8. Known Bugs & Edge Cases

* **BUG-001 (Edge Case — Unregistered Email P2P Recipient):**
  - **Severity:** Low (Edge Case)
  - **Affected File:** `backend/app/services/wallet_service.py`
  - **Description:** Attempting a P2P transfer by email (`student_b@unn.edu.ng`) requires the recipient to already exist in the `users` table. If a student attempts to transfer QUAI to an institutional email that has not yet registered on CampusOS, the request is rejected with `HTTP 404 Not Found` (`Recipient user not found`).
  - **Reproduction Steps:**
    1. Connect wallet for `student-wallet-01`.
    2. Attempt `POST /api/v1/wallet/send` with `recipient = "nonexistent.student@unn.edu.ng"`.
    3. Observe HTTP 404 rejection.

---

## 9. Missing Features & Planned Enhancements

1. **Multi-University Tenant Partitioning (Post-M6 Scope):** Currently, CampusOS defaults campus filtering to single-campus scopes (e.g., University of Jos or UNN). Dedicated tenant ID isolation for multi-campus deployments is planned for enterprise scaling in Milestone 7.
2. **Dedicated Moderator Arbitration UI Tab (Post-M6 Scope):** While backend endpoints for resolving fraud reports (`POST /api/v1/fraud/reports/{id}/resolve`) and escrow disputes (`POST /api/v1/escrow/{id}/resolve`) are fully tested and documented in OpenAPI, a dedicated administrative frontend arbitration dashboard tab will be enhanced in Milestone 7.
3. **Real-Time WebSockets / SSE (Post-M6 Scope):** Frontend components currently use adaptive HTTP polling (`document.hidden` check) for verification confirmation. Replacing polling with Server-Sent Events (SSE) or WebSockets is planned for Milestone 8 (Events).

---

## 10. Suggestions for Architectural Improvement

1. **REC-M7-001 (Compound B-Tree DB Indexing):** Create Alembic migration `0007` adding compound indexes `sa.Index('ix_transactions_user_created', 'user_id', 'created_at')` and `sa.Index('ix_trust_history_user_created', 'user_id', 'created_at')` to eliminate single-column historical index scanning under high production load.
2. **REC-M7-002 (Async Cloudinary Threading):** Wrap synchronous Cloudinary SDK network calls in `app/services/storage_service.py` with `asyncio.to_thread` to ensure zero blocking of the FastAPI async event loop during concurrent upload spikes.
3. **REC-M7-003 (Escrowed Invite P2P Transfers):** Extend `WalletService.send_transfer()` to support escrowing funds for unregistered recipient email addresses, dispatching an invitation email with a claim OTP to resolve `BUG-001`.

---
*Documented and certified by Senior Full-Stack Engineer & QA Tester, CampusOS.*
