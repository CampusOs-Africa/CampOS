# CampusOS — Complete Blip Pay Payment & Quai Escrow Integration Guide
## Complete Architecture Diagrams, Webhook Security & Endpoint Reference

> **Project:** CampusOS  
> **Module:** Blip Pay Checkout & Quai Network Smart Contract Escrow (`MarketplaceEscrow.sol`)  
> **Status:** **COMPLETE** (32/32 Backend tests passing; 23/23 Solidity tests passing; 10/10 Frontend tests passing; 0 linter errors)  

---

## 1. Executive Implementation Summary

The Blip Pay payment engine (`app/services/payment_service.py`) handles secure campus checkout, cryptographic webhook verification, duplicate payment protection, retry logic, and automated binding to Quai Network smart contract escrow (`MarketplaceEscrow.sol`).

### Core Capabilities Implemented
1. **Payment Initialization & Duplicate Protection (`POST /api/v1/payments/initiate`):**
   * Enforces inventory checks (`status == 'active'` and `inventory_count > 0`) with PostgreSQL row-level locking (`with_for_update()`).
   * Protects against self-purchasing (`buyer_id == seller_id` rejected with `400 Bad Request`).
   * **Duplicate Payment Protection:** Detects existing active `initiated` orders for the same buyer and listing, returning the existing payment intent reference and URL instead of creating duplicate orders.
   * Creates an `Order` (`status='initiated'`) and an audited **`BlipPaymentRecord`** (`status='initiated'`).
2. **Webhook HMAC Signature Verification (`POST /api/v1/payments/webhook`):**
   * Inspects `X-Blip-Signature` header and re-computes HMAC-SHA256 hex digest using `settings.BLIP_PAY_WEBHOOK_SECRET`.
   * Uses constant-time `hmac.compare_digest(computed, signature)` to prevent timing side-channel attacks.
   * Rejects unauthenticated webhooks with `401 Unauthorized`.
3. **Idempotency Guarantee:**
   * Checks `if order.status != 'initiated': return order`. If a webhook retry arrives for an order that is already `escrow_locked` or `completed`, the handler returns `200 OK` without duplicating state changes or Quai blockchain transactions.
4. **Payment Success Callback & Escrow Trigger:**
   * On payment success, transitions order to `escrow_locked`, records `BlipPaymentRecord(status='successful')`, decrements inventory, and asynchronously calls `MarketplaceEscrow.createEscrow()` and `deposit()` on Quai Network (`escrow_tx_hash`).
   * `/api/v1/payments/callback/success` handles browser redirects back to the order escrow status page.
5. **Payment Failure Callback & Record Audit:**
   * `/api/v1/payments/callback/failure` transitions initiated orders to `failed`, logs `BlipPaymentRecord(status='failed')`, and redirects back to checkout.
6. **Refund Handling (`POST /api/v1/payments/refund`):**
   * Allows sellers or administrators to refund an order (`escrow_locked` ➔ `refunded`).
   * Calls Quai smart contract escrow refund (`quai_blockchain_service.refundStudent` / `escrow_service.refund_escrow`).
   * Restores inventory (`listing.inventory_count += 1`).
   * Applies trust score penalty (`-5` Trust Score to Seller via `TrustService.penalize_order_refund`).
7. **Retry Strategy & Environment Support:**
   * Uses exponential backoff retry logic (`_execute_blip_pay_request_with_retry`, max 3 attempts) for live HTTP calls to Blip Pay API.
   * Configurable via `USE_MOCK_BLIP_PAY=True` for local development/hackathon demos or `False` for live deployment.

---

## 2. Architecture & Sequence Diagrams (Mermaid)

### 2.1 Complete Blip Pay Checkout, Webhook & Quai Escrow Lock Sequence
```mermaid
sequenceDiagram
    autonumber
    actor Buyer
    participant UI as Checkout Modal
    participant API as FastAPI Router (/payments)
    participant Pay as PaymentService
    participant DB as PostgreSQL
    participant Blip as Blip Pay API / Webhook
    participant Order as OrderService
    participant Quai as QuaiBlockchainService
    participant SC as MarketplaceEscrow.sol

    Buyer->>UI: Click "Pay with Blip Pay"
    UI->>API: POST /api/v1/payments/initiate {buyer_id, listing_id, amount}
    API->>Pay: initiate_checkout()
    Pay->>DB: Check listing inventory & row lock (.with_for_update())
    Pay->>DB: Duplicate check (get_initiated_order)
    Pay->>DB: INSERT INTO orders & blip_payment_records (status='initiated')
    Pay->>Blip: POST /checkout/intents [with Retry Strategy]
    Blip-->>Pay: checkout_url & payment_reference
    Pay-->>UI: 201 Created {order_id, payment_url, payment_reference}
    
    Note over Buyer,Blip: Buyer completes payment on Blip Pay Checkout URL
    Blip->>API: POST /api/v1/payments/webhook [X-Blip-Signature: HMAC-SHA256]
    API->>Pay: verify_webhook_signature(signature_header, raw_body_bytes)
    Pay->>Pay: hmac.compare_digest(computed, signature_header)
    Pay-->>API: true
    API->>Order: handle_webhook(payment_reference, 'success')
    Order->>DB: Idempotency Check (if status != 'initiated' return)
    Order->>DB: UPDATE orders SET status='escrow_locked'
    Order->>DB: INSERT INTO blip_payment_records (status='successful')
    Order->>Quai: await create_escrow(order_id, buyer, seller, amount)
    Note over Quai: Runs asynchronously in worker thread (asyncio.to_thread)
    Quai->>SC: createEscrow() + deposit{value: amount}()
    SC-->>Quai: EscrowFunded Event + Tx Hash (0xquai_escrow_lock_...)
    Order->>DB: UPDATE orders SET escrow_tx_hash=0xquai_escrow_lock_...
    Order->>DB: UPDATE marketplace_listings SET inventory_count-=1
    Order-->>API: 200 OK (OrderResponse with escrow_tx_hash)
```

### 2.2 Payment Refund & Inventory Restoration Sequence
```mermaid
sequenceDiagram
    autonumber
    actor Seller
    participant API as FastAPI Router (/payments)
    participant Pay as PaymentService
    participant DB as PostgreSQL
    participant Quai as QuaiBlockchainService
    participant SC as MarketplaceEscrow.sol
    participant Trust as TrustService

    Seller->>API: POST /api/v1/payments/refund?order_id=...&actor_id=...
    API->>Pay: refund_payment(order_id, actor_id, reason)
    Pay->>DB: Verify seller ownership or admin role
    Pay->>Quai: await refund_escrow(order_id)
    Quai->>SC: refund(orderId) [CEI Pattern + ReentrancyGuard]
    SC-->>Quai: EscrowRefunded Event + Tx Hash (0xquai_escrow_refund_...)
    Pay->>DB: UPDATE orders SET status='refunded', escrow_tx_hash=0x...
    Pay->>DB: UPDATE marketplace_listings SET inventory_count+=1
    Pay->>DB: INSERT INTO blip_payment_records (status='refunded')
    Pay->>Trust: penalize_order_refund(seller_id) [-5 Trust Score]
    Pay-->>API: 200 OK {success: true, status: 'refunded', escrow_tx_hash}
```

---

## 3. Complete Payment API Reference & OpenAPI Documentation

All 7 payment endpoints use standardized JSON envelopes (`{"success": true, "data": ..., "error": null, "meta": ...}`) mounted under `/api/v1/payments` and documented in `/openapi.json`:

| Route Endpoint | Method | Purpose | Authentication & RBAC | Expected Status Codes |
| :--- | :---: | :--- | :--- | :---: |
| `/api/v1/payments/initiate` | `POST` | Initiate Blip Pay checkout intent, lock inventory, create pending order with duplicate protection. | Authenticated Student | `201 Created` / `400` / `404` |
| `/api/v1/payments/webhook` | `POST` | Blip Pay payment confirmation webhook validated by constant-time HMAC-SHA256 signature checking. | **HMAC-SHA256 Signature Check** | `200 OK` / `401 Unauthorized` |
| `/api/v1/payments/refund` | `POST` | Process full refund to buyer, transition order to 'refunded', restore inventory, and apply -5 Trust Score penalty. | Seller or Admin | `200 OK` / `400` / `403` |
| `/api/v1/payments/callback/success` | `GET` | Browser callback redirect after successful Blip Pay checkout. Returns order confirmation link. | Public / Client Browser | `200 OK` / `404` |
| `/api/v1/payments/callback/failure` | `GET` | Browser callback redirect after failed/cancelled checkout. Transitions order to 'failed'. | Public / Client Browser | `200 OK` / `404` |
| `/api/v1/payments/records/order/{id}` | `GET` | Get chronological audit trail of all Blip Payment Records associated with an order ID. | Authenticated Student / Admin | `200 OK` |
| `/api/v1/payments/records/reference/{ref}` | `GET` | Retrieve specific Blip Payment Record by its unique payment reference. | Authenticated Student / Admin | `200 OK` / `404` |

---

## 4. Environment Variables Configuration (`.env` / `app/core/config.py`)

```env
# Blip Pay API & Webhook Configuration
BLIP_PAY_API_KEY=mock-blip-pay-api-key
BLIP_PAY_WEBHOOK_SECRET=campusos-blip-pay-webhook-hmac-secret-2026
BLIP_PAY_API_URL=https://api.blippay.com/v1
USE_MOCK_BLIP_PAY=True  # Set to False in staging/production deployment

# Quai Network JSON-RPC & Smart Contract Configuration
QUAI_RPC_URL=https://rpc.quai.network
QUAI_CONTRACT_ADDRESS=0xYourStudentIdentityAddressHere
QUAI_PRIVATE_KEY=0xYourAdminPrivateKeyHere
QUAI_CHAIN_ID=9000
QUAI_RPC_TIMEOUT=30
QUAI_TX_TIMEOUT=120
USE_MOCK_BLOCKCHAIN=True  # Set to False in live Quai testnet deployment
```

---

## 5. Test Suite Verification (100% Pass Rate)

### Backend Pytest Suite (`pytest -v` in `/home/user/backend`) — **32/32 PASSED**
* **`tests/test_payment_service.py`**:
  * `test_blip_pay_checkout_duplicate_protection_and_hmac_verification`: Verifies checkout initiation, duplicate payment protection (submitting second checkout for same buyer & listing reuses existing order), HMAC-SHA256 signature checking (`hmac.compare_digest`), webhook escrow locking, webhook idempotency, payment audit record retrieval, browser success callback redirect helper, and payment refund (by seller/admin) with inventory restoration (`0 -> 1`).
  * `test_blip_pay_failure_callback`: Verifies failure callback transitions initiated order to `failed` and records `BlipPaymentRecord(status='failed')`.
* **All existing marketplace, escrow, order, security, QR, blockchain, and wallet tests (`30 tests`)**: All passing cleanly.
