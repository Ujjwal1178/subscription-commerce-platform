# Circuit Breaker Pattern

## Question
"What happens if a downstream service (like Payment Gateway) goes down? How do you prevent cascading failures?"

---

## Answer

> "I'd implement a **Circuit Breaker pattern**. It's like an electrical circuit breaker - when too many failures occur, it 'trips' and stops making calls to the failing service.
>
> This prevents:
> - Wasting resources on doomed requests
> - Cascading failures (one service down → all services down)
> - Slow response times from timeouts
>
> The circuit has three states: CLOSED (normal), OPEN (blocking), and HALF-OPEN (testing)."

---

## The Problem: Cascading Failures

```
┌─────────────────────────────────────────────────────────────────────┐
│                  WITHOUT CIRCUIT BREAKER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Stripe is DOWN 💀                                                 │
│                                                                     │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐                    │
│   │  Client  │────▶│ Payment  │────▶│  Stripe  │ ❌ Timeout (30s)   │
│   │          │     │ Service  │     │   API    │                    │
│   └──────────┘     └──────────┘     └──────────┘                    │
│                         │                                           │
│                         ▼                                           │
│   100 users trying to pay...                                        │
│   Each waits 30 seconds for timeout                                 │
│                                                                     │
│   Result:                                                           │
│   • 100 threads blocked                                             │
│   • Payment service becomes unresponsive                            │
│   • Users see spinning loader                                       │
│   • Other services depending on Payment also slow down              │
│   • ENTIRE SYSTEM CRAWLS 💀                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Solution: Circuit Breaker

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                         CLOSED                              │   │
│   │                        (Normal)                             │   │
│   │                                                             │   │
│   │   Requests flow through normally                            │   │
│   │   Failures are counted                                      │   │
│   └────────────────────────┬────────────────────────────────────┘   │
│                            │                                        │
│                            │ 5 consecutive failures                 │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                          OPEN                               │   │
│   │                      (Fail Fast)                            │   │
│   │                                                             │   │
│   │   All requests IMMEDIATELY fail                             │   │
│   │   No calls to downstream service                            │   │
│   │   Returns fallback or error                                 │   │
│   └────────────────────────┬────────────────────────────────────┘   │
│                            │                                        │
│                            │ After 30 seconds (recovery timeout)    │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                       HALF-OPEN                             │   │
│   │                     (Testing)                               │   │
│   │                                                             │   │
│   │   Allow ONE request through                                 │   │
│   │   If SUCCESS → go to CLOSED                                 │   │
│   │   If FAILURE → go back to OPEN                              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## With Circuit Breaker

```
┌─────────────────────────────────────────────────────────────────────┐
│                   WITH CIRCUIT BREAKER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Stripe goes DOWN                                                  │
│                                                                     │
│   Request 1: Try → Fail (count: 1)                                  │
│   Request 2: Try → Fail (count: 2)                                  │
│   Request 3: Try → Fail (count: 3)                                  │
│   Request 4: Try → Fail (count: 4)                                  │
│   Request 5: Try → Fail (count: 5) 🔴 CIRCUIT OPENS!                │
│                                                                     │
│   Request 6-100: INSTANT FAILURE (no network call)                  │
│   "Payment service temporarily unavailable, try again later"        │
│                                                                     │
│   ... 30 seconds pass ...                                           │
│                                                                     │
│   🟡 HALF-OPEN: Let one request through                             │
│   Request 101: Try → Fail → Back to OPEN                            │
│                                                                     │
│   ... 30 more seconds ...                                           │
│                                                                     │
│   🟡 HALF-OPEN: Let one request through                             │
│   Request 102: Try → SUCCESS! 🟢 CIRCUIT CLOSES                     │
│                                                                     │
│   Normal operation resumes                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Code Implementation

```python
import time
from enum import Enum
from functools import wraps

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exceptions: tuple = (Exception,)
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_try_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpen("Circuit is OPEN, failing fast")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise
    
    def _should_try_reset(self) -> bool:
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


# Usage as decorator
def circuit_breaker(failure_threshold=5, recovery_timeout=30):
    cb = CircuitBreaker(failure_threshold, recovery_timeout)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Example usage
@circuit_breaker(failure_threshold=5, recovery_timeout=30)
async def charge_payment(amount: int, card_token: str):
    response = await stripe_client.charges.create(
        amount=amount,
        currency="usd",
        source=card_token
    )
    return response
```

---

## Follow-up Questions

### Q1: "What do you return when circuit is OPEN?"

**Answer**: Depends on the use case!

| Strategy | When to Use | Example |
|----------|-------------|---------|
| **Throw exception** | Caller should handle | `raise ServiceUnavailable()` |
| **Return cached data** | Stale data is acceptable | Return last successful response |
| **Return default** | Graceful degradation | `{"status": "unknown"}` |
| **Queue for retry** | Can process later | Add to retry queue |

```python
@circuit_breaker(failure_threshold=5, recovery_timeout=30)
async def get_user_with_fallback(user_id: str):
    try:
        return await user_service.get(user_id)
    except CircuitBreakerOpen:
        # Fallback 1: Try cache
        cached = await redis.get(f"user:{user_id}")
        if cached:
            return json.loads(cached)
        
        # Fallback 2: Return default
        return {"id": user_id, "name": "Unknown", "status": "unavailable"}
```

---

### Q2: "How is this different from retry?"

**Answer**: They complement each other!

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RETRY vs CIRCUIT BREAKER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   RETRY:                                                            │
│   • For TRANSIENT failures (network blip, temporary issue)          │
│   • Try again, maybe it'll work                                     │
│   • Good for: Occasional failures                                   │
│                                                                     │
│   CIRCUIT BREAKER:                                                  │
│   • For PERSISTENT failures (service is DOWN)                       │
│   • Stop trying, it's not going to work                             │
│   • Good for: Service outages                                       │
│                                                                     │
│   COMBINED (Best approach):                                         │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │   Request                                                   │   │
│   │      │                                                      │   │
│   │      ▼                                                      │   │
│   │   Circuit Breaker (Is service healthy?)                     │   │
│   │      │                                                      │   │
│   │      │ If CLOSED                                            │   │
│   │      ▼                                                      │   │
│   │   Retry Logic (Try 3 times with backoff)                    │   │
│   │      │                                                      │   │
│   │      │ All retries failed                                   │   │
│   │      ▼                                                      │   │
│   │   Circuit Breaker records failure                           │   │
│   │      │                                                      │   │
│   │      │ 5 failures                                           │   │
│   │      ▼                                                      │   │
│   │   Circuit OPENS (fast fail for future requests)             │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Q3: "What library would you use in production?"

**Answer**:

| Language | Library |
|----------|---------|
| Python | `circuitbreaker`, `pybreaker`, `tenacity` |
| Java | Resilience4j, Hystrix (deprecated) |
| Go | `sony/gobreaker` |
| Node.js | `opossum` |

```python
# Using 'circuitbreaker' library
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def call_stripe(amount: int):
    return await stripe.charges.create(amount=amount)
```

---

### Q4: "How do you monitor circuit breaker state?"

**Answer**: Metrics and alerts!

```python
# Emit metrics
async def charge_payment(amount: int):
    try:
        result = await stripe_call(amount)
        metrics.increment("payment.success")
        return result
    except CircuitBreakerOpen:
        metrics.increment("payment.circuit_open")
        alert("Payment circuit breaker is OPEN!")
        raise
    except PaymentError:
        metrics.increment("payment.failure")
        raise

# Prometheus metrics example
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'State of circuit breaker (0=closed, 1=open, 2=half_open)',
    ['service']
)
```

**Dashboard shows:**
- Circuit state over time
- Failure rate
- Recovery attempts
- Time spent in OPEN state

---

## Real World Usage

| Company | Circuit Breaker Usage |
|---------|----------------------|
| Netflix | Hystrix (now Resilience4j) |
| Amazon | Custom implementation |
| Uber | Custom with extensive monitoring |
| Apple | Used in all microservices |

---

## Interview Tips

1. **Draw the state diagram** - CLOSED → OPEN → HALF-OPEN
2. **Explain WHY** - Prevent cascading failures
3. **Mention fallbacks** - What happens when circuit opens?
4. **Combine with retry** - They work together
5. **Talk about monitoring** - How do you know circuit is open?
