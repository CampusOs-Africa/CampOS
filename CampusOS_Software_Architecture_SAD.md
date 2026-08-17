# CampusOS — Software Architecture Document (SAD)

> **Source of Truth:** `CampusOS Software Architecture.pdf`  
> **Project:** CampusOS  
> **Version:** 1.0  
> **Architecture Style:** Modular Monolith (Hackathon MVP) with Microservice-Ready Design  
> **Buildathon Context:** Quai × Blip Buildathon  

---

## 1. Purpose & Core Architectural Principles

This document defines the strict software architecture for **CampusOS**, ensuring a consistent technical approach during the Quai × Blip Buildathon. 

### Core Priorities
* Rapid MVP development
* Scalability & Security
* Blockchain integration (Quai Network) & Payments (Blip Pay)
* API-first development & clear separation of concerns

### Architectural Principles (Strict Guidelines)
1. **Blockchain only where it adds trust.**
2. **Personal data remains off-chain.**
3. **APIs are stateless and documented.**
4. **Modules are loosely coupled.**
5. **Security is built in from day one.**
6. **Mobile-first user experience.**
7. **Clear separation between business logic, persistence, and presentation.**
8. **Every blockchain interaction must provide a tangible benefit to the user or the platform.**

---

## 2. System Overview & High-Level Architecture

CampusOS is structured across five primary layers:

```
+-------------------------------------------------------------+
|               Next.js 15 Frontend (Vercel)                  |
+-------------------------------------------------------------+
                              |
                     HTTPS REST API (JSON)
                              |
+-------------------------------------------------------------+
|               FastAPI Backend (Railway)                     |
|  +-------------------------------------------------------+  |
|  | Auth Module       | Marketplace Module | Wallet Module|  |
|  | Payment Module    | Event Module       | Verification |  |
|  | Trust Module      | Admin Module                      |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
          |                   |                     |
     PostgreSQL          Quai Network          External APIs
(Supabase / Neon)     (Smart Contracts)     (Blip Pay, Cloudinary,
                                              Email Service)
```

### High-Level Request Flow
`Student` ➔ `Frontend (Next.js 15)` ➔ `API Gateway (HTTPS REST API)` ➔ `Business Services (FastAPI)` ➔ `Database / Blockchain / External APIs`

---

## 3. Technology Stack

| Layer | Technologies & Tools | Deployment / Hosting |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15, React, TypeScript, TailwindCSS, shadcn/ui, Framer Motion, React Query, React Hook Form, Zod, Axios, QRCode Library | **Vercel** |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT Authentication | **Railway** |
| **Database** | PostgreSQL, Redis (future) | **Supabase** or **Neon** |
| **Blockchain** | Quai Network, Wallet SDK, Smart Contracts | **Quai Network** |
| **Storage & Integrations** | Cloudinary (Images/Documents), Blip Pay API (Payments), Email Service | Cloudinary / Blip Pay |

---

## 4. Strict Folder Structure

### 4.1 Frontend Folder Structure (`frontend/`)
```
frontend/
├── app/
├── components/
│   ├── wallet/
│   ├── marketplace/
│   ├── events/
│   ├── trust/
│   ├── verification/
│   ├── dashboard/
│   ├── admin/
│   ├── common/
│   └── ui/
├── hooks/
├── services/
├── store/
├── types/
├── utils/
├── styles/
├── public/
└── middleware.ts
```

* **Frontend Route Pages:** `/`, `/login`, `/register`, `/dashboard`, `/wallet`, `/marketplace`, `/listing`, `/checkout`, `/trust`, `/profile`, `/verification`, `/events`, `/admin`

### 4.2 Backend Folder Structure (`backend/`)
```
backend/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── wallet.py
│   │   ├── marketplace.py
│   │   ├── payments.py
│   │   ├── events.py
│   │   ├── verification.py
│   │   ├── trust.py
│   │   ├── reviews.py
│   │   └── admin.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── wallet_service.py
│   │   ├── payment_service.py
│   │   ├── trust_service.py
│   │   ├── verification_service.py
│   │   ├── event_service.py
│   │   └── marketplace_service.py
│   ├── repositories/
│   ├── middleware/
│   ├── core/
│   ├── utils/
│   ├── contracts/
│   └── tests/
└── main.py
```

---

## 5. Module Architecture & Responsibilities

1. **Authentication Module:** Registration, Login, JWT, Role Management, Password Reset.
2. **Verification Module:** Student Verification, Admin Approval, Credential Generation, Blockchain Verification.
3. **Wallet Module:** Wallet Connection, Balance, Transaction History, QR Payments.
4. **Marketplace Module:** Listings, Search, Checkout, Reviews, Escrow.
5. **Trust Module:** Trust Score, Reviews, Fraud Reports, Reputation Engine.
6. **Events Module:** Event Creation, Registration, NFT Ticket, Attendance.
7. **Admin Module:** Moderation, Verification, Reports, Analytics.

---

## 6. Database Schema (PostgreSQL)

```sql
-- Users Table
Users (
  id, name, email, wallet_address, student_id,
  school, faculty, department, level,
  trust_score, verification_status, created_at
);

-- Verification Table
Verification (
  id, user_id, student_id_document, admission_letter,
  status, approved_by, credential_hash, approved_at
);

-- Marketplace Table
Marketplace (
  id, seller_id, title, description,
  category, price, images, status, created_at
);

-- Orders Table
Orders (
  id, buyer_id, listing_id, seller_id,
  amount, payment_hash, status, created_at
);

-- Transactions Table
Transactions (
  id, wallet, receiver, amount,
  tx_hash, status, network, timestamp
);

-- Reviews Table
Reviews (
  id, reviewer, reviewee, rating, comment, created_at
);

-- Events Table
Events (
  id, title, description, date,
  location, price, organizer, nft_enabled
);

-- Tickets Table
Tickets (
  id, event_id, owner, nft_hash, qr_code, checked_in
);
```

---

## 7. Smart Contract Architecture (Quai Network Boundaries)

The architecture defines exactly **5 Smart Contracts** on Quai Network:

| Smart Contract | Required Functions |
| :--- | :--- |
| **1. `StudentIdentity`** | `registerStudent()`, `verifyStudent()`, `revokeStudent()`, `isVerified()`, `getCredentialHash()` |
| **2. `MarketplaceEscrow`** | `createEscrow()`, `deposit()`, `release()`, `refund()`, `cancel()` |
| **3. `TrustRegistry`** | `updateScore()`, `recordReview()`, `recordFraud()`, `getTrustScore()` |
| **4. `CampusEventNFT`** | `mintTicket()`, `transferTicket()`, `verifyTicket()`, `burnTicket()` |
| **5. `ReceiptRegistry`** | `storeReceipt()`, `verifyReceipt()` |

---

## 8. REST API Architecture (FastAPI Endpoints)

```
# Authentication
POST   /auth/register
POST   /auth/login
POST   /auth/logout
GET    /auth/profile

# Verification
POST   /verification/upload
GET    /verification/status
POST   /verification/approve
POST   /verification/reject

# Wallet
GET    /wallet
GET    /wallet/balance
GET    /wallet/history
POST   /wallet/send
POST   /wallet/connect

# Marketplace
GET    /marketplace
POST   /marketplace
GET    /marketplace/{id}
PUT    /marketplace/{id}
DELETE /marketplace/{id}

# Payments
POST   /payments/initiate
POST   /payments/webhook
GET    /payments/history

# Trust
GET    /trust
POST   /trust/review
GET    /trust/history

# Events
POST   /events
GET    /events
POST   /events/register
POST   /events/checkin

# Admin
GET    /admin/users
GET    /admin/reports
POST   /admin/suspend
POST   /admin/approve
```

---

## 9. Blockchain Interaction Flows

### 9.1 Student Payment Flow
`Student` ➔ `Create Payment` ➔ `Blip API` ➔ `Payment Success` ➔ `Backend Verifies` ➔ `Store Transaction` ➔ `Quai Receipt Contract` ➔ `Trust Score Updated` ➔ `Notification Sent`

### 9.2 Student Verification Flow
`Student` ➔ `Upload Documents` ➔ `Admin Approves` ➔ `Generate Credential Hash` ➔ `Write Hash to Quai` ➔ `Verified Badge Appears`

### 9.3 Marketplace Purchase Flow
`Buyer` ➔ `Checkout` ➔ `Blip Payment` ➔ `Escrow Contract` ➔ `Seller Confirms` ➔ `Funds Released` ➔ `Review Requested` ➔ `Trust Score Updated`

### 9.4 Event Registration Flow
`Student` ➔ `Register` ➔ `Payment` ➔ `Mint NFT` ➔ `QR Generated` ➔ `Check-in` ➔ `Attendance Recorded`

---

## 10. Trust Score Engine Specification

* **Initial Starting Score:** `50`
* **Valid Score Range:** `0–100`

### Score Modifiers
```
Positive Events:
  +5   Successful Purchase
  +5   Successful Sale
  +10  Verified Identity
  +2   Positive Review
  +3   Event Attendance

Negative Events:
  -5   Refund
  -10  Fraud Report
  -5   Dispute
  -3   Failed Payment
```

---

## 11. Security & Role-Based Access Control (RBAC)

### Security Controls (Mandatory)
* JWT Authentication & Wallet Signature Verification
* HTTPS & Password Hashing
* Strict Input Validation & Rate Limiting
* Role-Based Access Control (RBAC)
* Cloudinary Signed Uploads
* Prepared SQL Queries (SQLAlchemy ORM)
* Environment Variables & Secrets Manager
* Blockchain Transaction Verification & Webhook Signature Validation (Blip Pay)

### Role Permissions Matrix
| Role | Permitted Areas & Actions |
| :--- | :--- |
| **Student** | Marketplace, Payments, Events, Wallet |
| **Merchant** | Everything Student + Business Dashboard & Analytics |
| **Admin** | Verification, Suspensions, Reports, Analytics, Settings |

---

## 12. Logging, Error Handling & Deployment

* **Required Logging Areas:** Authentication, Payments, Verification, Marketplace, Errors, Blockchain Transactions, API Calls, Admin Actions.
* **Error Handling Infrastructure:** Central Exception Middleware, Validation Errors, Authentication Errors, Blockchain Errors, Payment Failures, Database Failures, Retry Logic, User-Friendly Messages.
* **Deployment Flow:** Internet ➔ Vercel (Next.js 15) ➔ FastAPI (Railway) ➔ PostgreSQL / Cloudinary / Quai Network / Blip Pay.
* **Development Workflow:** GitHub ➔ Feature Branch ➔ Pull Request ➔ Review ➔ Merge ➔ Deploy Preview ➔ Production.

---

## 13. MVP Priorities & Future Scale

### Phase 1 (Must Build - MVP Scope)
* [x] Authentication
* [x] Verified Student Identity
* [x] Wallet Connection
* [x] Marketplace
* [x] Blip Payment Integration
* [x] Quai Transaction Recording
* [x] Trust Score
* [x] Admin Verification

### Phase 2 (If Time Allows)
* NFT Event Tickets, Split Bills, Merchant Dashboard, Push Notifications, Analytics.

### Future Architecture Evolution
When CampusOS grows beyond the MVP, the modular monolith can be split into independent services (**Authentication Service, Identity Service, Marketplace Service, Payment Service, Trust Service, Event Service, Notification Service, Analytics Service**), exposing REST or gRPC APIs through a shared API gateway and event bus.
