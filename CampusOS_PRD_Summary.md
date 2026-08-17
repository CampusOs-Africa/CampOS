# CampusOS — Product Requirements Document (PRD) Summary

> **Source of Truth:** `CampusOS.pdf`  
> **Tagline:** The Trusted Operating System for University Campuses  
> **Context:** Quai × Blip Buildathon  

---

## 1. Executive Summary & Vision

**CampusOS** is a unified digital operating system designed to serve as the **trusted identity and commerce layer for university campuses**, starting with African universities. 

Existing payment apps focus purely on transactions. In contrast, **CampusOS focuses on trust**: every payment, marketplace purchase, event registration, and peer interaction contributes to a student's **portable Trust Score**. Powered by **Quai Network** (blockchain verification) and **Blip Pay API** (secure payments), CampusOS creates a safer, scam-free campus economy.

* **Vision:** Build the trust infrastructure for African universities, becoming the digital identity and commerce layer for every university campus.
* **Platforms:** Web for Hackathon MVP; Mobile planned for future phases.

---

## 2. Problem Statement

University students currently rely on a fragmented web of disconnected platforms (**WhatsApp, Telegram, Opay, PalmPay, Google Forms, Cash, Excel, School Portals**). This disconnection causes critical market failures:
* **High Fraud & Scams:** Fake payment screenshots and marketplace scams.
* **Lack of Accountability:** Anonymous buyers and sellers with no verifiable reputation.
* **Inaccessible Reputation:** No portable reputation system or verified digital student identity.
* **Friction-Heavy Commerce:** Manual event registration, difficult bill splitting, and poor user verification.

---

## 3. Product Goals

### Primary Goals
1. **Create Trusted Campus Commerce:** Establish a scam-resistant peer-to-peer (P2P) marketplace.
2. **Enable Secure Payments:** Integrate **Blip Pay API** for seamless campus payments.
3. **Blockchain Verification:** Demonstrate **Quai Network** capabilities by recording critical transactions on-chain.
4. **Reduce Student Scams:** Replace anonymous interactions with verified student identities and reputation scoring.
5. **Simplify Transactions:** Provide a unified wallet and payment interface for campus life.

### Secondary Goals
* Campus event management & ticketing
* Student freelancing & accommodation marketplace
* Digital student identity & badges
* Campus business directory & student reward systems

---

## 4. Target User Personas

| Persona Class | Target Users | Key Needs & Roles |
| :--- | :--- | :--- |
| **Primary** | **University Students (18–30)** | Peer-to-peer commerce, secure payments, event discovery, building portable trust/reputation on campus. |
| **Secondary** | **Campus Merchants** | Restaurants, photocopy centers, barbers, laundromats, fashion vendors, bookstores needing reliable payment receipt and merchant discovery. |
| **Tertiary** | **Organizations & Institutions** | Universities, student unions, department associations, clubs, and event organizers requiring ticketing, verified access, and event management. |

---

## 5. Scope Breakdown: MVP vs. Roadmap

### 5.1 Hackathon MVP Scope (Must-Have)
1. **Authentication & RBAC:** Secure JWT authentication, role-based access control, and encrypted secrets.
2. **Verified Student Identity:** Verification system granting a **Verified Student Identity Badge**.
3. **Wallet Connection:** Connecting to Quai Network wallets with signature verification.
4. **Blip Payment Integration:** Peer-to-peer payments and checkout via Blip Pay API.
5. **Quai Transaction Recording:** Immutable on-chain recording of transaction & reputation proofs.
6. **Campus Marketplace:** Core buying and selling functionality between verified peers.
7. **Trust Score System:** Reputation engine that updates dynamically based on positive transactions and interactions.
8. **Reviews:** Post-transaction feedback mechanisms.
9. **Admin Verification Dashboard:** Administrative governance for student/merchant verification and monitoring.

### 5.2 Nice-to-Have (MVP Bonus Scope)
* **NFT Event Tickets** (on Quai Network)
* **Split Bills / Split Payments**
* **Merchant Dashboard**
* **Notifications & Activity Alerts**
* **Analytics & Reporting**

### 5.3 Out of Scope for MVP
* Messaging / In-app Chat
* Accommodation Matching
* Food Delivery & Ride Sharing
* Academic Timetable & Course Registration

---

## 6. Technical Stack & Security Requirements

### Technical Stack
* **Frontend:** Next.js, React, TypeScript, TailwindCSS, shadcn/ui (Deployed on Vercel)
* **Backend:** FastAPI (Python), PostgreSQL, SQLAlchemy (Deployed on Railway)
* **Blockchain & Payments:** Quai Network, Blip Pay API
* **Media Storage:** Cloudinary

### Security & Compliance Checklist
* [x] **JWT Authentication** & **Role-Based Access Control (RBAC)**
* [x] **Wallet Signature Verification**
* [x] **Encrypted Secrets** & **CSRF Protection**
* [x] **Rate Limiting** & **Duplicate Payment Detection**
* [x] **Strict Input & File Validation**
* [x] **Comprehensive Audit Logs**

---

## 7. Success Metrics & KPIs

### Hackathon MVP Success Criteria
* Student registration and verified identity badge issuance
* Successful wallet connection and signature verification
* End-to-end successful payment via Blip Pay
* Successful marketplace purchase flow
* Verified Trust Score update and event registration

### Business & Growth KPIs
* User registrations & Daily Active Users (DAU)
* Marketplace transaction volume & payment volume
* Event registrations & Trust Score activity rate
* Merchant onboarding rate

---

## 8. Business Model & Go-To-Market (GTM) Strategy

### Revenue & Monetization Streams
* **Free Student Accounts** (Base tier to maximize adoption)
* **Premium Sellers & Merchant Subscriptions**
* **University Partnerships & Event Service Fees**
* **Transaction Fees & Campus Advertising**

### Phased GTM Rollout Strategy
* **Phase 1 (Launch):** **University of Jos** — Driving initial adoption via campus ambassadors, student organizations, department executives, and local campus vendors.
* **Phase 2:** Expansion across **5 major Nigerian universities**.
* **Phase 3:** National rollout across Nigeria.
* **Phase 4:** Pan-African university expansion.

---

## 9. Future Product Roadmap

```
Phase 1: MVP (Current Build)
  ├── Verified Student Identity & Campus Wallet
  ├── P2P Marketplace & Trust Score (Quai × Blip)
  └── Admin Verification & Core Event Tools

Phase 2: Commerce & Financial Expansion
  ├── Campus Merchants Onboarding
  ├── Scholarships, Student Loans & Savings Groups
  └── Digital Certificates

Phase 3: Institutional & Advanced FinTech
  ├── University System Integrations & Campus Banking
  ├── AI Fraud Detection & Campus Credit Score
  └── Cross-Campus Reputation Portability

Phase 4: Pan-African Network
  ├── Pan-African Student Identity Network
  ├── Cross-University Marketplace
  └── Employment Verification & Alumni Credentials
```
