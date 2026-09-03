# Non-Functional Requirements (NFRs) — Interview Questions

## Question 1: What are Non-Functional Requirements?

**Answer:**
Non-functional requirements define HOW the system should perform, not WHAT it should do.

| Type | Question it answers |
|------|---------------------|
| Functional | "What features does the system have?" |
| Non-Functional | "How fast? How reliable? How secure?" |

**Key NFRs:**
- Latency (response time)
- Throughput (requests per second)
- Availability (uptime)
- Consistency (data accuracy)
- Security (protection)
- Scalability (growth handling)

---

## Question 2: What latency targets would you set for a Subscription Service?

**Answer:**

| Operation Type | Target | Reasoning |
|----------------|--------|-----------|
| **Read APIs** (list plans, get subscription) | < 100ms | User expects instant response |
| **Write APIs** (subscribe, upgrade, cancel) | < 500ms | Involves DB writes, external calls (payment gateway) |

**Interview-ready explanation:**

*"For read operations like listing plans or viewing subscription details, I'd target under 100ms since these are simple DB reads and users expect instant response. For write operations like subscribing or upgrading, 500ms is acceptable because these involve database transactions, payment gateway calls, and potentially Kafka event publishing. Users understand that payment-related actions take slightly longer."*

---

## Question 3: What throughput would you design for?

**Answer:**

**Target: 15,000 requests per second**

**Breakdown:**
```
Peak hours assumption:
- 10M monthly active users
- 10% active during peak hour = 1M users
- Average 5 requests per session
- Peak hour = 3600 seconds

Calculation:
(1,000,000 × 5) / 3600 = ~1,400 RPS average
Peak multiplier (3-5x) = 4,200 - 7,000 RPS
Safety margin (2x) = 15,000 RPS target
```

**Interview-ready explanation:**

*"I'd design for 15K RPS which gives us headroom for traffic spikes. This accounts for peak hours, flash sales, and viral growth moments. We achieve this through horizontal scaling of stateless services, connection pooling for databases, Redis caching for frequently accessed data like plans, and read replicas for read-heavy operations."*

---

## Question 4: What availability target and why?

**Answer:**

**Target: 99.99% (Four nines)**

| Availability | Downtime/Year | Downtime/Month |
|--------------|---------------|----------------|
| 99.9% | 8.7 hours | 43 minutes |
| 99.99% | 52 minutes | 4.3 minutes |
| 99.999% | 5.2 minutes | 26 seconds |

**Why 99.99%:**
- Subscription service is **revenue-critical** — downtime = lost money
- Affects user signup flow — if subscription service down, new users can't onboard
- 99.999% requires Google-level infrastructure investment
- 99.99% is achievable with proper architecture (multi-AZ, failover, health checks)

**Interview-ready explanation:**

*"I'd target 99.99% availability which allows about 52 minutes of downtime per year. This is critical because our subscription service is in the signup path — if it's down, new users can't register and existing users can't upgrade. We achieve this through multi-AZ deployment, database failover, circuit breakers, and health check-based load balancing. Going to 99.999% would require significantly more infrastructure investment that may not be justified for our scale."*

---

## Question 5: Strong vs Eventual Consistency — When to use which?

**Answer:**

| Consistency | Meaning | Use When |
|-------------|---------|----------|
| **Strong** | Read always returns latest write | Money, access control, critical state |
| **Eventual** | Read may return stale data temporarily | Analytics, history, non-critical reads |

**Subscription Service breakdown:**

| Operation | Consistency | Why |
|-----------|-------------|-----|
| Create Subscription | STRONG | User paid → must see access immediately |
| Upgrade/Downgrade | STRONG | Payment done → new features must reflect now |
| Cancel Subscription | STRONG | Billing must stop immediately |
| Pause/Resume | STRONG | Access control change |
| List Plans | EVENTUAL OK | Plans rarely change, 1-2 sec delay fine |
| Subscription History | EVENTUAL OK | Historical data, slight lag acceptable |

**The Danger of Eventual Consistency:**
```
User upgrades to Premium → Payment successful
User clicks "Watch 4K" → Read hits stale replica
System says "You're on Basic" → BAD USER EXPERIENCE!
```

**Interview-ready explanation:**

*"For subscription service, I'd use strong consistency for all operations involving money or access control — subscribing, upgrading, cancelling. If a user pays for Premium, they must see Premium features immediately, not after replication lag. For read-only operations like listing available plans or viewing past subscription history, eventual consistency is acceptable since 1-2 seconds of staleness won't impact user experience or business logic."*

---

## Question 6: What security measures for a Subscription Service?

**Answer:**

| Asset | Protection Method |
|-------|-------------------|
| **Payment tokens** | Encrypted at rest, never logged, Stripe handles actual card |
| **API endpoints** | JWT authentication, role-based access (user vs admin) |
| **Admin APIs** | Separate admin role, audit logging |
| **User data** | HTTPS only, input validation, SQL injection prevention |
| **Subscription state** | Tamper-proof (user can't modify their own plan level) |

**Interview-ready explanation:**

*"Security is critical for subscription service since it handles payment information. First, we never store actual card numbers — only Stripe tokens, which are useless without Stripe's keys. All APIs require JWT authentication, with admin endpoints requiring elevated roles. Payment tokens are encrypted at rest and never appear in logs. We use HTTPS everywhere, validate all inputs, use parameterized queries to prevent SQL injection, and maintain audit logs for all subscription changes for compliance."*

---

## Question 7: How would you scale this service?

**Answer:**

**Horizontal Scaling Strategy:**

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    Service Pod 1   Service Pod 2   Service Pod 3
         │               │               │
         └───────────────┼───────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         Primary DB            Read Replicas
              │                     │
              └─────── Redis ───────┘
                     (Cache)
```

**Scaling Techniques:**

| Component | Scaling Method |
|-----------|----------------|
| **Service Pods** | Horizontal (add more instances) |
| **Database Reads** | Read replicas |
| **Database Writes** | Vertical first, then sharding by user_id |
| **Hot Data (Plans)** | Redis cache |
| **Async Operations** | Kafka for event processing |

**Interview-ready explanation:**

*"The service is stateless, so we scale horizontally by adding more pods behind a load balancer. For database, we use read replicas to handle read-heavy traffic like listing plans and checking subscriptions. For writes, we start with vertical scaling, then shard by user_id if needed. Frequently accessed data like plan details is cached in Redis with TTL. Heavy operations like sending welcome emails or syncing with analytics are offloaded to Kafka for async processing. This architecture can handle 15K+ RPS while maintaining low latency."*

---

## Question 8: What's the difference between Latency and Throughput?

**Answer:**

| Metric | Definition | Analogy |
|--------|------------|---------|
| **Latency** | Time for ONE request to complete | How long to deliver ONE pizza |
| **Throughput** | Requests handled per second | How many pizzas delivered per hour |

**They're related but different:**
- Low latency doesn't mean high throughput
- High throughput doesn't mean low latency

**Example:**
```
System A: 100ms latency, 100 RPS throughput
System B: 500ms latency, 1000 RPS throughput (parallel processing)
```

System B is slower per request but handles 10x more traffic!

**Interview-ready explanation:**

*"Latency is user-facing — how long does the user wait? Throughput is system-facing — how much load can we handle? We optimize both but they require different strategies. Latency is improved through caching, efficient queries, and reducing network hops. Throughput is improved through horizontal scaling, connection pooling, and async processing. A system can have low latency but poor throughput if it can only handle one request at a time, or high throughput with mediocre latency if it batches requests."*

---

## Follow-up Questions Interviewer Might Ask:

1. "How would you monitor these NFRs in production?"
2. "What happens when you exceed your throughput limit?"
3. "How do you test for 99.99% availability?"
4. "What's the cost trade-off between 99.99% and 99.999%?"
5. "How does your consistency model change with microservices?"
6. "What's your strategy for handling traffic spikes during sales?"

---

## Quick Reference Card:

```
┌─────────────────────────────────────────────────┐
│         SUBSCRIPTION SERVICE NFRs               │
├─────────────────────────────────────────────────┤
│ Latency:      Read < 100ms, Write < 500ms       │
│ Throughput:   15,000 RPS                        │
│ Availability: 99.99% (52 min downtime/year)     │
│ Consistency:  Strong for payments, eventual OK  │
│               for reads                         │
│ Security:     PCI compliant (tokenization),     │
│               JWT auth, encrypted tokens        │
│ Scalability:  Horizontal pods, read replicas,   │
│               Redis cache, Kafka async          │
└─────────────────────────────────────────────────┘
```
