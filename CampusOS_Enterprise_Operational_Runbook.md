# CampusOS — Enterprise Operational Runbook & Day-2 Operations Guide
**Document Version:** 1.0.0-run  
**Date:** July 30, 2026  
**Audience:** Site Reliability Engineers (SRE), DevOps & Release Engineers  

---

## 1. System Overview & Health Monitoring
CampusOS runs as a stateless Modular Monolith backend on FastAPI/Uvicorn, backed by PostgreSQL 16 (RDS), Redis 7 (ElastiCache/Railway), Quai Network EVM JSON-RPC (`Chain ID 9000`), and Blip Pay Payment Gateway.

### 1.1 Automated Health Probe
* **Probe Endpoint:** `GET https://api.campusos.ng/health`
* **Expected Response (`200 OK`):**
  ```json
  {
    "status": "healthy",
    "service": "CampusOS Backend",
    "version": "1.0.0",
    "blockchain": "Quai Network Testnet (Mock Enabled: True)",
    "storage": "Cloudinary (Mock Enabled: True)"
  }
  ```

---

## 2. Standard Operating Procedures (SOPs)

### SOP-001: Zero-Downtime Secret Rotation (JWT & Webhook HMAC)
When rotating secret keys in staging or enterprise production:
1. **Generate New Secret Key:**
   ```bash
   openssl rand -hex 32
   ```
2. **Update Environment Variables in AWS Secrets Manager / Railway:**
   * Set `JWT_SECRET_KEY_ROTATION` to the **current primary key** (so existing signed tokens remain valid).
   * Set `JWT_SECRET_KEY` to the **newly generated key** (all new tokens will be signed with this key).
3. **Deploy Backend Containers:**
   * Perform rolling deployment across Uvicorn containers.
   * `settings.get_jwt_secret_keys()` automatically validates both keys during the transition.
4. **Retire Old Key (After 24 Hours / Token TTL):**
   * After 24 hours (`1440 minutes`), clear `JWT_SECRET_KEY_ROTATION=""` in environment variables and redeploy.

---

### SOP-002: Monitoring & Debugging Distributed Rate Limits (Redis)
To inspect or reset rate limits for a specific client IP address:
1. **Connect to Redis Server:**
   ```bash
   redis-cli -u $REDIS_URL
   ```
2. **Inspect Active Sliding Window Timestamps for an IP:**
   ```bash
   ZCARD "campusos:ratelimit:192.168.1.50"
   ```
3. **Clear Rate Limit for a Blocked IP Address:**
   ```bash
   DEL "campusos:ratelimit:192.168.1.50"
   ```
4. **Verify In-Memory Fallback Behavior:**
   * If Redis becomes unreachable, log monitoring will automatically alert: `Redis rate limiter initialization failed... falling back to in-memory sliding window`. No manual intervention is required to maintain API availability.

---

### SOP-003: Investigating Webhook Replay & Timestamp Drift Alerts
When Datadog or CloudWatch triggers an alert for `Webhook timestamp drift exceeded allowable window`:
1. **Query SIEM Logs by Correlation ID:**
   * Filter structured JSON logs where `"name": "campusos.payments"` and `"level": "WARNING"`.
   * Extract `"request_id"` and `"correlation_id"`.
2. **Verify Client Clock Drift:**
   * Confirm if the payment gateway's NTP clock drifted or if an adversary is replaying captured HTTP headers.
3. **Check 24-Hour Redis Replay Cache:**
   ```bash
   GET "campusos:webhook_replay:blip_pay_reference_uuid"
   ```
   * If key exists, the webhook was already processed and locked escrow cleanly.

---

### SOP-004: Institutional Email OTP Incident Response
If a student reports being locked out (`Maximum OTP verification attempts exceeded`):
1. **Inspect Cooldown & Attempt Cache in Redis:**
   ```bash
   KEYS "campusos:otp:*"
   ```
2. **Manually Reset Student OTP Cache Key:**
   ```bash
   DEL "campusos:otp:user_uuid_001:student@unilag.edu.ng"
   DEL "campusos:otp_cooldown:student@unilag.edu.ng"
   ```
3. **Audit Verification History:**
   * Query PostgreSQL `verification_history` table for `user_id` to inspect previous OTP attempts and administrative actions.

---

## 3. SIEM Structured JSON Query Templates (CloudWatch / Datadog)

### 3.1 Querying Security Audit Events
```json
{
  "query": "service:campusos-backend @audit:true",
  "columns": ["@timestamp", "@action", "@actor_id", "@target_id", "@status", "@details"]
}
```

### 3.2 Querying High-Severity Rate Limit Lockouts
```json
{
  "query": "service:campusos-backend logger:campusos.ratelimit level:WARNING",
  "alert_rule": "count() > 50 in 5m"
}
```
