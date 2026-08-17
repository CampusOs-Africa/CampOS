# CampusOS — Comprehensive Product Requirements & Architecture Summary

> **Sources of Truth:** `CampusOS.pdf` (PRD) & `CampusOS Software Architecture.pdf` (SAD)  
> **Tagline:** Trusted Operating System for University Campuses  
> **Architecture Style:** Modular Monolith (Hackathon MVP) with Microservice-Ready Design  
> **Buildathon Context:** Quai × Blip Buildathon  

---

## 1. Executive Summary & Vision

**CampusOS** is the trusted digital operating system designed to serve as the **identity and commerce layer for university campuses**, starting with African universities.

Traditional payment and marketplace apps focus purely on transactions. In contrast, **CampusOS focuses on trust**: every payment, marketplace purchase, event registration, and peer interaction contributes to a student's **portable Trust Score**. Powered by **Quai Network** (blockchain verification, escrow, and reputation registries) and **Blip Pay API** (secure campus payments), CampusOS eliminates common campus fraud and scams.

* **Core Principles:** 
  1. Blockchain is used strictly where it adds trust; **personal data remains off-chain**.
  2. Stateless, API-first architecture with a mobile-first user experience.
  3. Security and role-based access control built in from day one.

---

## 2. Problem Statement & Solution

### The Problem
University students rely on disconnected, unverified platforms (**WhatsApp, Telegram, Opay, PalmPay, Google Forms, Cash, Excel, School Portals**), resulting in:
* **High Scam Rates:** Fake payment screenshots, anonymous vendor scams, and no accountability.
* **Lack of Reputation:** No portable reputation system or verifiable digital student identity.
* **Friction-Heavy Interactions:** Manual event ticketing, complex bill splitting, and poor user verification.

### The Solution: CampusOS
* **Verified Student Identity:** Admin-approved, blockchain-verified credential hashing on Quai Network.
* **Trust Score Engine:** Dynamic scoring (0–100) reflecting real campus commerce behavior.
* **Escrow-Backed Marketplace:** P2P marketplace integrated with smart contract escrow and Blip Pay checkout.
* **Unified Campus Wallet & Events:** QR code P2P payments and NFT-enabled event ticketing.

---

## 3. Product Goals & Scope Breakdown

### 3.1 Primary Product Goals
1. Create trusted campus commerce and eradicate student marketplace scams.
2. Enable secure P2P and marketplace payments via **Blip Pay API**.
3. Provide verifiable on-chain reputation and identity using **Quai Network** smart contracts.
4. Simplify everyday campus transactions and event registration.

### 3.2 Hackathon MVP Priorities (Must Build)
* [x] **Authentication Module** (JWT, Role Management, RBAC)
* [x] **Verified Student Identity Module** (Document upload, Admin approval, Credential Hash on Quai)
* [x] **Wallet Module** (Connection, Balance, History, QR Payments)
* [x] **Marketplace Module** (Listings, Search, Blip Checkout, Escrow, Reviews)
* [x] **Blip Payment Integration** (Initiate payments & webhook validation)
* [x] **Quai Transaction Recording** (On-chain receipts & trust score proofs)
* [x] **Trust Score Engine** (Score range 0–100, dynamic reputation rules)
* [x] **Admin Verification & Moderation Dashboard**

### 3.3 Phase 2 Priorities (If Time Allows)
* NFT Event Tickets & QR Check-ins
* Split Bills / Split Payments
* Merchant Dashboard & Push Notifications
* Advanced Analytics & Reporting

### 3.4 Explicitly Out of Scope for MVP
* In-app Messaging / Chat, Accommodation Matching, Food Delivery, Ride Sharing, Academic Timetable & Course Registration.

---

## 4. System Architecture & Topology

CampusOS is structured as a **Modular Monolith** for the Hackathon MVP, architected to cleanly split into independent microservices (Auth, Identity, Marketplace, Payment, Trust, Event, Notification) as it scales across universities.

```
+-------------------------------------------------------------+
|              Next.js 15 Frontend (Vercel)                   |
|   TailwindCSS | shadcn/ui | React Query | Zod | Framer     |
+-------------------------------------------------------------+
                              |
                     HTTPS REST API (JSON)
                              |
+-------------------------------------------------------------+
|              FastAPI Backend (Railway)                      |
|  +-------------------------------------------------------+  |
|  | Auth | Verification | Wallet | Marketplace | Payments |  |
|  |      Trust Engine   |  Events Module    |  Admin      |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
       |             |                   |              |
 PostgreSQL     Quai Network         Blip Pay     Cloudinary
(Supabase/Neon) (Smart Contracts)   (Payments)     (Storage)
```

---

## 5. Module Responsibilities & Technical Stack

### 5.1 Technology Stack
* **Frontend:** Next.js 15, React, TypeScript, TailwindCSS, shadcn/ui, Framer Motion, React Query, React Hook Form, Zod, Axios, QRCode Library (Deployed on **Vercel**).
* **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT Authentication (Deployed on **Railway**).
* **Database & Caching:** PostgreSQL (Supabase or Neon), Redis (planned for future caching/queues).
* **Blockchain:** Quai Network, Wallet SDK, Solidity/Quai Smart Contracts.
* **External APIs:** Blip Pay API (Payments), Cloudinary (Image/Document storage), Email Service.

### 5.2 Backend Core Modules
1. **Authentication Module:** User registration, login, JWT token issuance, RBAC, password resets.
2. **Verification Module:** Student document handling (ID, admission letter), admin approval workflow, cryptographic credential hashing, and blockchain verification.
3. **Wallet Module:** Quai wallet connection, balance lookup, transaction history, and QR-based P2P payments.
4. **Marketplace Module:** Listing CRUD, categorization, search, checkout flow, review aggregation, and escrow coordination.
5. **Trust Module:** Trust score calculation, review recording, fraud reporting, and reputation engine maintenance.
6. **Events Module:** Event creation, registration, NFT ticket minting, QR code generation, and check-in attendance.
7. **Admin Module:** User moderation, verification approvals/rejections, suspension handling, and system analytics.

---

## 6. Database Schema (PostgreSQL)

| Table | Primary Columns & Types | Description |
| :--- | :--- | :--- |
| **`Users`** | `id`, `name`, `email`, `wallet_address`, `student_id`, `school`, `faculty`, `department`, `level`, `trust_score` (default 50), `verification_status`, `created_at` | Core user profile & trust state. |
| **`Verification`** | `id`, `user_id`, `student_id_document`, `admission_letter`, `status`, `approved_by`, `credential_hash`, `approved_at` | Student identity verification records. |
| **`Marketplace`** | `id`, `seller_id`, `title`, `description`, `category`, `price`, `images`, `status`, `created_at` | Marketplace product & service listings. |
| **`Orders`** | `id`, `buyer_id`, `listing_id`, `seller_id`, `amount`, `payment_hash`, `status`, `created_at` | Marketplace orders and escrow state. |
| **`Transactions`** | `id`, `wallet`, `receiver`, `amount`, `tx_hash`, `status`, `network`, `timestamp` | Ledger of P2P and marketplace transactions. |
| **`Reviews`** | `id`, `reviewer`, `reviewee`, `rating`, `comment`, `created_at` | Peer ratings and feedback. |
| **`Events`** | `id`, `title`, `description`, `date`, `location`, `price`, `organizer`, `nft_enabled` | Campus events & ticketing configuration. |
| **`Tickets`** | `id`, `event_id`, `owner`, `nft_hash`, `qr_code`, `checked_in` | Event attendance and NFT ticket records. |

---

## 7. Smart Contract Architecture (Quai Network)

The platform utilizes **5 dedicated smart contracts** on Quai Network:

```
1. StudentIdentity
   ├── registerStudent()
   ├── verifyStudent()
   ├── revokeStudent()
   ├── isVerified()
   └── getCredentialHash()

2. MarketplaceEscrow
   ├── createEscrow()
   ├── deposit()
   ├── release()
   ├── refund()
   └── cancel()

3. TrustRegistry
   ├── updateScore()
   ├── recordReview()
   ├── recordFraud()
   └── getTrustScore()

4. CampusEventNFT
   ├── mintTicket()
   ├── transferTicket()
   ├── verifyTicket()
   └── burnTicket()

5. ReceiptRegistry
   ├── storeReceipt()
   └── verifyReceipt()
```

---

## 8. REST API Specification (FastAPI)

### Authentication & Verification
* `POST /auth/register` | `POST /auth/login` | `POST /auth/logout` | `GET /auth/profile`
* `POST /verification/upload` | `GET /verification/status` | `POST /verification/approve` | `POST /verification/reject`

### Wallet & Marketplace
* `GET /wallet` | `GET /wallet/balance` | `GET /wallet/history` | `POST /wallet/send` | `POST /wallet/connect`
* `GET /marketplace` | `POST /marketplace` | `GET /marketplace/{id}` | `PUT /marketplace/{id}` | `DELETE /marketplace/{id}`

### Payments, Trust & Events
* `POST /payments/initiate` | `POST /payments/webhook` | `GET /payments/history`
* `GET /trust` | `POST /trust/review` | `GET /trust/history`
* `POST /events` | `GET /events` | `POST /events/register` | `POST /events/checkin`

### Administration
* `GET /admin/users` | `GET /admin/reports` | `POST /admin/suspend` | `POST /admin/approve`

---

## 9. Trust Score Engine Rules

* **Score Range:** `0` to `100`
* **Initial Starting Score:** `50`
* **Positive Score Additions:**
  * `+10` — Verified Student Identity
  * `+5` — Successful Marketplace Purchase
  * `+5` — Successful Marketplace Sale
  * `+3` — Event Attendance
  * `+2` — Positive Review Received
* **Negative Score Deductions:**
  * `-10` — Confirmed Fraud Report
  * `-5` — Transaction Refund / Dispute
  * `-3` — Failed Payment Attempt

---

## 10. End-to-End System Interaction Flows

### 10.1 Student Verification Flow
1. **Student** uploads Student ID & Admission Letter via Frontend (`POST /verification/upload`).
2. **Admin** reviews and approves documents via Dashboard (`POST /verification/approve`).
3. **Backend** generates a cryptographic `credential_hash` of the verification record.
4. **Smart Contract** (`StudentIdentity`) records the hash on-chain via `verifyStudent()`.
5. **Trust Engine** adds `+10` to the student's Trust Score; **Verified Badge** activates.

### 10.2 Marketplace Purchase & Escrow Flow
1. **Buyer** initiates checkout on a marketplace listing.
2. **Blip Pay API** processes the payment; funds are locked in the **`MarketplaceEscrow`** contract.
3. **Seller** fulfills the order; buyer/seller confirm completion.
4. **Escrow** releases funds (`release()`); **`ReceiptRegistry`** stores the receipt hash on Quai Network.
5. **Trust Engine** awards `+5` to both Buyer and Seller; review prompt is sent.

### 10.3 NFT Event Registration Flow
1. **Student** registers for an event (`POST /events/register`) and completes payment.
2. **`CampusEventNFT`** contract executes `mintTicket()`, generating an on-chain ticket hash.
3. **Backend** generates an encrypted QR Code linked to the ticket NFT.
4. **Check-in:** Organizer scans QR Code (`POST /events/checkin`); attendance is recorded, adding `+3` to Trust Score.

---

## 11. Security, Roles & Governance

### Security Architecture
* **Auth & Secrets:** JWT Authentication, Role-Based Access Control (RBAC), Password Hashing, Environment Secrets Manager.
* **Transaction & API Security:** Wallet Signature Verification, Blip Pay Webhook Signature Validation, HTTPS, Rate Limiting.
* **Data Protection:** Cloudinary Signed Uploads, Prepared SQL Queries (SQLAlchemy ORM), Personal Data Kept Off-Chain.

### Role-Based Access Control (RBAC)
* **Student:** Access to Marketplace, Payments, Events, and Wallet.
* **Merchant:** All Student privileges plus Business Dashboard and Sales Analytics.
* **Admin:** User verification approvals, account suspensions, fraud reports, analytics, and platform configuration.

---

## 12. Go-To-Market & Roadmap

* **Phase 1 (MVP Launch):** **University of Jos** — targeting campus ambassadors, student organizations, department executives, and local campus vendors.
* **Phase 2 (Growth):** Expansion across 5 major Nigerian universities; adding scholarships, savings groups, and merchant dashboards.
* **Phase 3 (Scale):** National rollout across Nigeria; university portal integrations, campus banking, and AI fraud detection.
* **Phase 4 (Pan-African):** Pan-African student identity network and cross-university marketplace.
