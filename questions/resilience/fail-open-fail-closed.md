# Fail-Open vs Fail-Closed Strategies

## Question 1: Fail-Open aur Fail-Closed mein kya difference hai?

### Answer:

Jab koi dependency (Redis, external service) fail ho jaye:

| Strategy | Behavior | Example |
|----------|----------|---------|
| **Fail-Open** | Allow the request | Redis down → Rate limit skipped, request proceeds |
| **Fail-Closed** | Block the request | Redis down → All requests blocked |

**Analogy:**

```
Building Security Gate:

Fail-Open (Fire Safety):
  - Power goes out
  - Gate OPENS automatically
  - People can escape (safety > security)

Fail-Closed (Bank Vault):
  - Power goes out
  - Vault stays LOCKED
  - Protect assets (security > convenience)
```

---

## Question 2: Rate limiting ke liye kaunsa strategy use karna chahiye?

### Answer:

**It depends on the context!**

| Scenario | Strategy | Reason |
|----------|----------|--------|
| General API rate limit | **Fail-Open** | UX > temporary vulnerability |
| Login attempts | **Fail-Open/Closed** | Depends on risk tolerance |
| Payment/Financial | **Fail-Closed** | Security critical |
| OTP verification | **Fail-Open** | User shouldn't be blocked |
| Admin operations | **Fail-Closed** | High privilege actions |

**Code example:**

```python
# Fail-Open (our rate limiter)
try:
    result = check_rate_limit(...)
except RedisError:
    # Allow request to proceed
    return RateLimitInfo(allowed=True)

# Fail-Closed alternative
try:
    result = check_rate_limit(...)
except RedisError:
    # Block request
    raise ServiceUnavailableError("Rate limit service down")
```

---

## Question 3: Production mein fail-open risks kaise mitigate karte hain?

### Answer:

**Multiple layers of protection:**

1. **Redis High Availability**
   - Redis Cluster (multiple nodes)
   - Redis Sentinel (auto-failover)
   - 99.99% uptime target

2. **Local Fallback**
   ```python
   try:
       return redis_rate_check(user_id)
   except RedisError:
       # In-memory fallback (less accurate but works)
       return local_memory_rate_check(user_id)
   ```

3. **Monitoring & Alerts**
   - Alert when Redis unreachable
   - Track fail-open events
   - Auto-scaling for traffic spikes

4. **Secondary Protection**
   - DB-level attempt tracking (persistent)
   - IP-based blocking at load balancer
   - WAF (Web Application Firewall) rules

---

## Question 4: Authentication mein fail-closed kyun prefer karte hain kuch companies?

### Answer:

**Trade-off analysis:**

| Fail-Open (Auth) | Fail-Closed (Auth) |
|------------------|-------------------|
| Users can login | Users blocked |
| Attacker can brute-force during outage | Attacker also blocked |
| Better UX | Worse UX |
| Security risk window | No security risk |

**Companies choose based on:**
- **Banks:** Fail-Closed (security > UX)
- **Social Media:** Fail-Open (UX > temporary risk)
- **E-commerce:** Depends (checkout: closed, browsing: open)

**Interview answer:** "There's no universal right answer. It's a business decision based on risk tolerance, user impact, and the specific operation being protected."

---

## Question 5: Graceful degradation kya hai?

### Answer:

**Graceful degradation = Partial functionality instead of complete failure**

```
Full Service:
  Rate Limiting (Redis) ✓
  + User Auth (DB) ✓
  + Full Features ✓

Redis Down → Graceful Degradation:
  Rate Limiting (Skipped/Local) ⚠️
  + User Auth (DB) ✓
  + Limited Features ✓
  
vs Complete Failure:
  Everything down ❌
```

**Implementation:**
```python
def process_request():
    # Try Redis rate limit
    rate_limited = False
    try:
        rate_limited = check_redis_rate_limit()
    except RedisError:
        # Log and continue without rate limit
        logger.warning("Redis down, skipping rate limit")
    
    if rate_limited:
        return error_response()
    
    # Continue with core functionality
    return process_core_logic()
```

---

## Question 6: Hybrid approach kya hota hai?

### Answer:

**Use both strategies for different scenarios:**

```python
def smart_fail_strategy(action: str, redis_error: Exception):
    """
    Different strategies for different actions.
    """
    
    # Critical actions → Fail-Closed
    critical_actions = ["payment", "password_change", "admin_action"]
    if action in critical_actions:
        raise ServiceUnavailableError("Security service unavailable")
    
    # Normal actions → Fail-Open
    logger.warning(f"Rate limit skipped for {action}: {redis_error}")
    return RateLimitInfo(allowed=True)
```

**Config-driven approach:**
```python
RATE_LIMIT_FAIL_STRATEGY = {
    "login": "open",
    "register": "open", 
    "otp_verify": "open",
    "payment": "closed",
    "password_reset": "closed",
}
```

---

## Summary Table

| Factor | Fail-Open | Fail-Closed |
|--------|-----------|-------------|
| UX Impact | Low (service continues) | High (users blocked) |
| Security Risk | Higher during outage | Lower |
| Use Case | Non-critical operations | Security-critical ops |
| Recovery | Automatic when service returns | Automatic |
| Monitoring Need | High (track vulnerability window) | Medium |

---

## Interview Key Points

1. **Know both strategies** and when to use each
2. **Explain trade-offs** clearly
3. **Mention hybrid approaches** for real-world systems
4. **Discuss mitigation** for fail-open risks
5. **Connect to business context** (bank vs social media)

---

## Tags
`resilience` `fail-open` `fail-closed` `rate-limiting` `system-design`
