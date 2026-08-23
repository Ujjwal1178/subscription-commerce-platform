# Data Ownership in Microservices - Interview Questions

## Q1: How should data be shared between microservices?

**Answer:**

**Golden Rule:** Each piece of data has ONE owner service. Others access it via:

| Method | How | When to Use |
|--------|-----|-------------|
| **Sync (API)** | Service A calls Service B's API | Real-time data needed |
| **Async (Events)** | Service B publishes event, Service A listens | Eventual consistency OK |
| **Hybrid** | Critical via API, non-critical via events | Most common in production |

**Example:**
```
User Subscription Service needs user email to send notification:

Option 1 (API): GET /internal/users/{user_id} → Auth Service
Option 2 (Event): Listen to "user.created" event, cache locally
```

---

## Q2: Why not duplicate user table in every service?

**Answer:**

**Problems with duplication:**

| Problem | Impact |
|---------|--------|
| Data sync issues | User updates name → other services show old name |
| Inconsistency | Two services have different "truth" |
| Storage waste | Same data in 5 databases |
| Update complexity | Must propagate changes everywhere |

**Single Source of Truth principle:**
```
User data       → Auth Service owns
Subscription    → Subscription Service owns
Payment history → Payment Service owns
```

---

## Q3: What is eventual consistency? When is it acceptable?

**Answer:**

**Eventual consistency:** Data will be consistent across services... eventually (not immediately).

```
User updates profile in Auth Service
        ↓ (event published)
        ↓ (network delay: 100ms - 5s)
        ↓
Subscription Service receives event, updates cache
```

**Acceptable when:**
- Display-only data (user name shown in dashboard)
- Non-critical operations (analytics, recommendations)
- High-volume data (too expensive to sync real-time)

**NOT acceptable when:**
- Financial transactions
- Authentication/Authorization
- Inventory (e-commerce stock counts)

---

## Q4: How to handle service-to-service authentication?

**Answer:**

Internal APIs (service-to-service) need protection too!

**Options:**

| Method | How | Pros/Cons |
|--------|-----|-----------|
| **API Keys** | Each service has secret key | Simple, but key rotation hard |
| **mTLS** | Mutual TLS certificates | Secure, but complex setup |
| **Service Mesh** | Istio/Linkerd handles auth | Best for Kubernetes |
| **JWT with service identity** | Services have their own JWTs | Flexible, auditable |

**Our approach:** Internal network + API keys (simple for now, upgrade to mTLS in prod).

---

## Q5: What happens if Auth Service is down and Subscription Service needs user data?

**Answer:**

**Options:**

1. **Circuit Breaker:** Return cached/default data, don't crash
2. **Local Cache:** Subscription Service caches minimal user data
3. **Graceful Degradation:** Show "User" instead of actual name
4. **Retry with backoff:** Try again after 1s, 2s, 4s...

**Code example:**
```python
async def get_user_name(user_id: str) -> str:
    try:
        user = await auth_service.get_user(user_id)
        return user.name
    except ServiceUnavailable:
        # Fallback to cache or default
        cached = await redis.get(f"user:{user_id}:name")
        return cached or "User"
```

---

## Q6: Database per service vs Shared database?

**Answer:**

| Aspect | Database per Service | Shared Database |
|--------|---------------------|-----------------|
| Independence | ✅ Services evolve independently | ❌ Schema changes affect all |
| Scaling | ✅ Scale each DB based on load | ❌ Single bottleneck |
| Data integrity | ❌ No foreign keys across services | ✅ Referential integrity |
| Complexity | ❌ Need inter-service communication | ✅ Simple queries |
| Deployment | ✅ Deploy services independently | ❌ Tight coupling |

**Recommendation:** Database per service for true microservices.

---

## Q7: How to maintain referential integrity without foreign keys?

**Answer:**

In microservices, you CAN'T have foreign keys across databases.

**Solutions:**

1. **Application-level validation:**
```python
# Before creating subscription, verify user exists
user = await auth_service.get_user(user_id)
if not user:
    raise UserNotFoundError()
```

2. **Soft references with eventual cleanup:**
```python
# Store user_id, but don't enforce FK
# Background job cleans orphaned records
```

3. **Saga pattern for distributed transactions:**
```
Create subscription → Success
        ↓
Charge payment → Failed
        ↓
Rollback: Delete subscription (compensating action)
```

---

## Follow-up Questions:

1. "How do you handle distributed transactions across services?"
   → Saga pattern, eventual consistency, or avoid them

2. "What if you need to join data from multiple services?"
   → API composition, BFF (Backend for Frontend), or CQRS

3. "How do you debug issues spanning multiple services?"
   → Distributed tracing (Jaeger, Zipkin), correlation IDs

4. "When would you NOT use microservices?"
   → Small team, simple domain, early startup (start monolith, split later)
