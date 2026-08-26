# JWT (JSON Web Token) - Deep Dive

## Question 1: JWT kya hai aur structure kya hai?

### Answer:

**JWT = JSON Web Token** - A self-contained token for authentication

**Structure (3 parts separated by dots):**
```
eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMTIzIn0.SIGNATURE
        │                      │                    │
     HEADER                 PAYLOAD             SIGNATURE
```

| Part | Content | Encoded |
|------|---------|---------|
| Header | `{"alg": "HS256", "typ": "JWT"}` | Base64 |
| Payload | `{"user_id": "123", "exp": 1699999}` | Base64 |
| Signature | HMAC(header.payload, SECRET) | Binary |

---

## Question 2: User payload decode karke modify kar de (exp badhade), toh kaise pata chalega?

### Answer:

**SIGNATURE prevents tampering!**

```
Original:
  Payload: {"user_id": "123", "exp": 1699999}
  Signature: HMAC("header.payload", SECRET) = "abc123"

Attacker modifies:
  Payload: {"user_id": "123", "exp": 9999999999}  ← Changed!
  Signature: "abc123"  ← Can't change (needs SECRET)

Server validates:
  Recalculate: HMAC("header.NEW_payload", SECRET) = "xyz789"
  Compare: "abc123" ≠ "xyz789"
  
  MISMATCH! TOKEN REJECTED! 🚫
```

**Attacker can't create valid signature without SECRET_KEY!**

---

## Question 3: Secret key leak ho jaye toh kya hoga?

### Answer:

**DISASTER! Attacker can:**
- Create valid tokens for any user
- Modify expiry to never expire
- Impersonate admins

**Mitigation:**
1. **Immediate key rotation** - Change SECRET_KEY
2. **All existing tokens invalid** - Users re-login
3. **Never commit secrets** - Use env vars, secret managers
4. **Key rotation schedule** - Periodic key changes

---

## Question 4: Access Token vs Refresh Token - difference?

### Answer:

| Aspect | Access Token | Refresh Token |
|--------|--------------|---------------|
| **Purpose** | API access | Get new access token |
| **Lifetime** | Short (7-15 min) | Long (2hr - 7 days) |
| **Stored** | Memory/LocalStorage | HttpOnly Cookie |
| **Contains** | user_id, name, device_id | user_id, device_id |
| **Sent with** | Every API request | Only /refresh endpoint |

**Why two tokens?**
- Access token short = Less damage if stolen
- Refresh token long = Good UX (don't login every 7 min)

---

## Question 5: Refresh token se naya access token kaise milta hai?

### Answer:

```
POST /refresh
{
  "refresh_token": "eyJ..."
}
         │
         ▼
┌─────────────────────────────────────┐
│  1. Verify signature (SECRET_KEY)   │
│  2. Check expiry (not expired?)     │
│  3. Extract device_id from token    │
│  4. Check DB: device_id matches?    │
│     - Yes → Return new access_token │
│     - No → Reject (logged out)      │
└─────────────────────────────────────┘
```

**device_id validation = Single device login!**

---

## Question 6: Single device login kaise achieve karte hain?

### Answer:

```
# User logs in on Phone
device_id = "phone123" → Stored in DB

# User logs in on Laptop (new login)
device_id = "laptop456" → REPLACE in DB

# Phone tries to refresh
Token has: "phone123"
DB has: "laptop456"
"phone123" ≠ "laptop456" → REJECTED!

Phone user is automatically logged out!
```

**No explicit logout needed - device_id mismatch = session invalid**

---

## Question 7: JWT mein kya store karna chahiye, kya nahi?

### Answer:

**DO store:**
- user_id (identifier)
- device_id (session validation)
- user_name (display, non-sensitive)
- role (authorization)
- exp (expiry)
- iat (issued at)

**DON'T store:**
- email (PII)
- password (never!)
- phone number (PII)
- sensitive personal data
- large data (increases token size)

**Why?** JWT payload is just Base64 - anyone can decode and read!

---

## Question 8: JWT verify karne ke liye DB call zaruri hai?

### Answer:

**For Access Token: NO (Stateless)**
```
Receive token → Verify signature → Check expiry → Allow
```
No DB needed! That's the beauty of JWT.

**For Refresh Token: YES (Semi-stateless)**
```
Receive token → Verify signature → Check expiry 
             → Check device_id in DB → Allow
```
DB call needed for device_id validation.

---

## Question 9: JWT vs Session-based auth - tradeoffs?

### Answer:

| Aspect | JWT | Session |
|--------|-----|---------|
| Storage | Client-side | Server-side |
| Scalability | Easy (stateless) | Hard (shared session store) |
| Revocation | Hard (wait for expiry) | Easy (delete session) |
| Size | Larger (~500 bytes) | Small (session ID) |
| DB calls | Minimal | Every request |

**JWT good for:** Microservices, APIs, Mobile apps
**Session good for:** Traditional web apps, need instant revocation

---

## Question 10: How to invalidate/revoke a JWT before expiry?

### Answer:

**Options:**

1. **Token blacklist (Redis)**
   ```
   On logout: Add token to Redis blacklist
   On verify: Check if token in blacklist
   ```

2. **Short expiry + Refresh tokens**
   - Access token: 7 min (damage limited)
   - Refresh token: Can be revoked via device_id

3. **Token versioning**
   - Store token_version in user table
   - Include version in JWT
   - Increment version on logout = all old tokens invalid

4. **device_id validation** (Our approach)
   - Change device_id = old tokens invalid

---

## Summary

| Concept | Key Point |
|---------|-----------|
| Signature | Prevents tampering, needs SECRET |
| Base64 | NOT encryption, anyone can read |
| Access Token | Short-lived, stateless validation |
| Refresh Token | Long-lived, DB validation |
| device_id | Enables single-device login |
| Revocation | Tricky with pure JWT, use hybrid |

---

## Tags
`jwt` `authentication` `security` `tokens` `refresh-token`
