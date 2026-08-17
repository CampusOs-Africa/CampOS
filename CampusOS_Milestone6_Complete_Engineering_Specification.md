# CampusOS Milestone 6 — Complete Engineering & Architectural Specification
## Bounded Trust Score Engine, Immutable Audit Trail, Review Moderation, Fraud Reporting & Leaderboard

> **Project:** CampusOS — *"The trusted digital operating system for African universities."*  
> **Milestone Specified:** Milestone 6 — Campus Trust Score Engine (`TrustScoreService`, `TrustRepository`, `FraudService`, `ReviewService`)  
> **Date:** July 30, 2026  
> **Status:** **COMPLETE & VERIFIED** (81/81 automated tests passing across Solidity, Python & Next.js; 0 linter errors)  

---

## Table of Contents
1. [Executive Summary & Bounded Score Engine Architecture](#1-executive-summary--bounded-score-engine-architecture)
2. [Deterministic Reputation Rules (0–100 Scale)](#2-deterministic-reputation-rules-0100-scale)
3. [Immutable Audit Trail (`TrustHistory` & `FraudReport`)](#3-immutable-audit-trail-trusthistory--fraudreport)
4. [Peer Reviews & Review Moderation Engine](#4-peer-reviews--review-moderation-engine)
5. [Fraud Reporting & Dispute Penalty Governance](#5-fraud-reporting--dispute-penalty-governance)
6. [Trust Score Dashboard, Leaderboard & Campus Analytics](#6-trust-score-dashboard-leaderboard--campus-analytics)
7. [Database Schema & ERD (Alembic `0006`)](#7-database-schema--erd-alembic-0006)
8. [REST API Specification (OpenAPI 3.1.0)](#8-rest-api-specification-openapi-310)

---

## 1. Executive Summary & Bounded Score Engine Architecture

Milestone 6 implements the **Campus Trust Score Engine**, establishing an immutable, verifiable reputation layer across all CampusOS commerce, verification, and peer interactions.

```
                  ┌────────────────────────────────────────────────────────────┐
                  │                 CAMPUS TRUST SCORE ENGINE                  │
                  │   • Bounded 0–100 Scale        • Tier Badges (Platinum ->) │
                  │   • Baseline Starting Score 50 • Immutable TrustHistory    │
                  └─────────────────────────────┬──────────────────────────────┘
                                                │
          ┌─────────────────────────────────────┼─────────────────────────────────────┐
          │                                     │                                     │
          ▼                                     ▼                                     ▼
┌──────────────────┐                ┌──────────────────────┐              ┌──────────────────────┐
│ POSITIVE REWARDS │                │   REVIEW MODERATION  │              │  PENALTY DEDUCTIONS  │
│ • Verification+10│                │ • Peer Review (+1)   │              │ • Order Refund (-5)  │
│ • Order Release+5│                │ • Market Review (+2) │              │ • Dispute Lost (-10) │
│ • Wallet P2P   +5│                │ • Reversal on Remove │              │ • Fraud Confirmed-20 │
└──────────────────┘                └──────────────────────┘              └──────────────────────┘
```

The engine is encapsulated within `TrustScoreService` (`app/services/trust_score_service.py`), enforcing that **every score change creates an immutable audit record in PostgreSQL (`trust_history`)** and emits structured JSON audit logs (`AUDIT_EVENT: TRUST_SCORE_UPDATED`).

---

## 2. Deterministic Reputation Rules (0–100 Scale)

All student accounts start at a baseline score of **50** and are bounded strictly within `[0, 100]` (`_clamp_score(old + delta)`):

| Event Type | Event Code (`event_type`) | Score Delta (`delta`) | Operational Trigger |
| :--- | :--- | :---: | :--- |
| **Verified Student Identity** | `verification` | **+10** | Admin approves documents (`POST /api/v1/verification/admin/{id}/approve`) |
| **Marketplace Order Release** | `order_release` | **+5** | Buyer confirms delivery and releases Quai escrow (`POST /api/v1/orders/{id}/release-escrow`) — awarded to both Buyer and Seller |
| **Quai Campus Wallet Activity** | `wallet_p2p` | **+5** | Connecting Quai EVM wallet address (`POST /api/v1/wallet/connect`) |
| **Marketplace Review (≥ 4★)** | `marketplace_review` | **+2** | Receiving a 4 or 5 star review on a completed marketplace order |
| **Peer Reputation Review (≥ 4★)** | `peer_review` | **+1** | Receiving a 4 or 5 star peer review from a campus classmate |
| **Review Removed by Admin** | `review_moderation` | **-1** / **-2** | Reversal of trust bonus when an approved positive review is removed by a moderator |
| **Order Refund** | `order_refund` | **-5** | Seller refunds an escrow order (`POST /api/v1/payments/refund`) |
| **Escrow Dispute Lost** | `dispute_lost` | **-10** | Admin resolves an escrow dispute against a user (`POST /api/v1/escrow/resolve`) |
| **Confirmed Fraud Report** | `fraud_penalty` | **-20** | Admin resolves a fraud report as confirmed (`POST /api/v1/fraud/reports/{id}/resolve`) |

### Trust Tier Badges (`get_trust_badge`)
* **Platinum (85–100):** Top-tier verified campus sellers and leaders.
* **Gold (70–84):** Highly trusted students with verified commerce history.
* **Silver (55–69):** Verified students in good standing (default verified starting tier is 60).
* **Bronze (40–54):** Baseline unverified students or minor penalty recovery.
* **At-Risk (0–39):** Restricted reputation requiring administrative review.

---

## 3. Immutable Audit Trail (`TrustHistory` & `FraudReport`)

### 3.1 `TrustHistory` Entity (`app/models/trust.py`)
Every score mutation creates an immutable row in `trust_history`:
* `id` (UUIDv4 Primary Key)
* `user_id` (Foreign Key to `users.id`, indexed)
* `delta` (Integer change: `+10`, `+5`, `-20`, etc.)
* `old_score` and `new_score` (Snapshot of bounded score transition)
* `event_type` (Indexed category string)
* `reason` (Descriptive audit string)
* `reference_id` (Optional FK/UUID to order, review, fraud report, or verification)
* `created_at` (UTC timestamp with index `idx_trust_history_user_created`)

---

## 4. Peer Reviews & Review Moderation Engine

### 4.1 Peer vs. Marketplace Reviews (`app/models/review.py`)
* **`review_type='marketplace'`**: Bound to an `order_id`; requires order completion.
* **`review_type='peer'`**: Peer-to-peer reputation review between students (`order_id = NULL`). Prevents self-reviews (`reviewer_id == reviewee_id`).

### 4.2 Review Moderation Workflow (`POST /api/v1/reviews/{id}/moderate`)
Administrators can approve, flag, or remove reviews. When a previously approved positive review ($\ge 4\text{ stars}$) is removed, `ReviewService.moderate_review` automatically invokes `TrustScoreService.penalize_review_removed` to deduct the unearned bonus points.

---

## 5. Fraud Reporting & Dispute Penalty Governance

### 5.1 Formal Fraud Reporting (`POST /api/v1/fraud/reports`)
Students can submit fraud reports (`FraudReportCreateRequest`) categorized as:
* `scam_listing`: Fake or non-existent accommodation/items.
* `fake_item`: Counterfeit or defective goods.
* `non_delivery`: Failure to deliver after meetup.
* `identity_fraud`: Credential or student ID impersonation.

### 5.2 Admin Fraud Resolution (`POST /api/v1/fraud/reports/{id}/resolve`)
When an administrator resolves a report as `resolved_confirmed`, `FraudService.resolve_report` applies a `-20` Trust Score penalty via `TrustScoreService.penalize_fraud_report`, creating an immutable `TrustHistory` audit record.

---

## 6. Trust Score Dashboard, Leaderboard & Campus Analytics

### 6.1 User Trust Dashboard (`GET /api/v1/trust/dashboard/{user_id}`)
Returns `TrustDashboardResponse` containing bounded score, badge, full `TrustHistoryResponse` audit trail, and aggregate metrics (`total_positive_earned`, `total_penalties_deducted`, `completed_sales`, `peer_reviews_count`, `average_rating`).

### 6.2 Campus Leaderboard (`GET /api/v1/trust/leaderboard`)
Returns top students sorted by `trust_score DESC, name ASC`, filterable by `school` and `department`. Assigns sequential 1-based rankings (`rank`).

### 6.3 Campus Analytics (`GET /api/v1/trust/analytics`)
Returns campus-wide metrics: `campus_average_score`, `total_verified_students`, `recent_trust_events_24h`, and tier distribution counts (`Platinum` through `At-Risk`).

---

## 7. Database Schema & ERD (Alembic `0006`)

```
+---------------------+         +-----------------------+         +-----------------------+
|       users         |         |     trust_history     |         |     fraud_reports     |
+---------------------+         +-----------------------+         +-----------------------+
| id (PK)             |1       *| id (PK)               |       *1| id (PK)               |
| name                |---------| user_id (FK)          |    ┌────| reporter_id (FK)      |
| email               |         | delta                 |    │    | reported_user_id (FK) |
| trust_score (0-100) |         | old_score / new_score |    │    | category              |
| verification_status |         | event_type            |    │    | status                |
+---------------------+         | reference_id          |    │    | penalty_applied       |
          │1                    | created_at            |    │    | created_at            |
          │                     +-----------------------+    │    +-----------------------+
          │*                                                 │
+---------------------+                                      │
|       reviews       |                                      │
+---------------------+                                      │
| id (PK)             |                                      │
| reviewer_id (FK)    |──────────────────────────────────────┘
| reviewee_id (FK)    |
| rating (1-5)        |
| review_type         |
| status              |
+---------------------+
```

---

## 8. REST API Specification (OpenAPI 3.1.0)

| Route Endpoint | Method | Purpose | RBAC Gate | Status Codes |
| :--- | :---: | :--- | :--- | :---: |
| `/api/v1/trust/dashboard/{user_id}` | `GET` | Get bounded Trust Score, badge, and immutable history | Public / Student | `200 OK` / `404` |
| `/api/v1/trust/leaderboard` | `GET` | Filterable campus leaderboard (school, department) | Public / Student | `200 OK` |
| `/api/v1/trust/history/{user_id}` | `GET` | Get paginated immutable TrustHistory audit trail | Public / Student | `200 OK` |
| `/api/v1/trust/analytics` | `GET` | Get campus-wide trust score analytics & distribution | Public / Student | `200 OK` |
| `/api/v1/reviews/` | `POST` | Submit peer review (`review_type='peer'`) or market review | Authenticated Student | `201 Created` / `400` / `409` |
| `/api/v1/reviews/user/{user_id}` | `GET` | Get reviews received by student (filterable by type/status)| Public / Student | `200 OK` |
| `/api/v1/reviews/{id}/moderate` | `POST` | Admin moderate review (`approved`/`flagged`/`removed`) | **Admin Only** | `200 OK` / `403` / `404` |
| `/api/v1/reviews/admin/queue` | `GET` | Admin queue of flagged reviews for moderation | **Admin Only** | `200 OK` |
| `/api/v1/fraud/reports` | `POST` | Submit formal fraud report with Cloudinary proof | Authenticated Student | `201 Created` / `400` |
| `/api/v1/fraud/reports` | `GET` | Filterable list of fraud reports by status/user | Authenticated Student | `200 OK` |
| `/api/v1/fraud/reports/{id}` | `GET` | Get fraud report details and evidence link | Authenticated Student | `200 OK` / `404` |
| `/api/v1/fraud/reports/{id}/resolve`| `POST` | Admin resolve report (`confirmed`/`dismissed`) & penalize| **Admin Only** | `200 OK` / `403` / `404` |

---
*Specification generated and verified for CampusOS Milestone 6 engineering deliverables.*
