# Stateful vs Stateless Authentication

## Question
"What's the difference between session-based and JWT-based authentication? Which would you use in a microservices architecture?"

---

## Answer

> "Session-based authentication is **stateful** - the server stores session data in memory. JWT-based is **stateless** - all user info is embedded in the token itself.
>
> For microservices, I'd always choose JWT because:
> 1. Any server can verify the token (no shared state needed)
> 2. Scales horizontally without sticky sessions
> 3. Works across different services seamlessly
>
> Session-based breaks when you have multiple servers because the session exists only on the server that created it."

---

## Session-Based (Stateful) - The Problem

```
┌─────────────────────────────────────────────────────────────────────┐
│                 SESSION-BASED AUTHENTICATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   STEP 1: User logs in on Server 1                                  │
│                                                                     │
│   User ─────────────────▶ Server 1                                  │
│         POST /login                                                 │
│                               │                                     │
│                               ▼                                     │
│                    ┌─────────────────────┐                          │
│                    │    Server 1 Memory  │                          │
│                    │                     │                          │
│                    │  sessions = {       │                          │
│                    │    "abc123": {      │  ← Session IN MEMORY!    │
│                    │      user_id: 42    │                          │
│                    │    }                │                          │
│                    │  }                  │                          │
│                    └─────────────────────┘                          │
│                               │                                     │
│   User ◀─────────────────────┘                                      │
│         Set-Cookie: session_id=abc123                               │
│                                                                     │
│   ─────────────────────────────────────────────────────────────     │
│                                                                     │
│   STEP 2: Next request goes to Server 2 (load balanced)             │
│                                                                     │
│   User ─────────────────▶ Server 2                                  │
│         Cookie: session_id=abc123                                   │
│                               │                                     │
│                               ▼                                     │
│                    ┌─────────────────────┐                          │
│                    │    Server 2 Memory  │                          │
│                    │                     │                          │
│                    │  sessions = { }     │  ← EMPTY! 😱             │
│                    │                     │                          │
│                    │  "abc123"? Who?     │                          │
│                    └─────────────────────┘                          │
│                               │                                     │
│   User ◀─────────────────────┘                                      │
│         401 Unauthorized                                            │
│                                                                     │
│   USER: "I just logged in!" 😭                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## JWT-Based (Stateless) - The Solution

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JWT-BASED AUTHENTICATION                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   STEP 1: User logs in (any server)                                 │
│                                                                     │
│   User ─────────────────▶ Server 1                                  │
│         POST /login                                                 │
│                               │                                     │
│                               ▼                                     │
│                    Server creates JWT:                              │
│                    {                                                │
│                      "user_id": 42,       ← Data IN the token!      │
│                      "email": "ujjwal@",                            │
│                      "exp": 1234567890                              │
│                    }                                                │
│                    Signed with SECRET_KEY                           │
│                               │                                     │
│   User ◀─────────────────────┘                                      │
│         JWT: eyJhbGciOiJIUzI1NiIs...                                │
│                                                                     │
│   ─────────────────────────────────────────────────────────────     │
│                                                                     │
│   STEP 2: Next request (ANY server can handle!)                     │
│                                                                     │
│   User ─────────────────▶ Server 2                                  │
│         Authorization: Bearer eyJhbGciOiJIUzI1NiIs...               │
│                               │                                     │
│                               ▼                                     │
│                    Server 2:                                        │
│                    1. Decode JWT                                    │
│                    2. Verify signature (same SECRET_KEY)            │
│                    3. Extract user_id: 42 ✅                        │
│                    4. Process request                               │
│                               │                                     │
│   User ◀─────────────────────┘                                      │
│         200 OK                                                      │
│                                                                     │
│   WORKS! No shared state needed! ✅                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Difference

| Aspect | Session (Stateful) | JWT (Stateless) |
|--------|-------------------|-----------------|
| **Where is data?** | Server memory | Inside the token |
| **Scalability** | ❌ Need sticky sessions or shared store | ✅ Any server works |
| **Logout** | Easy - delete session | Harder - need token blacklist |
| **Token size** | Small (just session ID) | Larger (contains user data) |
| **Server memory** | Grows with users | Constant |

---

## Follow-up Questions

### Q1: "How do you logout with JWT?"

**Answer**: Since JWT is stateless, you can't "delete" it. Options:

```
1. Short expiry (15-30 min) + Refresh tokens
   - Access token expires quickly
   - Refresh token stored in DB, can be revoked

2. Token blacklist (Redis)
   - On logout, add token to blacklist
   - Check blacklist on each request
   - Clean up expired tokens

3. Token versioning
   - Store token_version in DB per user
   - Include version in JWT
   - On logout, increment version
   - Old tokens become invalid
```

### Q2: "What if someone steals the JWT?"

**Answer**:
```
Mitigations:
1. Short expiry times (15-30 min)
2. HTTPS only (prevent interception)
3. HttpOnly cookies (prevent XSS)
4. Refresh token rotation
5. Fingerprinting (IP, User-Agent)
```

### Q3: "Can you use sessions in microservices?"

**Answer**: Yes, but with **centralized session store**:
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│Server 1 │     │Server 2 │     │Server 3 │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     └───────────────┼───────────────┘
                     ▼
              ┌─────────────┐
              │    Redis    │
              │  (Sessions) │
              └─────────────┘

All servers read/write sessions to Redis.
Works, but adds latency and dependency.
```

### Q4: "Why not always use JWT then?"

**Answer**: JWT has downsides:
- Larger payload (bandwidth)
- Can't revoke immediately (without blacklist)
- Sensitive data in token (even if signed)
- Token refresh complexity

For **single server** apps, sessions are simpler. For **microservices**, JWT wins.

---

## Interview Tips

1. **Draw the diagram** - Show why sessions break with multiple servers
2. **Know tradeoffs** - JWT isn't perfect either (revocation, size)
3. **Mention solutions** - Refresh tokens, blacklisting
4. **Show you understand scaling** - This is a distributed systems question
