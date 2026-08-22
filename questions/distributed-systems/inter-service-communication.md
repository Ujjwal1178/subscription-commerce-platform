# Inter-Service Communication

## Question
"In microservices, if Payment service needs User details but they're in different databases, how do you handle it?"

---

## Answer

> "I'd use **synchronous API calls** for real-time data needs. Payment service would call User service's API to get user details.
>
> This creates a dependency, so I'd add:
> - **Caching** in Redis to reduce calls
> - **Circuit Breaker** to handle User service failures
> - **Fallback strategies** for graceful degradation"

---

## Communication Patterns

```
┌─────────────────────────────────────────────────────────────────────┐
│                 INTER-SERVICE COMMUNICATION                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. SYNCHRONOUS (HTTP/REST)                                         │
│     Request → Wait → Response                                       │
│     Use for: Real-time data needs                                   │
│                                                                     │
│     ┌──────────┐     GET /users/123      ┌──────────┐               │
│     │ Payment  │ ───────────────────────▶│  User    │               │
│     │ Service  │                         │ Service  │               │
│     │          │◀─────────────────────── │          │               │
│     └──────────┘    {name: "Ujjwal"}     └──────────┘               │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  2. ASYNCHRONOUS (Kafka/Events)                                     │
│     Fire and forget, process later                                  │
│     Use for: Non-critical, can be delayed                           │
│                                                                     │
│     ┌──────────┐    payment.success      ┌──────────┐               │
│     │ Payment  │ ───────────────────────▶│  KAFKA   │               │
│     │ Service  │     (publish)           │          │               │
│     └──────────┘                         └────┬─────┘               │
│                                               │                     │
│                              ┌────────────────┼────────────────┐    │
│                              ▼                ▼                ▼    │
│                         ┌────────┐      ┌────────┐      ┌────────┐  │
│                         │Notif   │      │Analytics│     │Audit   │  │
│                         │Service │      │Service │      │Service │  │
│                         └────────┘      └────────┘      └────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Flow: Payment Service Needs User Details

```
┌─────────────────────────────────────────────────────────────────────┐
│          PAYMENT SERVICE GETTING USER DETAILS                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Client: "GET /payments/456/invoice"                               │
│                                                                     │
│   ┌─────────────────┐                                               │
│   │ Payment Service │                                               │
│   │                 │                                               │
│   │  1. Get payment │                                               │
│   │     from DB     │                                               │
│   │     user_id:123 │                                               │
│   │                 │                                               │
│   │  2. Check Redis │     Cache miss!                               │
│   │     cache ──────┼──────────────────┐                            │
│   │                 │                  │                            │
│   │  3. Call User   │                  ▼                            │
│   │     Service ────┼─────────▶ ┌─────────────────┐                 │
│   │                 │           │  User Service   │                 │
│   │                 │           │                 │                 │
│   │                 │           │  GET /users/123 │                 │
│   │                 │           │                 │                 │
│   │                 │◀───────── │  {name:"Ujjwal",│                 │
│   │                 │           │   email:"..."}  │                 │
│   │                 │           └─────────────────┘                 │
│   │  4. Cache in    │                                               │
│   │     Redis       │                                               │
│   │                 │                                               │
│   │  5. Return      │                                               │
│   │     combined    │                                               │
│   │     response    │                                               │
│   └─────────────────┘                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Follow-up Questions

### Q1: "What if User service is down?"

**Answer**: Implement resilience patterns!

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RESILIENCE STRATEGIES                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. CIRCUIT BREAKER                                                 │
│     ┌──────────┐         5 failures        ┌──────────┐             │
│     │  CLOSED  │ ────────────────────────▶ │   OPEN   │             │
│     │ (Normal) │                           │(Fail Fast)│            │
│     └──────────┘                           └────┬─────┘             │
│          ▲                                      │                   │
│          │ Success                After 30s     │                   │
│          │                              ┌───────┘                   │
│          │                              ▼                           │
│          │                       ┌────────────┐                     │
│          └────────────────────── │ HALF-OPEN  │                     │
│                                  │(Test 1 req)│                     │
│                                  └────────────┘                     │
│                                                                     │
│  2. FALLBACK OPTIONS                                                │
│     • Return cached data (even if stale)                            │
│     • Return partial response (invoice without name)                │
│     • Return default values                                         │
│                                                                     │
│  3. RETRY WITH BACKOFF                                              │
│     Attempt 1 → fail → wait 1s                                      │
│     Attempt 2 → fail → wait 2s                                      │
│     Attempt 3 → fail → wait 4s                                      │
│     Give up → use fallback                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Code example:**
```python
@circuit_breaker(failure_threshold=5, recovery_timeout=30)
async def get_user(user_id: str) -> dict:
    # 1. Try cache first
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # 2. Call User service
    try:
        response = await http_client.get(
            f"{USER_SERVICE_URL}/users/{user_id}",
            timeout=5.0
        )
        user = response.json()
        
        # 3. Cache for future
        await redis.setex(f"user:{user_id}", 300, json.dumps(user))
        return user
        
    except (Timeout, ConnectionError) as e:
        # 4. Fallback - try stale cache
        stale = await redis.get(f"user:{user_id}:stale")
        if stale:
            return json.loads(stale)
        
        # 5. Last resort - default values
        return {"name": "Unknown", "email": "N/A"}
```

---

### Q2: "Isn't this slow with multiple HTTP calls?"

**Answer**: Yes! Here are optimizations:

| Strategy | How | Trade-off |
|----------|-----|-----------|
| **Caching** | Store user in Redis (5 min TTL) | Stale data possible |
| **Batch APIs** | `GET /users?ids=1,2,3` | API design complexity |
| **Denormalization** | Store user_name in Payment DB | Data duplication |
| **Parallel calls** | `asyncio.gather()` | Still network overhead |

```python
# Parallel calls - faster than sequential
async def get_invoice_data(payment_id: str):
    payment = await get_payment(payment_id)
    
    # Fetch in parallel
    user_task = get_user(payment.user_id)
    subscription_task = get_subscription(payment.subscription_id)
    
    user, subscription = await asyncio.gather(user_task, subscription_task)
    
    return {
        "payment": payment,
        "user": user,
        "subscription": subscription
    }
```

---

### Q3: "How do you keep data consistent when User updates their name?"

**Answer**: Event-driven cache invalidation!

```
┌─────────────────────────────────────────────────────────────────────┐
│              EVENT-DRIVEN CACHE INVALIDATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   User updates name: "Ujjwal" → "Ujjwal Thakur"                     │
│                                                                     │
│   ┌─────────────────┐                                               │
│   │  User Service   │                                               │
│   │                 │                                               │
│   │  1. Update DB   │                                               │
│   │  2. Publish     │                                               │
│   │     event       │                                               │
│   └────────┬────────┘                                               │
│            │                                                        │
│            ▼                                                        │
│   ┌─────────────────┐                                               │
│   │     KAFKA       │                                               │
│   │                 │                                               │
│   │ Topic: user.updated                                             │
│   │ {                                                               │
│   │   user_id: 123,                                                 │
│   │   name: "Ujjwal Thakur"                                         │
│   │ }                                                               │
│   └────────┬────────┘                                               │
│            │                                                        │
│       ┌────┴────┐                                                   │
│       ▼         ▼                                                   │
│   ┌───────┐ ┌───────┐                                               │
│   │Payment│ │Notif  │                                               │
│   │Service│ │Service│                                               │
│   │       │ │       │                                               │
│   │Delete │ │Delete │                                               │
│   │cache  │ │cache  │                                               │
│   └───────┘ └───────┘                                               │
│                                                                     │
│   Next request → Cache miss → Fresh data fetched                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Q4: "When to use sync (HTTP) vs async (Kafka)?"

**Answer**:

| Use Case | Pattern | Why |
|----------|---------|-----|
| Need data immediately | **Sync (HTTP)** | Can't proceed without it |
| User expects response | **Sync (HTTP)** | Real-time feedback |
| Can be processed later | **Async (Kafka)** | Decouple, resilience |
| Multiple consumers | **Async (Kafka)** | Fan-out pattern |
| Audit/logging | **Async (Kafka)** | Don't slow main flow |

**Examples:**
```
Sync (HTTP):
- Get user details for invoice ✅
- Verify payment status ✅
- Check subscription validity ✅

Async (Kafka):
- Send welcome email ✅
- Update analytics ✅
- Sync to third-party systems ✅
- Audit logging ✅
```

---

## Interview Tips

1. **Show you understand trade-offs** - Sync is simpler but creates coupling
2. **Mention resilience** - Circuit breaker, caching, fallbacks
3. **Discuss consistency** - Eventual consistency with events
4. **Know when to use what** - Sync for critical path, async for side effects
