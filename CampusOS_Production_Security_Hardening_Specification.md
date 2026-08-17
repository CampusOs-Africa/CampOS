# CampusOS — Production Security Hardening Specification
**Document Version:** 1.0.0-sec  
**Date:** July 30, 2026  
**Scope:** Complete Production Engineering Security Improvements  

---

## 1. Architectural Overview of Security Hardening
This specification documents the engineering architecture, data flows, and cryptographic controls implemented for CampusOS to achieve enterprise production readiness on Quai Network and Blip Pay.

```
       [ Client / Browser ] ─── X-Request-ID / X-Correlation-ID ───► [ CorrelationIdMiddleware ]
                                                                                │
                                                                                ▼
       [ Production CORS Gate ] ◄── Only https://campusos.vercel.app ── [ CORSMiddleware ]
                                                                                │
                                                                                ▼
       [ Redis Sliding Window ] ◄── Atomic Lua Script (100/30 RPM) ─── [ RateLimitMiddleware ]
       (or In-Memory Fallback)                                                  │
                                                                                ▼
       [ API Routers (/api/v1) ] ───► [ Domain Services ] ───► [ Structured JSON Logger & SIEM ]
```

---

## 2. Institutional Email OTP Verification Architecture
To address Technical Debt **TD-SEC-002** from previous security audits, institutional `.edu.ng` email addresses now undergo active email inbox verification prior to document submission:

```
[Student] ──(1) POST /send-email-otp (user_id, email) ──► [VerificationService]
                                                                 │
    ┌────────────────────────────────────────────────────────────┴─────────────┐
    ▼                                                                          ▼
[Redis OTP Cache]                                                    [Resend Email API]
 • Key: "campusos:otp:{user_id}:{email}"                              • "Your code is: 482910"
 • TTL: 600s (10 min)                                                 • From: noreply@campusos.ng
 • Cooldown: 60s per email                                            • To: student@unilag.edu.ng
 • Max Attempts: 3
    ▲
    │
[Student] ──(2) POST /verify-email-otp (user_id, email, "482910") ──► [Constant-Time HMAC Check]
```

### 2.1 Security Controls & Policies
* **Cooldown Protection:** Enforces a mandatory 60-second cooldown per institutional email (`f"campusos:otp_cooldown:{email}"`). Requests within cooldown return `429 Too Many Requests`.
* **Lockout Protection:** Enforces a maximum of 3 failed verification attempts (`EMAIL_OTP_MAX_ATTEMPTS = 3`). Exceeding the limit deletes the OTP from cache and raises `403 Forbidden`.
* **Timing-Attack Immunity:** Code verification uses `hmac.compare_digest(stored_code, otp_code)` to prevent timing side-channel attacks.
* **Audit Trail Integration:** Upon successful verification, an immutable audit entry is recorded in `VerificationHistory` and emitted via the structured JSON audit logger.

---

## 3. Distributed Redis Sliding Window Rate Limiting
To address Technical Debt **TD-SEC-001**, `RateLimitMiddleware` now utilizes an atomic Lua script executed inside Redis to enforce sliding window rate limits across horizontally autoscaling Uvicorn worker containers:

### 3.1 Redis Lua Script Atomicity
```lua
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local max_limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
local current_count = redis.call('ZCARD', key)
if current_count >= max_limit then
    return 0
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, 60)
return 1
```

### 3.2 High-Availability Graceful Fallback
If the Redis server becomes unreachable or connection timeouts occur (`socket_timeout=0.5`), `RateLimitMiddleware` logs an administrative warning (`logger.warning("Redis atomic rate limit call failed... falling back to in-memory sliding window")`) and seamlessly switches to the in-memory token bucket, preventing network outages from disrupting API availability.

---

## 4. Webhook Replay Protection & Timestamp Drift Validation
To protect Blip Pay payment checkouts (`POST /api/v1/payments/webhook`) from replay attacks and timestamp manipulation:

### 4.1 Timestamp Drift Window ($\pm 300\text{ Seconds}$)
When incoming webhooks include the `X-Blip-Timestamp` header, `PaymentService.verify_webhook_signature()` validates:
$$\left| t_{\text{current}} - t_{\text{header}} \right| \le 300\text{ seconds}$$
If drift exceeds 300 seconds (5 minutes), the webhook is rejected immediately with `401 Unauthorized ("Webhook timestamp drift exceeded allowable window")`.

### 4.2 24-Hour Redis Replay Cache
`PaymentService.check_and_cache_webhook_replay(reference, ttl_seconds=86400)` checks if the payment reference (`blip_pay_xxx`) has been processed within the last 24 hours:
* **Fresh Webhook:** Adds the reference to Redis (`campusos:webhook_replay:{reference}`) with `EX=86400` and executes normal escrow lock state transitions.
* **Replayed Webhook:** Returns `True`. `OrderService.handle_webhook` logs `"Duplicate/replayed Blip Pay webhook detected; returning idempotently"` and returns HTTP `200 OK` without re-executing state changes or Quai Network transactions.

---

## 5. Multi-Key Secret Rotation Architecture
To enable zero-downtime rotation of cryptographic secrets:
* **JWT Secret Keys (`settings.get_jwt_secret_keys()`):** `verify_access_token` loops through the primary `JWT_SECRET_KEY` and all secondary keys defined in `JWT_SECRET_KEY_ROTATION`. Expired tokens raise `401 TOKEN_EXPIRED` immediately; invalid signatures fall back to testing subsequent keys in the rotation list.
* **Blip Pay Webhook Secrets (`settings.get_blip_webhook_secrets()`):** `verify_webhook_signature` loops through `BLIP_PAY_WEBHOOK_SECRET` and `BLIP_PAY_WEBHOOK_SECRET_ROTATION`, allowing payment gateway HMAC keys to be phased over cleanly.

---

## 6. Dynamic CORS Lockdown
`settings.get_cors_origins()` dynamically computes CORS allowlists based on `settings.ENVIRONMENT`:
* **Production Mode (`ENVIRONMENT=production`):** Enforces strict allowlist (`https://campusos.vercel.app`, `https://campusos.ng`). Rejects wildcard `'*'`.
* **Development/Test Mode:** Includes local development origins (`http://localhost:3000`, `http://127.0.0.1:3000`).

---

## 7. Structured JSON Logging & Correlation Tracing
All application loggers (`campusos.*`) format output as structured JSON via `python-json-logger`. Every request passing through `CorrelationIdMiddleware` sets contextvars (`request_id_var`, `correlation_id_var`) so every log line contains uniform trace metadata:

```json
{
  "timestamp": "2026-07-30T15:15:00Z",
  "level": "INFO",
  "name": "campusos.audit",
  "message": "AUDIT_EVENT: EMAIL_OTP_VERIFIED",
  "request_id": "req-9abfd4cba468",
  "correlation_id": "corr-c860ac4e13e4",
  "audit": true,
  "action": "EMAIL_OTP_VERIFIED",
  "actor_id": "user-001",
  "target_id": "user-001",
  "status": "SUCCESS",
  "service": "campusos-backend"
}
```
