# Rate Limiting: DB vs Redis - Where to Store?

## Question 1: Rate limiting Redis mein kyun karte hain, DB mein kyun nahi?

### Answer:

**Rate limiting = Per-request check!**

Every single API call pe check karna hota hai:
- "Has this user exceeded 10 requests/minute?"

**If we use DB:**
```
Request 1 → DB query → slow
Request 2 → DB query → slow
Request 3 → DB query → slow
... (10 requests = 10 DB queries)

DB load: 10 queries/minute/user
1000 users = 10,000 DB queries/minute just for rate limiting!
```

**If we use Redis:**
```
Request 1 → Redis INCR → microseconds
Request 2 → Redis INCR → microseconds
Request 3 → Redis INCR → microseconds
... (10 requests = 10 Redis ops, but FAST)

Redis handles millions of ops/second, no sweat!
```

### Performance Comparison:

| Aspect | DB | Redis |
|--------|-----|-------|
| Latency | ~5-50ms | ~0.1-1ms |
| Ops/sec | ~10,000 | ~100,000+ |
| Storage | Disk | Memory |
| TTL support | Manual cleanup | Native EXPIRE |
| Atomic increment | Needs transaction | Native INCR |

---

## Question 2: Redis mein rate limiting kaise implement karte hain?

### Answer:

**Simple approach - Counter with TTL:**

```python
import redis

r = redis.Redis()

def is_rate_limited(user_id: str, limit: int = 10, window: int = 60) -> bool:
    """
    Check if user exceeded rate limit.
    
    Args:
        user_id: Unique identifier
        limit: Max requests allowed
        window: Time window in seconds
    """
    key = f"rate:{user_id}"
    
    # Increment counter
    current = r.incr(key)
    
    # Set TTL only on first request
    if current == 1:
        r.expire(key, window)
    
    return current > limit
```

**How it works:**
```
First request:
  INCR rate:user123 → 1
  EXPIRE rate:user123 60 → TTL set
  
Next requests (within 60s):
  INCR rate:user123 → 2, 3, 4...
  
After 60s:
  Key auto-expires
  Fresh window starts
```

---

## Question 3: Rate limiting ke liye Redis key structure kya hona chahiye?

### Answer:

**Different granularities, different keys:**

```python
# Per IP (global protection)
rate:ip:192.168.1.1

# Per user (authenticated endpoints)
rate:user:uuid-123

# Per endpoint per IP
rate:login:ip:192.168.1.1

# Per endpoint per user
rate:otp_verify:user:uuid-123

# Per action per user
rate:resend_otp:user:uuid-123
```

**Example .env config:**
```
LOGIN_RATE_LIMIT_PER_MINUTE=10
OTP_VERIFY_RATE_LIMIT_PER_MINUTE=5
OTP_RESEND_RATE_LIMIT_PER_10MIN=3
```

---

## Question 4: DB-based attempt tracking vs Redis rate limiting - dono ki zaroorat kyun?

### Answer:

**Both serve different purposes!**

| Aspect | DB Attempt Tracking | Redis Rate Limiting |
|--------|---------------------|---------------------|
| **Purpose** | Security audit, account locking | DDoS protection, fair usage |
| **Persistence** | Forever (audit trail) | Temporary (window-based) |
| **Granularity** | Per-action lifetime | Per-time-window |
| **Example** | "3 wrong OTPs = account blocked" | "Max 10 OTP attempts/minute" |

**Flow with BOTH:**

```
User enters wrong OTP
        │
        ▼
┌─────────────────┐
│  REDIS CHECK    │  "10 attempts this minute allowed?"
│  (rate limit)   │
└────────┬────────┘
         │
    Passed? ──No──→ 429 Too Many Requests
         │
        Yes
         ▼
┌─────────────────┐
│  DB CHECK       │  "3 lifetime attempts remaining?"
│  (attempt track)│
└────────┬────────┘
         │
    Passed? ──No──→ Account Blocked (need support)
         │
        Yes
         ▼
┌─────────────────┐
│  Verify OTP     │
└─────────────────┘
```

**In our OTPVerification table:**
```python
remaining_retry = Column(Integer, default=3)  # Lifetime attempts
is_user_blocked = Column(Boolean, default=False)  # Account locked
```

**This is separate from Redis rate limiting!**

---

## Question 5: What if Redis is down? Rate limiting ka fallback kya hai?

### Answer:

**Options:**

1. **Fail Open (Allow requests)**
   - Risky! Attackers can exploit
   - Use only if rate limiting is non-critical

2. **Fail Closed (Block all requests)**
   - Safe but bad UX
   - Returns 503 Service Unavailable

3. **Local fallback (Best)**
   - In-memory counter as backup
   - Less accurate but better than nothing

```python
def is_rate_limited(user_id: str, limit: int = 10) -> bool:
    try:
        return redis_rate_check(user_id, limit)
    except redis.ConnectionError:
        # Fallback to local memory
        return local_memory_rate_check(user_id, limit)
```

**Production setup:**
- Redis Cluster for HA
- Redis Sentinel for failover
- Multiple replicas

---

## Question 6: Sliding window vs Fixed window rate limiting?

### Answer:

**Fixed Window:**
```
|---- Minute 1 ----|---- Minute 2 ----|
     8 requests         2 requests

At minute boundary, counter resets.
Problem: 10 requests at end of min 1 + 10 at start of min 2 = 20 in 2 seconds!
```

**Sliding Window:**
```
         |---- Last 60 seconds ----|
              Moves with time
              
No boundary exploits, smoother limiting.
```

**Redis Sliding Window implementation:**
```python
def sliding_window_rate_limit(user_id: str, limit: int, window: int):
    now = time.time()
    key = f"rate:{user_id}"
    
    pipe = redis.pipeline()
    # Remove old entries
    pipe.zremrangebyscore(key, 0, now - window)
    # Add current request
    pipe.zadd(key, {str(now): now})
    # Count requests in window
    pipe.zcard(key)
    # Set TTL
    pipe.expire(key, window)
    
    results = pipe.execute()
    return results[2] > limit
```

---

## Summary

| What to Check | Where | Why |
|---------------|-------|-----|
| Requests/minute | Redis | Fast, TTL, frequent checks |
| Lifetime attempts | DB | Audit trail, persistent |
| Account blocked | DB | Important security state |

**Redis = Shield (fast rejection)**
**DB = Audit (persistent record)**

---

## Tags
`rate-limiting` `redis` `system-design` `security` `performance`
