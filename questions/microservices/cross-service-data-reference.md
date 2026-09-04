# Cross-Service Data Reference in Microservices

## Question 1: Why can't you use Foreign Key across microservices?

**Interviewer:** *"In your subscription service, you have user_id column. Why didn't you create a foreign key to the users table?"*

**Answer:**

*"In our microservices architecture, each service has its own database:*
- *Auth Service → auth_db → users table*
- *Subscription Service → subscription_db → user_subscriptions table*

*Foreign key constraints only work within the SAME database. PostgreSQL cannot enforce a FK constraint that references a table in a different database. If I tried to create `FOREIGN KEY (user_id) REFERENCES auth_db.users(user_id)`, it would fail.*

*So instead, I:*
1. *Store user_id as a regular UUID column*
2. *Add an INDEX for query performance*
3. *Validate user existence at application level before creating subscription"*

---

## Question 2: How do you ensure data consistency without FK?

**Interviewer:** *"Without FK constraint, what if someone creates a subscription for a user_id that doesn't exist?"*

**Answer:**

*"We handle this at the application level with multiple strategies:*

**1. API Validation:**
```python
# Before creating subscription
async def create_subscription(user_id: UUID, plan_id: UUID):
    # Call Auth Service to verify user exists
    user = await auth_service_client.get_user(user_id)
    if not user:
        raise UserNotFoundException()
    
    # Now create subscription
    subscription = UserSubscription(user_id=user_id, ...)
```

**2. Event-Driven Cleanup:**
*When a user is deleted in Auth Service, it publishes a `UserDeleted` event to Kafka. Subscription Service listens and handles cleanup:*
```python
# Kafka consumer
async def handle_user_deleted(event):
    user_id = event.user_id
    # Cancel all subscriptions for this user
    await subscription_service.cancel_all_for_user(user_id)
```

**3. Periodic Reconciliation:**
*Background job that checks for orphaned records and cleans them up.*"

---

## Question 3: What's the trade-off of not having FK?

**Interviewer:** *"What do you lose by not having FK constraints?"*

**Answer:**

| With FK | Without FK |
|---------|------------|
| Database enforces referential integrity | Application must enforce |
| CASCADE delete handled by DB | Must handle in code |
| Can't insert invalid user_id | Can insert invalid user_id |
| Coupled databases | Decoupled databases (microservice benefit) |
| Single point of failure | Services can fail independently |

*"The trade-off is: We lose automatic data integrity enforcement but gain service independence. A bug in Auth Service won't bring down Subscription Service. Each service can be deployed, scaled, and maintained independently."*

---

## Question 4: Why add INDEX on user_id?

**Interviewer:** *"You mentioned adding an index. Why is that important?"*

**Answer:**

*"Without FK, we also lose the implicit index that FK creates. So I explicitly add an index:*

```python
user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
```

**Without index:**
```sql
SELECT * FROM user_subscriptions WHERE user_id = 'xxx';
-- Full table scan: O(n) → SLOW with millions of rows
```

**With index:**
```sql
-- B-tree index lookup: O(log n) → FAST
```

*Common queries like 'get user's subscription' or 'get user's payment history' all filter by user_id. Without index, these become unacceptably slow at scale."*

---

## Question 5: How would you handle user deletion across services?

**Interviewer:** *"User deletes their account in Auth Service. How do you clean up data in Subscription Service?"*

**Answer:**

*"We use the Saga pattern with event-driven communication:*

```
User clicks "Delete Account"
         │
         ▼
    Auth Service
    ├── Soft-delete user (is_deleted = true)
    ├── Publish event: UserDeletionRequested
         │
         ▼
    Kafka Topic: user-events
         │
         ├──────────────────────────┐
         ▼                          ▼
Subscription Service         Payment Service
├── Cancel active subs       ├── Cancel pending payments
├── Expire downloads         ├── Process refunds if needed
├── Publish: SubsCleaned     ├── Publish: PaymentsCleaned
         │                          │
         └──────────────────────────┘
                    │
                    ▼
              Orchestrator
              (or Auth Service)
              ├── All cleanups confirmed?
              ├── Yes: Hard-delete user
              └── No: Alert, manual intervention
```

*This ensures all related data is cleaned up before the user is fully deleted, maintaining consistency across services."*

---

## Question 6: What if the event is lost?

**Interviewer:** *"What if the Kafka message is lost? User is deleted but subscription data remains."*

**Answer:**

*"Multiple safeguards:*

**1. Kafka guarantees:**
- Replication factor = 3 (message stored on 3 brokers)
- acks = all (producer waits for all replicas)
- Consumer commits offset only after processing

**2. Idempotent consumers:**
- Consumer can receive same message twice
- Processing is idempotent (delete already deleted = no-op)

**3. Dead Letter Queue:**
- Failed messages go to DLQ
- Alert on DLQ growth
- Manual review and replay

**4. Periodic reconciliation job:**
```python
# Daily job
async def reconcile_orphaned_subscriptions():
    subscription_user_ids = await get_all_subscription_user_ids()
    for user_id in subscription_user_ids:
        user_exists = await auth_service.user_exists(user_id)
        if not user_exists:
            await cleanup_orphaned_subscription(user_id)
            alert_team(f"Orphaned subscription found for {user_id}")
```

*Belt and suspenders approach — multiple layers of protection."*

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│         CROSS-SERVICE DATA REFERENCE CHECKLIST                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. No FK across databases — use regular column + INDEX          │
│ 2. Validate at application level (API call to owning service)   │
│ 3. Event-driven sync (Kafka) for deletions/updates              │
│ 4. Idempotent event handlers                                    │
│ 5. Dead Letter Queue for failed events                          │
│ 6. Periodic reconciliation job as safety net                    │
│ 7. Soft delete first, hard delete after all services confirm    │
└─────────────────────────────────────────────────────────────────┘
```
