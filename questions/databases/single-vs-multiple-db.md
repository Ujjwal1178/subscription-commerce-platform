# Single Database vs Database per Service

## Question
"In a microservices architecture, should each service have its own database or share a single database?"

---

## Answer

> "For true microservices, I recommend **database per service**. Here's why:
>
> **1. Independence** - If User service DB goes down, Payment service still works
>
> **2. Schema freedom** - Each team can modify their schema without affecting others
>
> **3. Right tool for the job** - Payment service might need PostgreSQL (ACID), Analytics might need MongoDB (flexible schema)
>
> **4. Scaling** - Can scale databases independently based on load
>
> **However, trade-offs exist:**
> - No direct JOINs across services
> - Data duplication may be needed
> - Consistency is harder to maintain
>
> For development, I'd use a single PostgreSQL instance with **separate databases inside** - logically isolated but resource efficient."

---

## Visual Comparison

```
SHARED DATABASE                    DATABASE PER SERVICE
┌─────────┐ ┌─────────┐ ┌────────┐    ┌─────────┐ ┌─────────┐ ┌────────┐
│  Auth   │ │  User   │ │Payment │    │  Auth   │ │  User   │ │Payment │
│ Service │ │ Service │ │Service │    │ Service │ │ Service │ │Service │
└────┬────┘ └────┬────┘ └───┬────┘    └────┬────┘ └────┬────┘ └───┬────┘
     │           │          │              │           │          │
     └───────────┼──────────┘              ▼           ▼          ▼
                 ▼                    ┌─────────┐ ┌─────────┐ ┌────────┐
          ┌──────────────┐            │ Auth DB │ │ User DB │ │Pay DB  │
          │   ONE DB     │            └─────────┘ └─────────┘ └────────┘
          │              │
          │ • users      │            ✅ True independence
          │ • payments   │            ✅ Scale separately
          │ • subs       │            ✅ Schema freedom
          └──────────────┘            ❌ No cross-service JOINs
                                      ❌ Data consistency harder
✅ Easy JOINs
✅ Simple setup
✅ Single backup
❌ Single point of failure
❌ Schema changes affect all
❌ Can't scale independently
```

---

## Follow-up Questions

### Q1: "If Payment service needs User's name, how do you get it without JOINs?"

**Answer**: API call to User service!

```
┌─────────────────┐                    ┌─────────────────┐
│ Payment Service │                    │  User Service   │
│                 │  GET /users/123    │                 │
│  Need user name │ ──────────────────▶│  Returns:       │
│  for invoice    │                    │  {name: "Ujjwal"}│
│                 │◀─────────────────  │                 │
└─────────────────┘                    └─────────────────┘
```

**Code example:**
```python
# In Payment Service
async def get_invoice(payment_id: str):
    payment = await db.get(Payment, payment_id)
    
    # Call User service
    user = await http_client.get(f"{USER_SERVICE_URL}/users/{payment.user_id}")
    
    return {
        "payment": payment,
        "user_name": user["name"],
        "user_email": user["email"]
    }
```

---

### Q2: "Isn't that slow? Multiple HTTP calls?"

**Answer**: Yes, it can be. Solutions:

1. **Caching** - Cache user details in Redis
   ```python
   user = await redis.get(f"user:{user_id}")
   if not user:
       user = await http_client.get(f"/users/{user_id}")
       await redis.setex(f"user:{user_id}", 300, user)  # 5 min TTL
   ```

2. **Data duplication** - Store user_name in Payment DB (denormalization)

3. **Batch APIs** - Get multiple users in one call
   ```
   GET /users/batch?ids=1,2,3,4,5
   ```

---

### Q3: "What if User service is down?"

**Answer**: Multiple strategies:

1. **Circuit Breaker** - Fail fast, don't wait
2. **Cached data** - Use stale data from Redis
3. **Fallback** - Return partial response (invoice without name)
4. **Retry with backoff** - For transient failures

```python
@circuit_breaker(failure_threshold=5, recovery_timeout=30)
async def get_user(user_id: str):
    # Try cache first
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return cached
    
    # Call service
    try:
        user = await http_client.get(f"/users/{user_id}")
        await redis.setex(f"user:{user_id}", 300, user)
        return user
    except ServiceUnavailable:
        # Fallback to stale cache or default
        return {"name": "Unknown User", "email": "N/A"}
```

---

### Q4: "How do you keep data consistent across databases?"

**Answer**: Event-driven updates!

```
User updates name "Ujjwal" → "Ujjwal Thakur"
         │
         ▼
┌─────────────────┐
│  User Service   │
│  1. Update DB   │
│  2. Publish     │
│     event       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     KAFKA       │
│                 │
│ Topic: user.updated
│ {id: 123,       │
│  name: "Ujjwal  │
│  Thakur"}       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Payment│ │Notif  │
│Service│ │Service│
│       │ │       │
│Update │ │Update │
│cache  │ │cache  │
└───────┘ └───────┘
```

This is called **Eventual Consistency** - data will be consistent "eventually" (usually milliseconds to seconds).

---

## Our Project Setup

```
Development Environment:
┌─────────────────────────────────────────────────────────┐
│              Single PostgreSQL Instance                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │   auth_db   │ │user_subs_db │ │ payment_db  │        │
│  │             │ │             │ │             │        │
│  │  • tokens   │ │  • users    │ │  • payments │        │
│  │             │ │  • subs     │ │  • jobs     │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
└─────────────────────────────────────────────────────────┘

Logically separate, physically one instance (resource efficient)
```

---

## Interview Tips

1. **Know both approaches** - Shared DB is valid for small teams
2. **Mention trade-offs** - No perfect solution exists
3. **Talk about solutions** - Caching, events, API calls
4. **Use real examples** - "At scale, Netflix uses DB per service"
