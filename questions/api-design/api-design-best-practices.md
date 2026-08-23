# API Design Best Practices

## Questions Covered

### Q1: Why POST for Login instead of GET?

**Answer:**
- GET sends data in URL: `/login?email=x&password=y`
- URL is visible in browser history, server logs, cached
- Password exposed!
- POST sends data in body (hidden)

**Rule:** Any sensitive data → POST

---

### Q2: Should error message reveal "Email not found" vs "Wrong password"?

**Answer:**
"Invalid email or password" - same message for both.

**Why?** Prevents **email enumeration attack**:
- Attacker tries random emails
- "Email not found" → email doesn't exist
- "Wrong password" → email exists! Now attacker knows.

**Exception:** Registration - "Email already registered" is acceptable for UX (trade-off decision based on app sensitivity)

---

### Q3: Should registration return tokens immediately?

**Answer:** No! Return tokens only after email verification.

**Why?**
- Fake emails can register
- User never verifies
- Account with unverified email has access

**Flow:**
1. Register → Success message + OTP sent
2. Verify OTP → Get tokens
3. Now user can access app

---

### Q4: Why soft delete sessions instead of hard delete?

**Answer:**
- **Soft delete:** `is_active = false, ended_at = now()`
- **Hard delete:** `DELETE FROM sessions`

**Benefits of soft delete:**
- Login history for user ("Where was I logged in?")
- Security audit trail
- Can show "Logged out from MacBook at 10:00 AM"

**Cleanup:** Daily job deletes sessions older than 30 days

---

### Q5: Why separate `user_sessions` table instead of JSON array in user table?

**Answer:**

JSON array approach:
```json
devices: [{id: "abc", name: "Chrome"}, {id: "xyz", name: "iPhone"}]
```

**Problems:**
- Array update is slow (read → modify → write)
- Can't index for fast lookup
- Concurrent updates = race condition

**Separate table:**
```
user_sessions: session_id | user_id | device_id | device_name
```

**Benefits:**
- Fast lookup: `WHERE device_id = 'abc'`
- Easy delete: `DELETE WHERE device_id = 'abc'`
- No race conditions
- Can add more fields easily

---

### Q6: Why store device_id in DB instead of full refresh token?

**Answer:**

| Approach | Storage | Lookup |
|----------|---------|--------|
| Full token hash | ~64 bytes | Match hash |
| Device ID only | ~20 bytes | Match device_id |

**Device ID approach:**
- JWT contains device_id
- DB stores device_id
- On refresh: verify JWT signature + check device_id exists in DB
- Smaller storage, same security

---

### Q7: Rate limiting vs Attempt limiting - What's the difference?

**Rate limiting:** Max N requests per time period
- Example: Max 3 OTP requests per 10 minutes
- Prevents spam/cost attack

**Attempt limiting:** Max N wrong attempts before block
- Example: Max 3 wrong OTP attempts → 20 min block
- Prevents brute force attack

**Both needed for OTP endpoints!**
