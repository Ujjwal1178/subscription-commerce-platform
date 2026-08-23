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
- [x] Committed and pushed all code to dev branch
- [x] Started Auth Service Requirements Gathering
- [x] Discussed JWT Refresh Token storage strategies
- [x] Device ID approach (Ujjwal's idea!) vs Full Token storage

### Interview Questions Added This Session:
- **Docker: Image Rebuild on Code Change** - When to rebuild, volume mounts, dev vs prod setup
- **Refresh Token Storage** - Why store refresh tokens, device_id approach, stateful vs stateless

### Key Concepts Covered:
- Docker images are immutable (frozen at build time)
- Development uses volume mounts + hot reload (no rebuild needed)
- Production requires image rebuild for code changes
- Bind mounts vs Docker volumes
- **System Design Process:** Requirements → API Design → DB Schema → Implementation
- **Stateful Refresh, Stateless Access** pattern
- **Device ID in JWT** - Store device_id in DB, embed in JWT, validate on refresh
- **Single device login** - Replace device_id on new login, old device's refresh fails

### Auth Service Requirements (Finalized):
| Requirement | Decision |
|-------------|----------|
| Features | Register, Login, Logout, Forgot Password, Change Password |
| Registration Fields | Full name, Email (verified), Password |
| Multi-device | Single device (replace device_id on new login) |
| Access Token | JWT, 7 minutes, stateless |
| Refresh Token | JWT with device_id, 2 hours, semi-stateful |
| Token Storage | Store device_id in DB, not full token |
| Latency Target | Login < 500ms, Refresh < 100ms |
| Social Login | Later (Google/Apple) |

### What's Pending:
- [ ] Pydantic schemas (request/response validation)
- [ ] Register API implementation
- [ ] Password hashing with bcrypt
- [ ] Email/Phone encryption utilities
- [ ] OTP generation and verification
- [ ] JWT token generation

---

# PART 3: Auth Service Setup Complete
## Session Date: 23 August 2026 (Sunday Late Night)

### What We Did:
- [x] Folder restructure: services/, shared/, docker-compose → backend/
- [x] Auth Service API design (10 APIs documented in docs/api/auth-service-api.md)
- [x] Database schema design (3 tables documented in docs/database/auth-service-schema.md)
- [x] Dockerfile created (Python 3.13-slim, layer caching explained)
- [x] docker-compose.yml - auth-service added with volume mounts
- [x] Auth Service running on localhost:8001 ✅
- [x] SQLAlchemy models created (User, UserSession, OTPVerification)
- [x] Shared database utilities (Base class, engine, session factory)
- [x] Alembic setup for migrations
- [x] First migration generated and applied - tables created in auth_db!

### Key Concepts Covered:
- **Dockerfile layers & caching** - Copy requirements before code for faster rebuilds
- **python:3.13-slim vs alpine** - Slim for compatibility, alpine smallest but issues
- **psycopg vs psycopg2** - v3 is newer, better async support, Python 3.13 compatible
- **Volume mounts in docker-compose** - Live code sync for development
- **ORM (SQLAlchemy)** - Python classes mapped to DB tables
- **Why index columns** - B-tree for O(log n) lookups vs O(n) full scan
- **Cascade delete** - Auto-delete children when parent deleted
- **autocommit=False** - Transaction control, ACID Atomicity
- **Connection pooling** - Reuse connections (pool_size=5)
- **Soft delete vs Hard delete** - is_active flag vs actual DELETE
- **Alembic migrations** - Version control for database schema
- **OTP hashing** - Even 6-digit OTP stored as hash for security

### Interview Questions Added:
- `questions/api-design/api-design-best-practices.md` (7 questions)
- `questions/security/pii-encryption.md`
- `questions/databases/orm-and-sqlalchemy.md` (7 questions)

### Files Created/Modified:
```
backend/
├── docker-compose.yml (added auth-service)
├── shared/
│   └── database/
│       └── base.py (SQLAlchemy Base, engine, session)
└── services/
    └── auth_service/
        ├── Dockerfile
        ├── requirements.txt
        ├── alembic.ini
        └── app/
            ├── main.py (FastAPI entry point)
            ├── models/
            │   ├── __init__.py
            │   ├── user.py
            │   ├── user_session.py
            │   └── otp_verification.py
            └── migrations/
                ├── env.py
                └── versions/
                    └── 624b931af574_create_auth_tables.py
```

### Database Status:
```
auth_db tables:
✅ users
✅ user_sessions  
✅ otp_verifications
✅ alembic_version (migration tracking)
```

### Commands to Remember:
```bash
# Start all containers
cd backend
docker-compose up -d

# View auth service logs
docker-compose logs -f auth-service

# Run Alembic migrations
docker exec -w /app scp_auth_service alembic upgrade head

# Generate new migration
docker exec -w /app scp_auth_service alembic revision --autogenerate -m "description"

# Rollback migration
docker exec -w /app scp_auth_service alembic downgrade -1

# Connect to auth_db
docker exec -it scp_postgres psql -U postgres -d auth_db
\dt  # List tables
```

### What's Pending for Next Session:
- [ ] Pydantic schemas (RegisterRequest, LoginRequest, etc.)
- [ ] Register API implementation
- [ ] Password hashing with bcrypt
- [ ] Email/Phone encryption utilities (AES)
- [ ] OTP generation and verification
- [ ] JWT token generation (access + refresh)
- [ ] Login API implementation

---

# PART 4: SQLAlchemy Deep Dive + Learning Session
## Session Date: 24 August 2026 (Monday)

### What We Learned (Teaching Session):

**SQLAlchemy Models - Core Concepts:**
- `Base = declarative_base()` → Parent class for all models
- `Column()` → Defines database columns
- `nullable=False` → Required field, NOT NULL constraint
- `default=uuid.uuid4` → Auto-generate value if not provided
- `unique=True` → No duplicates allowed + auto-creates index in PostgreSQL
- `index=True` → Faster lookups (B-tree), redundant if already unique
- `relationship()` → Link between tables (User → Sessions)

**Encryption vs Hashing (Interview Gold!):**
- **Hashing:** One-way, same input = same output (SHA256, bcrypt)
- **Encryption:** Two-way, same input = DIFFERENT output with IV (AES)
- **Why can't UNIQUE on encrypted column?** → IV makes same data encrypt differently!
- **Password:** Always HASH (bcrypt) - never need original
- **PII (email, phone):** ENCRYPT - need to display/send later

**Port Mapping (Docker):**
- `5432:5432` = `HOST_PORT:CONTAINER_PORT`
- Left = Your machine's port (what you connect to)
- Right = Container's internal port

### Interview Questions Added:
- `questions/databases/encryption-vs-hashing.md` (7 detailed Q&As)

### Key Realizations:
- UNIQUE constraint auto-creates index in PostgreSQL
- Encrypted columns can't have UNIQUE (IV makes output different each time)
- Need hash column for lookups + encrypted column for display

### What's Pending for Next Session:
- [ ] Business logic for Auth Service
- [ ] Pydantic schemas
- [ ] Register API implementation
- [ ] JWT token generation

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
