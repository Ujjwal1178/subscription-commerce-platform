# Rate Limiting - Interview Questions

## Q1: What is Rate Limiting and why is it needed?

**Answer:**
Rate limiting controls how many requests a client can make to an API within a time window.

**Why needed:**
| Threat | How Rate Limiting Helps |
|--------|------------------------|
| DDoS attacks | Limits request flood from single source |
| Brute force | Prevents password guessing attempts |
| API abuse | Stops scraping, spam |
| Cost control | Prevents expensive operations abuse |
| Fair usage | Ensures all users get resources |

---

## Q2: What are common Rate Limiting algorithms?

**Answer:**

### 1. Fixed Window
```
Window: 0:00 - 1:00 → 10 requests allowed
Window: 1:00 - 2:00 → 10 requests allowed (reset)
```
**Problem:** Burst at window edges (19 requests in 2 seconds if timed right)

### 2. Sliding Window
```
Always looks at "last 60 seconds" from current time
More accurate, no edge bursts
```

### 3. Token Bucket
```
Bucket holds 10 tokens
1 token regenerates every 6 seconds
Each request costs 1 token
Allows controlled bursts
```

### 4. Leaky Bucket
```
Requests enter bucket
Processed at fixed rate (like water leaking)
Overflow = rejected
Smooths out traffic
```

**Interview tip:** Know Fixed vs Sliding Window deeply - most commonly asked.

---

## Q3: Where should Rate Limiting be implemented?

**Answer:**

```
┌─────────────────────────────────────────────────────────┐
│  Client Request                                         │
│       ↓                                                 │
│  [CDN/WAF] ← Layer 1: Edge rate limiting (Cloudflare)   │
│       ↓                                                 │
│  [Load Balancer] ← Layer 2: Infrastructure level        │
│       ↓                                                 │
│  [API Gateway] ← Layer 3: Application level (our code)  │
│       ↓                                                 │
│  [Service] ← Layer 4: Business logic specific           │
└─────────────────────────────────────────────────────────┘
```

**For our project:** Redis-based rate limiting at API Gateway/Application level.

---

## Q4: Why use Redis for Rate Limiting instead of Database?

**Answer:**

| Aspect | Redis | Database |
|--------|-------|----------|
| Speed | ~0.1ms (in-memory) | ~5-10ms (disk I/O) |
| TTL support | Built-in auto-expire | Manual cleanup needed |
| Atomic operations | INCR, EXPIRE atomic | Need transactions |
| Scalability | Designed for this | Overkill, adds load |

**Redis commands for rate limiting:**
```redis
INCR rate_limit:192.168.1.1:login    # Increment counter
EXPIRE rate_limit:192.168.1.1:login 60  # Auto-delete in 60s
GET rate_limit:192.168.1.1:login     # Check current count
```

---

## Q5: How to handle shared IP problem (office/NAT)?

**Problem:**
- 50 office employees share 1 public IP
- Strict IP rate limiting blocks legitimate users

**Answer: Multi-Layer Approach**

```python
# Layer 1: Global IP limit (generous)
GLOBAL_IP_LIMIT = 100  # requests per minute

# Layer 2: Endpoint-specific (tighter for sensitive)
ENDPOINT_LIMITS = {
    "/auth/login": 20,        # per minute per IP
    "/auth/register": 10,
    "/auth/verify-otp": 15,
    "/api/data": 60,
}

# Layer 3: User-based (after authentication)
USER_LIMIT = 100  # per minute per user_id
```

**Why this works:**
- Normal office usage: ~50 users × 2 req/min = 100/min → within global limit
- Attack from single IP: Will hit endpoint limit quickly
- Authenticated users: Tracked by user_id, not IP

---

## Q6: How to identify devices when you only get public IP?

**Answer:**

Backend receives only **public IP** due to NAT (Network Address Translation).

**Alternatives for device identification:**

| Method | Reliability | Notes |
|--------|------------|-------|
| Browser Fingerprinting | ~90% | Screen, fonts, plugins, timezone |
| Device ID (mobile apps) | High | Android ID, iOS Vendor ID |
| Cookies/LocalStorage | Medium | User can clear |
| User Account | Best | After login, track by user_id |

**Industry standard:**
- Pre-login: IP + Fingerprint hash
- Post-login: User ID (most reliable)

---

## Q7: What is User Enumeration Attack? How does Rate Limiting help?

**Answer:**

**Attack:**
```
Hacker tries: test1@gmail.com → "User not found"
Hacker tries: test2@gmail.com → "User not found"  
Hacker tries: ujjwal@gmail.com → "Wrong password" 
Hacker: "Found valid email!"
```

**Prevention:**
1. **Generic messages:** "Invalid email or password" (same for both)
2. **Rate limiting:** 5 attempts per IP per minute
3. **CAPTCHA:** After 3 failed attempts

```python
# Rate limit key for login attempts
key = f"login_attempt:{ip}:{email_hash}"
if redis.get(key) > 5:
    raise TooManyAttemptsError("Try again in 5 minutes")
```

---

## Q8: Implement basic Redis Rate Limiter (Code)

**Answer:**

```python
import redis
from fastapi import HTTPException, Request

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def rate_limit(request: Request, limit: int = 10, window: int = 60):
    """
    Simple sliding window rate limiter.
    
    Args:
        request: FastAPI request object
        limit: Max requests allowed
        window: Time window in seconds
    """
    # Get client IP
    client_ip = request.client.host
    endpoint = request.url.path
    
    # Create unique key
    key = f"rate_limit:{client_ip}:{endpoint}"
    
    # Increment counter
    current = redis_client.incr(key)
    
    # Set expiry on first request
    if current == 1:
        redis_client.expire(key, window)
    
    # Check limit
    if current > limit:
        ttl = redis_client.ttl(key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {ttl} seconds."
        )
    
    return True

# Usage in FastAPI
@app.post("/auth/login")
def login(request: Request, data: LoginRequest):
    rate_limit(request, limit=10, window=60)  # 10 per minute
    # ... login logic
```

---

## Q9: What HTTP status code for rate limiting?

**Answer:** `429 Too Many Requests`

**Response should include:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 45
}
```

**Headers:**
```
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1693234567
```

---

## Q10: Rate Limiting vs Throttling - Difference?

**Answer:**

| Aspect | Rate Limiting | Throttling |
|--------|--------------|------------|
| Behavior | Block excess requests | Slow down excess requests |
| User experience | Error (429) | Delayed response |
| Use case | Strict limits | Graceful degradation |

**Example:**
- Rate limit: 11th request → Rejected immediately
- Throttle: 11th request → Queued, processed after delay

---

## Follow-up Questions Interviewer May Ask:

1. "How would you implement rate limiting in a distributed system with multiple servers?"
   → Centralized Redis cluster, or distributed rate limiting with eventual consistency

2. "What if Redis goes down?"
   → Fallback: Allow requests (fail-open) or use local in-memory cache

3. "How to rate limit by user AND by IP simultaneously?"
   → Check both limits, reject if either exceeded

4. "How to handle legitimate high-traffic users (API partners)?"
   → API keys with custom rate limits, tier-based pricing

5. "How do you test rate limiting?"
   → Load testing tools (k6, locust), unit tests with mocked Redis
