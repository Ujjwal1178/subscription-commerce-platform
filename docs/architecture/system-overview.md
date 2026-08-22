# System Architecture Overview

## Subscription Commerce Platform

A production-grade, Apple-like subscription and commerce platform designed to scale toward 1M+ requests/sec while remaining highly available, fault-tolerant, and resilient.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENTS                                   │
│                        (Web App / Mobile App / API)                         │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                    │
│                                                                             │
│  • Single Entry Point        • JWT Verification      • Rate Limiting        │
│  • Request Routing           • Load Balancing        • Logging/Monitoring   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
┌───────────────────┐   ┌───────────────────────┐   ┌───────────────────┐
│   AUTH SERVICE    │   │ USER-SUBSCRIPTION SVC │   │  PAYMENT SERVICE  │
│                   │   │                       │   │                   │
│ • Registration    │   │ • User CRUD           │   │ • Process Payment │
│ • Login/Logout    │   │ • Profile Management  │   │ • Refunds         │
│ • JWT Generation  │   │ • Subscription CRUD   │   │ • Idempotency     │
│ • Token Refresh   │   │ • Plan Management     │   │ • Stripe Integration
│ • Password Reset  │   │ • Default Subscription│   │                   │
└────────┬──────────┘   └───────────┬───────────┘   └─────────┬─────────┘
         │                          │                         │
         ▼                          ▼                         ▼
┌───────────────────┐   ┌───────────────────────┐   ┌───────────────────┐
│     AUTH_DB       │   │    USER_SUBS_DB       │   │    PAYMENT_DB     │
│   (PostgreSQL)    │   │    (PostgreSQL)       │   │   (PostgreSQL)    │
│                   │   │                       │   │                   │
│ • tokens          │   │ • users               │   │ • payments        │
│ • refresh_tokens  │   │ • subscriptions       │   │ • refunds         │
│ • password_resets │   │ • plans               │   │ • jobs            │
└───────────────────┘   └───────────────────────┘   └───────────────────┘


                    BACKGROUND WORKERS & ASYNC PROCESSING
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌─────────────────────┐                    ┌────────────────────────┐     │
│   │  PAYMENT SCHEDULER  │                    │  NOTIFICATION SERVICE  │     │
│   │                     │                    │                        │     │
│   │ • Scan due payments │      KAFKA         │ • Email notifications  │     │
│   │ • Create jobs       │ ──────────────────▶│ • SMS notifications    │     │
│   │ • Process recurring │                    │ • Push notifications   │     │
│   │ • Retry failed      │                    │                        │     │
│   └─────────────────────┘                    └────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘


                              SHARED INFRASTRUCTURE
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                            REDIS                                    │   │
│   │                                                                     │   │
│   │  • Caching (User profiles, Plans)                                   │   │
│   │  • Rate Limiting (Token Bucket)                                     │   │
│   │  • Distributed Locks (Job processing)                               │   │
│   │  • Session Storage                                                  │   │
│   │  • Idempotency Keys                                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                           KAFKA                                     │   │
│   │                                                                     │   │
│   │  Topics:                                                            │   │
│   │  • subscription.created    • payment.success                        │   │
│   │  • subscription.cancelled  • payment.failed                         │   │
│   │  • user.registered         • notification.email                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Services Overview

| Service | Type | Port | Database | Responsibility |
|---------|------|------|----------|----------------|
| api-gateway | API | 8000 | None | Routing, Auth verify, Rate limiting |
| auth-service | API | 8001 | auth_db | Login, Register, JWT tokens |
| user-subscription-service | API | 8002 | user_subs_db | Users, Subscriptions, Plans |
| payment-service | API | 8003 | payment_db | Payments, Refunds |
| payment-scheduler | Worker | - | payment_db | Recurring payment jobs |
| notification-service | Worker | - | None | Email/SMS via Kafka |

---

## Tech Stack

| Component | Technology | Why? |
|-----------|------------|------|
| Framework | FastAPI | Async, fast, auto-docs, type-safe |
| Database | PostgreSQL | ACID compliance, reliable for transactions |
| ORM | SQLAlchemy | Industry standard, flexible |
| Migrations | Alembic | Version controlled schema changes |
| Cache | Redis | Fast, distributed locks, rate limiting |
| Message Queue | Apache Kafka | High throughput, persistent, replay capability |
| Containerization | Docker | Consistent environments |
| Orchestration | Kubernetes | Production scaling (future) |

---

## Key Design Patterns

### 1. API Gateway Pattern
Single entry point for all client requests. Handles cross-cutting concerns.

### 2. Database per Service
Each service owns its data. No direct DB access across services.

### 3. Event-Driven Architecture
Services communicate asynchronously via Kafka for non-critical operations.

### 4. Circuit Breaker
Fail fast when downstream services are unhealthy.

### 5. Idempotency
Prevent duplicate operations (especially payments) using idempotency keys.

### 6. Job Queue Pattern
Background processing with proper locking to prevent duplicate job execution.

---

## Data Flow Examples

### User Subscribes to a Plan

```
1. Client → API Gateway → Auth verify (JWT)
2. API Gateway → User-Subscription Service → Create subscription
3. User-Subscription Service → Payment Service → Charge card
4. Payment Service → Stripe API → Process payment
5. On success:
   - Payment Service → Kafka → "payment.success" event
   - Notification Service (consumer) → Send welcome email
   - User-Subscription Service → Activate subscription
```

### Monthly Recurring Payment

```
1. Payment Scheduler → Scan subscriptions due today
2. Create job records (status: PENDING)
3. Worker picks job (SELECT FOR UPDATE SKIP LOCKED)
4. Worker → Payment Service API → Charge card
5. On success: Update subscription.next_billing_date
6. On failure: Retry with exponential backoff
7. After max retries: Cancel subscription, notify user
```

---

## Resilience Strategies

| Strategy | Implementation |
|----------|----------------|
| Retry with Backoff | 1s → 2s → 4s → 8s (exponential) |
| Circuit Breaker | Open after 5 failures, half-open after 30s |
| Rate Limiting | Token bucket (100 req/min per user) |
| Distributed Locks | Redis SETNX for job processing |
| Idempotency | Store idempotency_key in Redis (24h TTL) |
| Dead Letter Queue | Failed Kafka messages after 3 retries |

---

## Monitoring & Observability

| Component | Tool |
|-----------|------|
| Metrics | Prometheus |
| Dashboards | Grafana |
| Distributed Tracing | OpenTelemetry |
| Logging | Structured JSON logs with correlation IDs |

---

## Future Enhancements

- [ ] Multi-region deployment
- [ ] Read replicas for databases
- [ ] GraphQL API layer
- [ ] Admin dashboard
- [ ] Analytics service
