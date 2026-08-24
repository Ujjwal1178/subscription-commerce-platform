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
- [ ] Business logic (service layer) for Register API
- [ ] API endpoint for Register
- [ ] Password hashing with bcrypt
- [ ] Email/Phone encryption (AES)
- [ ] OTP generation
- [ ] JWT token generation

---

# PART 5: Pydantic Schemas + Deep Learning Session
## Session Date: 24 August 2026 (Monday Late Night)

### What We Did:
- [x] DB Extension connect karna sikha (PostgreSQL + Redis)
- [x] Port mapping deep dive (HOST:CONTAINER)
- [x] Rate limiting discussion (Redis-based, multi-layer)
- [x] User enumeration attack prevention
- [x] Data ownership in microservices (Single Source of Truth)
- [x] Pydantic schemas created (auth.py, user.py)
- [x] Custom validators for password, phone, OTP
- [x] `__all__` in Python explained
- [x] bcrypt vs SHA256 for passwords
- [x] Salting, peppering, cost factor explained

### Key Concepts Learned:

**Port Mapping:**
- `5432:5432` = HOST_PORT:CONTAINER_PORT
- Left = your machine, Right = container internal

**Rate Limiting (Industry Standard):**
- Layer 1: Global IP limit (100/min)
- Layer 2: Per endpoint (login: 10/min, register: 5/min)
- Layer 3: Per user after login (50/min)
- Storage: Redis (fast, TTL, atomic)

**User Enumeration Prevention:**
- Same response for existing/non-existing users
- Generic error messages
- Rate limiting on sensitive endpoints

**Data Ownership:**
- Each microservice owns its data
- Others access via async API calls
- No duplicate user tables across services

**Password Hashing:**
- bcrypt over SHA256 (intentionally slow)
- Salt = random string per user (prevents rainbow tables)
- Cost factor = adjustable difficulty (rounds=12 recommended)
- bcrypt stores salt inside the hash itself

**Pydantic:**
- `Field()` for basic validation (min_length, max_length)
- `EmailStr` for auto email validation
- `@field_validator` for custom logic
- `Optional[str]` for nullable fields
- `__all__` controls `from module import *`

### Files Created:
```
backend/services/auth_service/app/schemas/
├── __init__.py (exports all schemas)
├── auth.py (Register, Login, OTP, Refresh, Logout, Password schemas)
└── user.py (Profile schemas)

questions/security/
├── rate-limiting.md (10 Q&As)
└── password-hashing.md (10 Q&As)

questions/microservices/
└── data-ownership.md (7 Q&As)
```

### Interview Questions Added (27 new):
- Rate limiting algorithms (fixed window, sliding window, token bucket)
- Redis for rate limiting
- Shared IP problem (office NAT)
- User enumeration attack
- Data ownership in microservices
- bcrypt vs SHA256
- Salt, pepper, cost factor
- Rainbow table attacks
- Password hash migration

### What's Pending for Next Session:
- [ ] Test Register API
- [ ] Login method in service layer
- [ ] Login API endpoint
- [ ] JWT token generation

---

# PART 6: Register API Complete + Deep Learning
## Session Date: 25 August 2026 (Monday)

### What We Built:

**Utilities (shared/utils/):**
- `security.py` - hash_password(), verify_password() (bcrypt)
- `encryption.py` - encrypt_data(), decrypt_data(), generate_hash() (AES + SHA256)
- `otp.py` - generate_otp(), hash_otp(), verify_otp()

**Configuration:**
- `backend/.env` - Common env file for all services
- `auth_service/app/config.py` - Loads env vars
- `auth_service/app/logger.py` - Proper logging (no print!)

**Business Logic:**
- `auth_service/app/services/auth_service.py` - AuthService class with register_user()

**API Layer:**
- `auth_service/app/dependencies.py` - Database session injection
- `auth_service/app/api/auth.py` - POST /api/v1/auth/register endpoint
- `auth_service/app/main.py` - FastAPI app with router

### Key Concepts Learned:

**bcrypt:**
- rounds=12 means 2^12 = 4096 iterations
- Salt stored inside hash string
- Intentionally slow for security

**AES Encryption:**
- Padding (PKCS7) needed for 16-byte blocks
- IV stored with ciphertext for decryption
- Same input + different IV = different output

**Timing Attacks:**
- Normal `==` comparison leaks timing info
- `secrets.compare_digest()` = constant time comparison

**Functions vs Classes:**
- Functions for stateless operations
- Classes when you need state (like db session)

**SQLAlchemy Internals:**
- Model class provides table/column mapping
- `db.add()` marks for insert
- `db.flush()` executes SQL, keeps transaction open
- `db.commit()` finalizes transaction
- `relationship()` = lazy query shortcut

**Connection Pool:**
- Engine = Pool of connections (reused)
- Session = New per request (uses connection from pool)
- pool_size=5, max_overflow=10 (total max 15)

**Horizontal Scaling:**
- Monitor CPU, memory, response time
- Auto-scale with Kubernetes HPA or AWS ASG
- Each instance has own connection pool

**Dependency Injection:**
- `Depends(get_db)` injects db session
- `yield` pauses, returns to cleanup after endpoint

### Files Created:
```
backend/
├── .env (common for all services)
└── services/auth_service/app/
    ├── config.py
    ├── logger.py
    ├── dependencies.py
    ├── api/
    │   ├── __init__.py
    │   └── auth.py (Register endpoint)
    ├── services/
    │   └── auth_service.py (Business logic)
    └── main.py (Updated with router)

shared/utils/
├── __init__.py
├── security.py (bcrypt)
├── encryption.py (AES + SHA256)
└── otp.py

questions/
├── databases/sqlalchemy-internals.md
├── security/timing-attacks.md
├── security/hashing-and-collision.md
├── python/functions-vs-classes.md
└── system-design/horizontal-scaling.md
```

### Interview Questions Added:
- SQLAlchemy internals (flush vs commit, relationship)
- Timing attacks prevention
- Hashing collision probability
- Functions vs Classes decision
- Horizontal scaling metrics and auto-scaling

### API Ready for Testing:
```
POST /api/v1/auth/register
{
    "user_name": "Ujjwal Thakur",
    "email": "ujjwal@gmail.com",
    "phone_number": "+919876543210",
    "password": "Secret@123"
}
```

### What's Pending:
- [ ] Test Register API (docker-compose up -d --build)
- [ ] Login method + endpoint
- [ ] JWT token generation
- [ ] Verify OTP endpoint

---

# PART 7: Register API Working + Redis Rate Limiting Discussion
## Session Date: 25 August 2026 (Monday Night)

### What We Did:
- [x] Fixed ENCRYPTION_KEY length (31 → 32 bytes)
- [x] Learned `docker-compose restart` vs `stop + up` (env vars don't reload on restart!)
- [x] Register API tested and working! ✅
- [x] User created in DB with encrypted PII
- [x] OTP logged in dev mode (615732)
- [x] Volume mount + hot reload explained (why no rebuild needed)
- [x] Rate limiting architecture discussion (Redis vs DB)

### Register API Test Results:
```json
// Request
POST http://localhost:8001/api/v1/auth/register
{
    "user_name": "Ujjwal Thakur",
    "email": "ujjwal@gmail.com",
    "phone_number": "+919876543210",
    "password": "Secret@123"
}

// Response (201 Created)
{
    "success": true,
    "message": "Registration successful. Please verify your email.",
    "otp_expires_in": 600,
    "masked_email": "uj****@gmail.com"
}
```

### Database Verification:
- User created with UUID: `33040f8d-25c6-47d7-b886-cf768d236078`
- email_encrypted: AES encrypted ✅
- email_hash: SHA256 for lookups ✅
- password_hash: bcrypt ($2b$12$...) ✅
- is_email_verified: false (pending OTP verification)
- OTP record created with hashed OTP

### Key Concepts Learned:

**Docker restart vs stop/up:**
- `restart` = Same container, env vars NOT reloaded
- `stop` + `up` = Container recreated, fresh env vars
- Always verify with: `docker exec container printenv VARIABLE`

**Volume Mount + Hot Reload:**
- Volume mount = Live link between host and container
- `--reload` flag watches for file changes
- Code changes: No rebuild needed
- requirements.txt changes: Rebuild needed

**Rate Limiting - Where to Store:**
- DB-based = Slow, DB hit on every request, bad for frequent checks
- Redis-based = Fast (microseconds), TTL support, atomic operations
- **Redis = Shield** (fast rejection), **DB = Audit** (persistent record)

**Two Types of Rate Limiting:**
1. **Redis Rate Limit:** 10 requests/minute (frequent check, temporary)
2. **DB Attempt Tracking:** 3 lifetime attempts (audit trail, persistent)

### Interview Questions Added (3 new):
- `questions/system-design/rate-limiting-where.md` - Redis vs DB for rate limiting
- `questions/docker/restart-vs-stop-up.md` - Environment variables reload
- `questions/docker/volume-mount-hot-reload.md` - Why no rebuild in dev

### Files Modified:
- `backend/.env` - Fixed ENCRYPTION_KEY to 32 bytes
- `backend/services/auth_service/app/services/auth_service.py` - Fixed column name mismatch

### Commands Used:
```bash
# Verify env var in container
docker exec scp_auth_service printenv ENCRYPTION_KEY

# Proper restart for env changes
docker-compose stop auth-service
docker compose up -d auth-service

# View logs
docker logs scp_auth_service --tail 20
```

### What's Next:
- [x] Verify OTP API with Redis rate limiting ✅
- [x] Redis client utility (shared/utils/redis_client.py) ✅
- [x] Rate limiter utility ✅
- [ ] Resend OTP API
- [ ] Login API + JWT generation
- [ ] Auto-login after OTP verification

---

# PART 8: Verify OTP API + Redis Rate Limiting Complete
## Session Date: 25 August 2026 (Monday Late Night)

### What We Built:

**Redis Utilities (shared/utils/):**
- `redis_client.py` - Connection pool, singleton pattern, health check
- `rate_limiter.py` - Reusable rate limiting with Redis

**Verify OTP Feature:**
- `auth_service.py` - `verify_otp()` method with full business logic
- `auth.py` - POST `/api/v1/auth/verify-otp` endpoint
- `config.py` - Rate limit configuration variables

### Key Concepts Learned:

**Atomic Operations in Redis:**
- Single Redis command = atomic (no race condition)
- `INCR` does read+add+write in ONE operation
- Multiple commands need `MULTI/EXEC` for atomicity

**Fail-Open vs Fail-Closed:**
- Fail-Open: Allow request if Redis down (better UX)
- Fail-Closed: Block request if Redis down (more secure)
- Choice depends on context (payment = closed, general = open)

**Rate Limiting Architecture:**
- Redis for frequent checks (fast, TTL support)
- DB for audit trail (persistent, lifetime attempts)
- Both serve different purposes!

**Docker Learnings:**
- `requirements.txt` change = image rebuild needed
- `--no-cache` flag forces fresh build
- Service-specific requirements, not shared folder

### Files Created/Modified:
```
backend/shared/utils/
├── redis_client.py (NEW) - Connection pool, helpers
├── rate_limiter.py (NEW) - Rate limit logic
└── __init__.py (UPDATED) - Export new modules

backend/services/auth_service/
├── requirements.txt (UPDATED) - Added redis==5.0.1
├── app/
│   ├── config.py (UPDATED) - Rate limit config
│   ├── services/auth_service.py (UPDATED) - verify_otp() method
│   └── api/auth.py (UPDATED) - verify-otp endpoint

backend/shared/requirements.txt (UPDATED) - Added redis

questions/
├── resilience/fail-open-fail-closed.md (NEW)
└── distributed-systems/atomic-operations.md (NEW)
```

### API Endpoints Working:
```
POST /api/v1/auth/register ✅
POST /api/v1/auth/verify-otp ✅ (NEW!)
```

### Test Results:
```
1. Register new user → 201 Created, OTP in logs ✅
2. Verify with correct OTP → "Email verified successfully" ✅
3. Verify expired OTP → "OTP has expired" ✅
4. Rate limiting via Redis → Working ✅
```

### Interview Questions Added (2 new):
- `resilience/fail-open-fail-closed.md` - When to use which strategy
- `distributed-systems/atomic-operations.md` - Redis INCR, race conditions

### Database State:
- 2 users in `users` table
- 2 OTP records in `otp_verifications` table
- `test@example.com` - `is_email_verified = true` ✅

### What's Pending for Next Session:
- [ ] Login API with JWT token generation
- [ ] Auto-login after OTP verification (optional)
- [ ] Resend OTP API
- [ ] Refresh token endpoint
- [ ] Logout endpoint

### Important Decisions Made:
- **Email hash as Redis key** - No PII in Redis
- **Fail-open for rate limiting** - UX over temporary vulnerability
- **Auto-login after verify** - Better UX (implement tomorrow)

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
