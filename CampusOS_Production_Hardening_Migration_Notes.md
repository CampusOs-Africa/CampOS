# CampusOS Production Hardening — Migration Notes & Upgrade Guide
**Version:** 1.1.0-prod  
**Date:** July 30, 2026  
**Target Environment:** Staging & Enterprise Production (Quai Network × Blip Pay)  
**Release Classification:** Non-breaking Production Hardening & Operational Resilience  

---

## 1. Summary of Changes
This release implements all outstanding production engineering recommendations identified in the Milestone 5 security and production readiness audits:
1. **Redis-Backed Distributed Rate Limiting (`RateLimitMiddleware`)** with atomic Lua script sliding windows and automatic in-memory fallback.
2. **Institutional Email OTP Verification (`VerificationService`)** (`POST /api/v1/verification/send-email-otp` and `POST /api/v1/verification/verify-email-otp`) with Resend integration, 10-minute expiration, 60-second cooldown, and 3-attempt lockout.
3. **Multi-Key Secret Rotation & Production Validation (`app.core.config.Settings`)** supporting zero-downtime rotation of JWT and Blip Pay webhook HMAC secrets via comma-separated rotation lists.
4. **Dynamic CORS Lockdown (`settings.get_cors_origins()`)** enforcing strict domain allowlists in production (`https://campusos.vercel.app`, `https://campusos.ng`) while retaining localhost fallbacks in development/test.
5. **Webhook Replay Protection & Timestamp Drift (`PaymentService`)** enforcing $\pm 300\text{-second}$ window validation (`X-Blip-Timestamp`) and a 24-hour Redis/in-memory replay cache (`check_and_cache_webhook_replay`).
6. **Structured JSON Logging & Correlation Tracing (`app.core.logger` & `CorrelationIdMiddleware`)** formatting all logs as structured JSON with `request_id`, `correlation_id`, and explicit audit events.

---

## 2. New Python Dependencies
Add the following packages to your staging and production environments (already updated in `backend/requirements.txt`):
```bash
pip install redis>=5.0.0 python-json-logger>=2.0.0
```

---

## 3. Environment Variables (.env Configuration)
The following new environment variables are supported in `app/core/config.py`:

```ini
# --- Redis Configuration (Supports Railway & Vercel) ---
REDIS_URL="redis://default:securepassword@redis.railway.internal:6379/0" # Or RAILWAY_REDIS_URL
USE_REDIS_RATE_LIMIT="True"
RATE_LIMIT_DEFAULT_PER_MINUTE="100"
RATE_LIMIT_SENSITIVE_PER_MINUTE="30"

# --- Secret Management & Rotation ---
# Primary secret key used for signing new tokens/webhooks
JWT_SECRET_KEY="256-bit-primary-random-secret-key-2026"
# Comma-separated list of secondary keys accepted during zero-downtime rotation
JWT_SECRET_KEY_ROTATION="previous-jwt-secret-key-to-phase-out,backup-jwt-secret-key"

BLIP_PAY_WEBHOOK_SECRET="256-bit-primary-webhook-hmac-secret-2026"
BLIP_PAY_WEBHOOK_SECRET_ROTATION="previous-blip-webhook-secret"

# --- Institutional Email OTP & Resend API ---
RESEND_API_KEY="re_live_resend_api_key_xxx" # Or "mock-resend-api-key" for local/demo
EMAIL_OTP_EXPIRE_SECONDS="600" # 10 minutes
EMAIL_OTP_MAX_ATTEMPTS="3"
USE_MOCK_EMAIL_OTP="False" # Set to "True" in local dev to accept OTP "123456"

# --- Production Mode Flag ---
ENVIRONMENT="production" # Rejects default testnet secrets via validate_production_secrets()
```

---

## 4. OpenAPI 3.1.0 API Schema Additions
Two new endpoints have been added to `/api/v1/verification`:

* `POST /api/v1/verification/send-email-otp`
  * **Request Body:** `{"user_id": "uuid", "email": "student@unilag.edu.ng"}`
  * **Response (`200 OK`):** `{"success": true, "message": "OTP sent to student@unilag.edu.ng", "email": "student@unilag.edu.ng", "expires_in_seconds": 600}`
  * **Rate Limit:** `30 req/min` + per-email `60s cooldown` (`429 Too Many Requests`).
* `POST /api/v1/verification/verify-email-otp`
  * **Request Body:** `{"user_id": "uuid", "email": "student@unilag.edu.ng", "otp_code": "123456"}`
  * **Response (`200 OK`):** `{"success": true, "message": "Institutional email verified successfully.", "user_id": "uuid", "email": "student@unilag.edu.ng", "verified_at": "2026-07-30T..."}`
  * **Lockout Policy:** 3 failed attempts invalidates the OTP (`403 Forbidden`).

---

## 5. Deployment & Migration Steps (Railway & Vercel)

### Step 1: Upgrade Backend Environment Variables
1. In Railway Dashboard $\rightarrow$ **Variables**, add `REDIS_URL`, `RESEND_API_KEY`, and set `ENVIRONMENT=production`.
2. Populate `JWT_SECRET_KEY` and `BLIP_PAY_WEBHOOK_SECRET` with 256-bit random strings generated via `openssl rand -hex 32`.

### Step 2: Deploy Backend & Verify Secrets Gate
1. Deploy `campusos-backend` container.
2. During application startup, `settings.validate_production_secrets()` automatically inspects the environment. If any insecure default keys remain when `ENVIRONMENT=production`, startup will halt immediately with a descriptive `ValueError`.

### Step 3: Check Health & Redis Connection
1. Execute `curl https://api.campusos.ng/health` and verify HTTP 200 `{"status": "healthy"}`.
2. Inspect structured JSON logs in Railway to confirm: `{"message": "Redis distributed rate limiter initialized successfully."}`.

### Step 4: Verify Frontend CORS Compatibility
1. In Vercel Dashboard $\rightarrow$ **Environment Variables**, confirm `NEXT_PUBLIC_API_URL` points to the upgraded backend.
2. Verify that CORS preflight `OPTIONS` requests from `https://campusos.vercel.app` return `200 OK` with `Access-Control-Allow-Origin: https://campusos.vercel.app`.
