# Monolith vs Microservices

## Question
"You're designing a subscription platform for Apple. Would you use monolith or microservices architecture? Why?"

---

## Answer

> "Great question! I would go with **microservices** for a subscription platform, and here's my reasoning:
>
> **1. Fault Isolation** - If my payment service goes down, users should still be able to browse plans, login, and use other features. In a monolith, one crashed module can bring down the entire system.
>
> **2. Independent Scaling** - Payment processing might need 10 instances during Black Friday sales, but User service might only need 2. With microservices, I can scale each service based on its load. In a monolith, I'd have to scale everything together - wasteful and expensive.
>
> **3. Team Autonomy** - Different teams can own different services, deploy independently, and even use different tech stacks if needed.
>
> **However, microservices come with trade-offs:**
> - Network latency between services
> - Distributed transactions are complex
> - Operational complexity - more services to monitor, deploy, debug
>
> For a subscription platform where reliability and independent scaling are critical, I believe the benefits outweigh the complexity."

---

## Follow-up Questions

### Q1: "Should every project start with microservices?"

**Answer**: No! 

| Scenario | Recommendation |
|----------|----------------|
| Small team (< 5 developers) | Monolith |
| New product, unclear requirements | Monolith |
| Speed of development matters | Monolith |
| Large team (10+ developers) | Microservices |
| Clear domain boundaries | Microservices |
| Different parts need different scaling | Microservices |
| High availability is critical | Microservices |

**Key Point**: Amazon, Netflix, Uber - all started as monoliths and migrated to microservices when scale demanded it.

---

### Q2: "What are the challenges of microservices?"

**Answer**:
1. **Network latency** - Service-to-service calls add latency
2. **Distributed transactions** - What if payment succeeds but subscription creation fails?
3. **Data consistency** - Each service has its own DB, keeping data in sync is hard
4. **Operational overhead** - More services = more deployments, monitoring, debugging
5. **Testing complexity** - Integration tests become harder

---

### Q3: "How do you handle a distributed transaction?"

**Answer**: Multiple approaches:

1. **Saga Pattern** - Break transaction into steps, each with compensating action
   ```
   Step 1: Create subscription → Compensate: Delete subscription
   Step 2: Charge payment → Compensate: Refund payment
   Step 3: Send email → Compensate: Send apology email
   ```

2. **Two-Phase Commit (2PC)** - All services vote, then commit (rarely used - too slow)

3. **Eventual Consistency** - Accept that data will be consistent "eventually" via events

---

## Visual Comparison

```
MONOLITH                           MICROSERVICES
┌─────────────────────┐           ┌───────┐ ┌───────┐ ┌───────┐
│                     │           │ Auth  │ │ User  │ │Payment│
│   ALL CODE HERE     │           │Service│ │Service│ │Service│
│                     │           └───┬───┘ └───┬───┘ └───┬───┘
│  Users + Payments   │               │         │         │
│  + Subscriptions    │               ▼         ▼         ▼
│  + Notifications    │           ┌───────┐ ┌───────┐ ┌───────┐
│                     │           │  DB   │ │  DB   │ │  DB   │
└──────────┬──────────┘           └───────┘ └───────┘ └───────┘
           │
           ▼                      ✅ Independent scaling
    ┌──────────┐                  ✅ Fault isolation
    │ ONE DB   │                  ✅ Team autonomy
    └──────────┘                  ❌ Network complexity
                                  ❌ Distributed transactions
✅ Simple                         ❌ Operational overhead
✅ Easy debugging
✅ No network latency
❌ Single point of failure
❌ Scale everything together
```

---

## Interview Tips

1. **Always mention trade-offs** - Interviewers love balanced thinking
2. **Give real examples** - "Netflix started as monolith..."
3. **Ask clarifying questions** - "How big is the team? What's the expected scale?"
4. **Don't be dogmatic** - "It depends on the context"
