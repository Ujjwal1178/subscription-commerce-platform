# Session Summary 2 - Notification Worker & Beyond

> **Previous File:** `SESSION-SUMMARY.md` (Parts 1-11, Auth Service)
> **This File:** Parts 12+ (Notification Worker, Subscription Service, etc.)

---

# PART 12: Auth Service Complete + Code Cleanup
## Session Date: 27 August 2026 (Wednesday)

### Auth Service v1.0 - DONE ✅

**10 APIs Complete:**
```
POST /api/v1/auth/register
POST /api/v1/auth/verify-otp
POST /api/v1/auth/login
POST /api/v1/auth/resend-otp
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/forgot-password
POST /api/v1/auth/verify-reset-otp
POST /api/v1/auth/reset-password
GET  /api/v1/auth/me
```

**Code Cleanup:**
- Removed verbose comments (~60% reduction)
- 19 files changed, 384 insertions, 1881 deletions

**Git Commit:** `524f574`

---

# PART 13: Notification Architecture Planning
## Session Date: 27 August 2026 (Wednesday)

### Problem:
OTP generated but not sent via email - only logged in dev mode.

### Architecture Decided:

```
Auth Service → Kafka → Notification Worker → AWS SES → User Inbox
```

### Why Kafka (not direct SES)?
- User doesn't wait for email
- Retry if SES fails (message stays in Kafka)
- Scale workers independently
- Buffer when downstream is slow

### Scaling Strategy:

```
Kafka Topic: notification_events (3 partitions)
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
Worker 1        Worker 2        Worker 3
(5 threads)     (5 threads)     (5 threads)
    │               │               │
    └───────────────┼───────────────┘
                    ▼
                AWS SES (single service)
```

### Key Concepts Learned:

| Concept | Explanation |
|---------|-------------|
| Partition ≠ Container | Partitions are inside Kafka (logical) |
| Max consumers = Partitions | 3 partitions → max 3 consumers |
| Pod = Container | Kubernetes terminology |
| Horizontal scaling | More partitions + more workers |
| Vertical scaling | More threads per worker |

**Netflix Scale:**
- 100+ partitions, 100+ workers
- Multi-provider (SES + SendGrid + Mailgun)
- Each worker has thread pool

**Our Scale:**
- 3 partitions, scalable to 3 workers
- 5 threads per worker
- 15 concurrent SES calls possible

### What We'll Build:

```
backend/services/notification_worker/
├── app/
│   ├── main.py           # Kafka consumer loop
│   ├── config.py         # SES, Kafka config
│   ├── email_sender.py   # SES integration
│   └── handlers/
│       └── otp_handler.py
├── Dockerfile
└── requirements.txt
```

### Rules Updated (Steering File):
- No `git add .` - stage specific files
- Multiple small commits > one big commit

### What's Next:
- [ ] AWS SES setup
- [ ] Notification Worker service
- [ ] Kafka producer in Auth Service
- [ ] End-to-end email test

---

# PART 14: Subscription Service - HLD & Database Design
## Session Date: 31 August 2026 (Monday)

### What We Did:
Interview-style HLD discussion for Subscription Service

### Functional Requirements Discussed:
- Plan management (Free, Basic, Premium, Family)
- User subscription lifecycle (subscribe, upgrade, downgrade, pause, cancel)
- Flexible pricing (monthly, yearly, one-time, recurring)
- Auto-renewal and billing cycle handling
- Default subscription on signup (Free tier)

### Non-Functional Requirements:
| Requirement | Target |
|-------------|--------|
| Latency | < 100ms (reads), < 500ms (writes with payment) |
| Throughput | 15K RPS |
| Availability | 99.99% (revenue-critical) |
| Consistency | Strong for payments |

### Database Tables Designed:

```
1. plans              - Plan definitions (Basic, Premium, Family)
2. plan_prices        - Flexible pricing per billing cycle
3. payment_methods    - Tokenized cards/UPI (PCI compliant)
4. user_subscriptions - User's active subscription with locked price
5. payment_transactions - Complete payment history
```

### Key Concepts Learned:

| Topic | Learning |
|-------|----------|
| Price Locking | User's price saved at subscription time, doesn't change |
| Tokenization | Never store card numbers, use Stripe/Razorpay tokens |
| PCI DSS | Payment security standard, Stripe handles compliance |
| is_recurring | Auto-renew after period ends? |
| duration_months | Commitment length (1 for monthly, 12 for yearly) |
| current_period_start/end | Billing period for access control |
| next_billing_date | When payment worker should charge |
| Idempotency Key | Prevent duplicate charges on retry |

### Pricing Model Clarity:
| billing_cycle | duration | amount | is_recurring | Meaning |
|---------------|----------|--------|--------------|---------|
| monthly | 1 | 100 | false | One-time 1 month, expires |
| monthly | 1 | 100 | true | Monthly subscription, auto-renews |
| yearly | 12 | 1100 | false | Yearly one-time full payment |
| yearly | 12 | 100 | true | Yearly commitment, monthly payments |

### Files Created:
- `docs/subscription-service-db-design.md` - Full DB schema with ER diagram
- `questions/payments/pci-dss-tokenization.md` - 7 interview questions

### Interview Questions Documented:
1. Why not store card details directly?
2. How does tokenization work?
3. Why is PCI compliance not a problem for Stripe?
4. What is PCI DSS exactly?
5. What to store in payment_methods table?
6. Update vs Create new payment method?
7. Multiple subscriptions with different payment methods?

### What's Next:
- [x] Create Subscription Service folder structure
- [ ] Write Alembic migrations for tables
- [ ] Implement Plans CRUD APIs
- [ ] Implement Subscription APIs
- [ ] Stripe integration for payments

---

# PART 15: Subscription Service Setup + Interview Prep
## Session Date: 3 September 2026 (Thursday)

### What We Did:

**1. Comprehensive Interview Prep Materials Created:**
- SQL Interview Questions (23 topics)
- Python OOPs Deep Dive (20 topics)
- Apple HLD Questions (15 systems)
- LLD Machine Coding (10+ problems)
- NFRs Interview Guide (8 questions)
- Apple Music System Design Deep Dive (complete 45-min interview script)

**2. Subscription Service Implementation Started:**
- Folder structure created
- Config with Stripe settings
- Dependencies (DB session, auth)
- 5 SQLAlchemy models created

### Folder Structure Created:
```
backend/services/subscription_service/
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── dependencies.py
│   ├── api/
│   ├── models/
│   │   ├── plan.py
│   │   ├── plan_price.py
│   │   ├── payment_method.py
│   │   ├── user_subscription.py
│   │   └── payment_transaction.py
│   ├── schemas/
│   ├── services/
│   └── migrations/
```

### Key Concepts Learned:

| Topic | Learning |
|-------|----------|
| Cross-DB FK | Can't have FK across microservice databases |
| Index without FK | Must add explicit INDEX on user_id for performance |
| get_current_user_optional | For public APIs (GET /plans doesn't need auth) |
| Soft Delete | payment_methods has is_deleted flag |
| Scheduled Changes | scheduled_plan_id for downgrades at period end |

### Interview Questions Documented Today:

**SQL (23 questions):**
- JOINs, Subqueries, CTEs, Window Functions
- Normalization (1NF, 2NF, 3NF)
- Indexes (B-tree, when to use)
- ACID, Isolation Levels
- Query Optimization (EXPLAIN)
- Practical problems (2nd highest salary, duplicates)

**Python OOPs (20 questions):**
- 4 Pillars with examples
- Magic methods (__init__, __str__, __eq__, __call__)
- @property, @classmethod, @staticmethod
- Descriptors, Metaclasses
- SOLID Principles

**HLD (15 systems):**
- Apple Music, iCloud, Push Notifications
- URL Shortener, Rate Limiter
- Chat System, Video Streaming
- E-commerce, Ride-sharing

**LLD (10+ problems):**
- Parking Lot, BookMyShow, Splitwise
- Elevator, LRU Cache, Rate Limiter
- Design Patterns (Singleton, Factory, Strategy)

**Microservices:**
- Cross-service data reference
- Why no FK across services
- Event-driven cleanup (Kafka)
- Saga pattern for deletions

### Files Created:
```
questions/
├── databases/
│   └── sql-interview-questions.md
├── python/
│   └── oops-interview-questions.md
├── microservices/
│   └── cross-service-data-reference.md
└── system-design/
    ├── apple-hld-questions.md
    ├── lld-machine-coding-questions.md
    ├── non-functional-requirements.md
    └── deep-dive/
        └── 01-apple-music-streaming.md

docs/
└── subscription-service-api-design.md

backend/services/subscription_service/
└── (folder structure + models)
```

### Git Commits:
```
0f55761 feat(subscription): Add folder structure, config, dependencies, models
beec9ed docs(questions): Add comprehensive interview prep materials
282c8bc docs(subscription): Add API design document with 22 endpoints
```

### What's Next:
- [ ] Alembic setup for Subscription Service
- [ ] Create migration for 5 tables
- [ ] Pydantic schemas
- [ ] Plans CRUD APIs (first 5 endpoints)
- [ ] One HLD deep dive daily (Rate Limiter next)

---

<!-- Template for future parts

# PART XX: [Title]
## Session Date: [Date]

### What We Did:
- 

### Key Concepts:
- 

### Files Modified:
- 

### What's Next:
- 

-->
