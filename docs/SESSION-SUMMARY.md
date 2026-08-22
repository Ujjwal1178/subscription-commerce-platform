# Session Summary - Subscription Commerce Platform

> **Instructions for Kiro:** Read this file at the START of every session. Update at the END of every session with new Part.

---

# PART 1: Project Setup & Architecture
## Session Date: 22-23 August 2026 (Saturday-Sunday Night)

---

## Project Overview

**Goal:** Build a production-grade, Apple-like subscription commerce platform for Ujjwal's portfolio (targeting Apple interview)

**Approach:** Learning-first - understand every concept deeply, document interview questions, build incrementally

---

## What We Accomplished

### 1. Git Setup ✅
- **SSH key generated** for personal GitHub (`id_ed25519_personal`)
- **SSH config** created to handle multiple Git accounts (office + personal)
- **Remote URL** set to SSH: `git@github.com-personal:Ujjwal1178/subscription-commerce-platform.git`
- **Branch:** Working on `dev` branch (master is protected)

### 2. Project Structure ✅
```
subscription-commerce-platform/
├── .gitignore                    # Python microservices ignores
├── .env.example                  # Environment template
├── docker-compose.yml            # Local infrastructure
├── requirements-dev.txt          # Dev tools (pytest, black)
│
├── docs/
│   ├── architecture/
│   │   └── system-overview.md    # Full architecture diagram
│   ├── decisions/
│   │   └── adr-001-tech-stack.md # Tech decisions documented
│   └── setup/
│       └── local-development.md  # How to run locally
│
├── questions/                    # Interview Q&A Bank
│   ├── authentication/
│   │   └── stateful-vs-stateless.md
│   ├── databases/
│   │   ├── single-vs-multiple-db.md
│   │   └── postgresql-vs-mysql.md
│   ├── distributed-systems/
│   │   ├── inter-service-communication.md
│   │   └── job-queue-pattern.md
│   ├── docker/
│   │   ├── docker-networking.md
│   │   └── docker-volumes.md
│   ├── microservices/
│   │   └── monolith-vs-microservices.md
│   └── resilience/
│       └── circuit-breaker.md
│
├── services/                     # All services (APIs + Workers)
│   ├── api_gateway/
│   ├── auth_service/
│   ├── user_subscription_service/
│   ├── payment_service/
│   ├── notification_service/     # API for fetching notifications
│   ├── notification_worker/      # Kafka consumer, sends emails
│   └── payment_scheduler_worker/ # Recurring payments
│
├── shared/                       # Common code
│   ├── config/
│   ├── database/
│   ├── schemas/
│   ├── utils/
│   └── requirements.txt          # Shared dependencies
│
├── infrastructure/
│   └── docker/
│       └── postgres-init.sh      # Creates DBs on first run
│
└── tests/
```

### 3. Architecture Finalized ✅

**7 Services:**
| Service | Type | Port | Database | Purpose |
|---------|------|------|----------|---------|
| api_gateway | API | 8000 | None | Routing, rate limiting, JWT verify |
| auth_service | API | 8001 | auth_db | Login, register, JWT tokens |
| user_subscription_service | API | 8002 | user_subs_db | Users, subscriptions, plans |
| payment_service | API | 8003 | payment_db | Payments, refunds, Stripe |
| notification_service | API | 8004 | notification_db | Fetch/manage notifications |
| notification_worker | Worker | - | notification_db | Send emails via Kafka |
| payment_scheduler_worker | Worker | - | payment_db | Recurring payment jobs |

**Infrastructure:**
- PostgreSQL (4 databases inside one instance)
- Redis (caching, rate limiting, distributed locks)
- Kafka + Zookeeper (async messaging)
- Kafka UI (debugging at localhost:8080)

### 4. Docker Compose Setup ✅

**Images Downloaded:**
- postgres:15-alpine (416 MB)
- redis:7-alpine (57 MB)
- confluentinc/cp-kafka:7.5.0 (1.33 GB)
- confluentinc/cp-zookeeper:7.5.0 (1.33 GB)
- provectuslabs/kafka-ui:latest (449 MB)

**Volumes Created (Data Persistence):**
- postgres_data
- redis_data
- kafka_data
- zookeeper_data

**Status:** Images pulled, ready to test containers

### 5. Per-Service Requirements ✅

Each service has its own `requirements.txt` (not monolithic):
- `shared/requirements.txt` - Common (FastAPI, SQLAlchemy, Pydantic)
- `services/auth_service/requirements.txt` - JWT, passlib, bcrypt
- `services/payment_service/requirements.txt` - Stripe
- etc.

This keeps Docker images small and services independent.

---

## Key Concepts Covered

### Architecture
- [x] Microservices vs Monolith (when to use what)
- [x] API Gateway pattern (single entry point)
- [x] Database per service (not shared DB)
- [x] Event-driven architecture (Kafka)

### Distributed Systems
- [x] Inter-service communication (sync vs async)
- [x] Circuit breaker pattern (fail fast)
- [x] Job queue pattern (SELECT FOR UPDATE SKIP LOCKED)
- [x] Idempotency (prevent duplicate payments)
- [x] Stateless design (scale horizontally)

### Docker
- [x] Containers vs VMs
- [x] Docker networking (bridge, service DNS)
- [x] Volumes (data persistence)
- [x] Docker Compose (multi-container setup)
- [x] Health checks and depends_on

### Databases
- [x] PostgreSQL vs MySQL (why Postgres for payments)
- [x] ACID compliance importance
- [x] Single DB vs DB per service

### Authentication
- [x] Stateful (sessions) vs Stateless (JWT)
- [x] Why JWT for microservices
- [x] JWT logout strategies

### Scaling
- [x] Code-level scaling (async, caching, connection pooling)
- [x] Infra-level scaling (horizontal, load balancing)
- [x] Both are needed!

### Production (discussed, not implemented yet)
- [x] AWS VPC architecture
- [x] Private/Public subnets
- [x] Security groups
- [x] Kubernetes service discovery

---

## Interview Questions Documented (9 total)

1. **Monolith vs Microservices** - When to use, tradeoffs
2. **Single DB vs Database per Service** - Cross-service data access
3. **Inter-service Communication** - HTTP vs Kafka, resilience
4. **Job Queue Pattern** - Race conditions, SELECT FOR UPDATE
5. **Circuit Breaker** - States, fallbacks, vs retry
6. **PostgreSQL vs MySQL** - ACID, JSON, concurrency
7. **Stateful vs Stateless Auth** - Sessions vs JWT
8. **Docker Networking** - How containers communicate
9. **Docker Volumes** - Data persistence

---

## Pending / Next Session

### Immediate:
1. [ ] **Test Docker Compose** - Run `docker-compose up -d`, verify all containers
2. [ ] **Verify databases created** - Connect to Postgres, check 4 DBs exist
3. [ ] **Test Kafka UI** - Open localhost:8080

### Then:
4. [ ] **Auth Service** - First actual microservice
   - FastAPI project structure
   - SQLAlchemy models (User table)
   - Alembic migrations
   - Registration endpoint
   - Login endpoint with JWT
   
5. [ ] **JWT Deep Dive** - How tokens work internally, signing, verification

6. [ ] **Commit and push** changes to dev branch

---

## Important Commands

```bash
# Start infrastructure
cd d:\UGF\subscription-commerce-platform\subscription-commerce-platform
docker-compose up -d

# Check containers
docker-compose ps

# View logs
docker-compose logs -f postgres
docker-compose logs -f kafka

# Connect to PostgreSQL
docker exec -it scp_postgres psql -U postgres
\l  # List databases

# Connect to Redis
docker exec -it scp_redis redis-cli
PING

# Kafka UI
http://localhost:8080

# Stop everything (KEEP data)
docker-compose down

# Stop and DELETE data (careful!)
docker-compose down -v
```

---

## Files Modified This Session

1. `.kiro/steering/teaching-mode.md` - Rules + progress tracker
2. `docker-compose.yml` - Infrastructure setup
3. `infrastructure/docker/postgres-init.sh` - DB initialization
4. `.gitignore` - Python ignores
5. `.env.example` - Environment template
6. `requirements-dev.txt` - Dev dependencies
7. `shared/requirements.txt` - Common dependencies
8. All service `requirements.txt` files
9. All `__init__.py` files
10. `docs/` - Architecture, setup, decisions
11. `questions/` - 9 interview Q&A documents

---

## Learner Notes

**Name:** Ujjwal
**Goal:** Apple interview preparation
**Style:** Learn by understanding, not copying code
**Language:** Hindi-English mix (Hinglish) is fine

**Key Rule:** NEVER write code without explaining first. Ask "Ready to implement?" before coding.

---

## Git Status

**Branch:** dev
**Last Commit:** Documentation and interview questions
**Pending:** Structure changes, docker-compose, questions folder

**To commit next session:**
```bash
git add .
git commit -m "Add Docker infrastructure and project structure

- Docker Compose with Postgres, Redis, Kafka, Zookeeper
- Per-service requirements.txt
- 9 interview questions documented
- Session summary for continuity"
git push origin dev
```


---

# PART 2: Auth Service Development Begins
## Session Date: 23 August 2026 (Sunday Night)

### What We Did:
- [x] Discussed Docker image rebuild concept (when code changes)
- [x] Volume mounts vs image rebuild for development vs production
- [x] Added interview question: `docker/image-rebuild-on-code-change.md`

### Interview Questions Added This Session:
- **Docker: Image Rebuild on Code Change** - When to rebuild, volume mounts, dev vs prod setup

### Key Concepts Covered:
- Docker images are immutable (frozen at build time)
- Development uses volume mounts + hot reload (no rebuild needed)
- Production requires image rebuild for code changes
- Bind mounts vs Docker volumes

### What's Pending:
- [ ] Test Docker Compose (containers should be running)
- [ ] Commit current changes to dev branch
- [ ] Start Auth Service implementation
- [ ] JWT deep dive

---

<!-- 
TEMPLATE FOR NEW PARTS:

# PART X: [Title]
## Session Date: [Date]

### What We Did:
- 

### Key Concepts Covered:
- 

### Interview Questions Added:
- 

### Files Modified:
- 

### What's Pending for Next Session:
- 

### Important Notes:
- 

-->
