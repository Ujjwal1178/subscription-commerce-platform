# Why Store Refresh Tokens? Isn't JWT Stateless?

## The Question
> "You said JWT is stateless, then why are you storing refresh tokens in the database?"

## Quick Answer
**Access tokens are stateless, but refresh tokens need storage for revocation capability.**

We use a **Stateful Refresh, Stateless Access** hybrid pattern.

---

## The Problem: Pure Stateless = No Revocation

```
┌─────────────────────────────────────────────────────────────────┐
│  SCENARIO: User logged in on Phone                              │
│                                                                  │
│  JWT Token:                                                      │
│  {                                                               │
│    "user_id": "123",                                             │
│    "exp": 1699999999  (2 hours from now)                        │
│  }                                                               │
│  Signature: Valid ✅                                             │
│                                                                  │
│  This token is SELF-CONTAINED. Server doesn't track it.         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: How to invalidate this token?                         │
│                                                                  │
│  - User logs in on Laptop (want to logout Phone)                │
│  - User clicks "Logout"                                          │
│  - Admin wants to ban user immediately                          │
│  - Security breach detected                                      │
│                                                                  │
│  ❌ You CAN'T! Token is valid until expiry.                     │
│  ❌ Server has no record of issued tokens.                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Solution 1: Store Full Refresh Token (Common Approach)

```
Database: refresh_tokens
┌─────────────────────────────────────────────────────────────┐
│ id │ user_id │ token_hash      │ device    │ expires_at    │
├─────────────────────────────────────────────────────────────┤
│ 1  │ usr_123 │ sha256(token)   │ iPhone    │ 2026-08-25    │
│ 2  │ usr_456 │ sha256(token)   │ Android   │ 2026-08-24    │
└─────────────────────────────────────────────────────────────┘

On refresh: Hash incoming token → Find in DB → If exists, issue new access token
On logout: Delete token from DB
On new login: Delete old tokens → Insert new one

✅ Can revoke specific tokens
❌ Stores ~64 bytes per token (hash)
```

---

## Solution 2: Store Device ID Only (Optimized Approach) ⭐

```
Database: user_sessions
┌─────────────────────────────────────────────────────────────┐
│ user_id │ device_id    │ device_name │ last_active         │
├─────────────────────────────────────────────────────────────┤
│ usr_123 │ dev_abc123   │ iPhone 14   │ 2026-08-23 10:00    │
└─────────────────────────────────────────────────────────────┘

JWT Refresh Token contains:
{
  "user_id": "usr_123",
  "device_id": "dev_abc123",  ← KEY!
  "exp": 1699999999
}

On refresh: 
  1. Verify JWT signature
  2. Check: Does device_id exist in DB for this user?
  3. If yes → Issue new access token
  4. If no → Reject (session was revoked)

On new login (single device mode):
  1. Update device_id in DB (overwrite old one)
  2. Old device's JWT still has old device_id
  3. Old device tries refresh → device_id not found → Logout!

✅ Smaller storage (~20 bytes vs 64 bytes)
✅ Device-level control
✅ Can implement "max N devices" easily
```

---

## Comparison Table

| Aspect | Store Full Token | Store Device ID |
|--------|-----------------|-----------------|
| Storage per session | ~64 bytes | ~20 bytes |
| Revocation | Token-level | Device-level |
| Multiple tokens per device | Yes | No (one session per device) |
| Token rotation | Creates new row | Same row |
| "Logout all devices" | Delete all tokens | Delete all device_ids |
| Session limit (max 3 devices) | Count tokens | Count device_ids |

---

## Why Access Token Stays Stateless?

```
┌─────────────────────────────────────────────────────────────────┐
│  ACCESS TOKEN                      REFRESH TOKEN                │
│  ──────────────                    ──────────────               │
│  Lifetime: 7-15 minutes            Lifetime: Hours to Days      │
│  Used: Every API call              Used: Only to get new access │
│  Storage: None                     Storage: DB (device_id)      │
│  Revocable: No                     Revocable: Yes               │
│  DB lookup: No (fast!)             DB lookup: Yes (rare)        │
│                                                                  │
│  If access token is stolen, attacker has max 7-15 min window   │
│  If refresh token is stolen, we can revoke it instantly        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Real Interview Answer

> "We use a **hybrid stateful-refresh, stateless-access** pattern. 
>
> Access tokens are pure stateless JWTs - we never store them, just verify signature and expiry. This keeps 99% of API calls fast with zero DB lookup.
>
> Refresh tokens are semi-stateful - we store a `device_id` in the database and embed it in the refresh token JWT. On refresh, we verify the device_id still exists. This gives us revocation capability for:
> - Logout (delete device session)
> - Single device login (replace device_id on new login)
> - Security incidents (admin can revoke all sessions)
> - 'Logout from all devices' feature
>
> The trade-off is one DB lookup per token refresh (every 7-15 minutes per user), which is acceptable for the control it provides."

---

## Follow-up Questions

### Q1: "What if attacker steals the refresh token?"

**Answer:**
1. They can generate access tokens until we detect it
2. **Detection methods:**
   - Refresh token reuse detection (if same token refreshed twice → breach!)
   - Device fingerprinting (browser, IP, location)
   - Anomaly detection (refresh from different country)
3. **Mitigation:** Rotate refresh tokens on each use (one-time use)

### Q2: "Why not just use very short access tokens (30 seconds)?"

**Answer:**
1. Too many refresh requests → DB load
2. Poor user experience (brief network issue = logged out)
3. 7-15 minutes is industry standard balance

### Q3: "How does 'Logout from all devices' work?"

**Answer:**
```sql
DELETE FROM user_sessions WHERE user_id = 'usr_123';
```
All device_ids gone → All refresh tokens become invalid → All devices logged out on next refresh attempt.

### Q4: "What about Redis vs PostgreSQL for session storage?"

**Answer:**
| Storage | Pros | Cons |
|---------|------|------|
| PostgreSQL | Persistent, ACID, survives restart | Slower |
| Redis | Super fast, TTL support | Can lose data |
| Both | Fast reads, persistent backup | Complex |

For sessions, Redis is often enough (losing sessions = users re-login, not catastrophic).

---

## Key Takeaway

> **Stateless is a spectrum, not binary.** 
> 
> Pure stateless = no control. Pure stateful = doesn't scale.
> 
> **Hybrid approach:** Stateless for frequent operations (API calls), Stateful for rare but critical operations (token refresh, revocation).
