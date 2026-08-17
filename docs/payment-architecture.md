# CampusOS Payment Architecture

Status labels: **LIVE**, **MOCK**, **UNVERIFIED**, **BLOCKED**.

## Overview

```
Buyer → CampusOS /payments/intent → (server derives order/amount)
      → Blip Pay provider (checkout)
      → Blip Pay HMAC webhook → CampusOS verifies → PaymentIntent paid
      → order/escrow locks (existing OrderService) → later release on delivery
```

The client never supplies buyer identity, amount, seller, payment status,
provider reference, or transaction hash. All of these are derived server-side.

## Components

- `PaymentIntent` (`payment_intents`): immutable financial facts in integer
  minor units (kobo for NGN), with status, provider reference, and optional
  Quai settlement hash.
- `WebhookEvent` (`webhook_events`): append-only record of incoming provider
  events with unique `(provider, event_id)` for replay safety.
- `PaymentIntentService`: orchestrates creation, idempotency, state machine,
  and webhook application.
- `PaymentProvider` / `BlipPayProvider`: provider abstraction. All Blip HTTP
  logic is isolated here.
- Existing `OrderService.handle_webhook` continues to lock escrow after a
  verified paid event.

## Payment state machine

```
pending ──► processing ──► paid ──► refunded
   │              │
   │              ├─► failed
   ├─► cancelled
   └─► expired
```

Illegal transitions are rejected. `paid` is only reached via a
cryptographically verified provider webhook that matches amount/currency/order.

## Idempotency

`POST /payments/intent` accepts an optional `idempotency_key`.
- Same buyer + key → same `PaymentIntent` (reused if facts match).
- Same key, different buyer → **409**.
- Same buyer + key but conflicting amount/seller → **409**.
- Unique DB constraint `(idempotency_key, buyer_id)` plus a global check
  prevents concurrent/duplicate intents (not just in-memory state).

## Webhook security

- HMAC-SHA256 signature verified with `BLIP_PAY_WEBHOOK_SECRET` using
  constant-time comparison.
- Optional timestamp drift check.
- `WebhookEvent` unique on `(provider, event_id)` makes replay idempotent at
  the database level.
- Before applying, the service verifies payment reference, order ownership,
  exact amount (minor units), currency, and provider.
- Browser callbacks (`/callback/success`) are UX signals only and never mark
  an order paid.

## Amounts

Money uses integer minor units (`amount_minor`). `to_minor()` converts the
listing's NGN price to kobo server-side. Float is never used for money math.

## Blip Pay status

**BLOCKED / UNVERIFIED (live).** The exact Blip Pay HTTP contract — base URL,
auth scheme, create-payment request/response, webhook schema, status values,
refund support, supported assets/chains, and wallet-connect capability — could
not be verified from this repository. `BlipPayProvider.create_payment`
therefore raises `501` in live mode. In mock mode it returns a deterministic
frontend checkout URL for development.

Before going live the following must be supplied and verified:
`BLIP_API_URL`, `BLIP_API_KEY`/merchant credentials, `BLIP_PAY_WEBHOOK_SECRET`,
documented create-payment and webhook schemas.

## Quai integration status

**MOCK (development); BLOCKED for production.** The existing blockchain
adapter generates `0xquai_*` placeholder hashes in mock mode. No real Quai
RPC, signing, or confirmation logic is wired in this phase. Production
refuses to start with `USE_MOCK_BLOCKCHAIN=true` unless
`ALLOW_MOCK_BLOCKCHAIN_IN_PRODUCTION=true` is explicitly set. Private keys are
server-side only and never sent to the client or logged.

## NGN / fiat

No fabricated FX rate. Blip is expected to handle NGN funding. If Quai
settlement requires a crypto amount, a provider-issued quote must be used
server-side (future work); the frontend must not calculate crypto amounts.

## API

- `POST /api/v1/payments/intent` → `PaymentIntentResponse`
- `GET  /api/v1/payments/intent/{id}` → `PaymentStatusResponse`
- `POST /api/v1/payments/provider/webhook` → provider webhook (HMAC)
- Legacy `POST /api/v1/payments/initiate` and `/webhook` remain for
  backwards compatibility but new code should use `/intent`.

## Required environment variables

```
BLIP_API_URL=
BLIP_API_KEY=
BLIP_PAY_API_KEY=
BLIP_PAY_WEBHOOK_SECRET=
USE_MOCK_BLIP_PAY=true
USE_MOCK_BLOCKCHAIN=true
ALLOW_MOCK_BLOCKCHAIN_IN_PRODUCTION=false
QUAI_RPC_URL=
QUAI_NETWORK=
QUAI_CHAIN_ID=
QUAI_PRIVATE_KEY=
```

Production requires `BLIP_PAY_WEBHOOK_SECRET`, a real `JWT_SECRET`, and mock
modes disabled (or explicitly overridden).

## Failure scenarios

- Provider unavailable at intent creation → intent remains `pending` with
  `failure_reason`; client can retry/poll.
- Bad signature / stale event / unknown reference / amount mismatch → 4xx and
  the event is recorded as failed; no order state change.
- Duplicate event → idempotent, returns existing order.
- Payment received but escrow lock fails → webhook is quarantined; alerting
  should be added in operations.

## Phase 7 verification status (authoritative)

- **Blip Pay live integration: BLOCKED — NOT VERIFIED.** No official payment
  API contract (base URL, auth, create-payment schema, webhook schema/signature,
  status values, refund, NGN/crypto/Quai settlement, wallet connect) is
  available in the repository or from the vendor marketing site. The live
  provider path returns 501; mock mode is used only in development.
- **Real Quai settlement: BLOCKED.** A verified RPC endpoint, target chain ID,
  deployed contract address + ABI, and secure server-side signing configuration
  are required. The existing adapter emits clearly-labelled mock hashes.
- Production refuses to start with `USE_MOCK_BLIP_PAY=true` and requires
  `BLIP_API_URL` + `BLIP_PAY_API_KEY` when mock is disabled (though the live
  call itself remains 501 until the contract is verified).
- The frontend polls `GET /payments/intent/{id}` and never treats a browser
  callback as proof of payment.

## Phase 9 — Orchard RPC verification

Orchard Cyprus-1 RPC was independently verified live:
- chainId `0x3a98` (15000), block production confirmed, and `eth_getBalance`,
  `eth_getCode`, and `eth_getTransactionReceipt` all respond correctly.
- The backend Quai verifier is therefore ready to confirm real transactions.
- Contracts are NOT deployed because no funded Cyprus-1 deployer key is present
  in this environment. See `docs/quai-deployment.md` for the exact step. No
  addresses or hashes are fabricated.
