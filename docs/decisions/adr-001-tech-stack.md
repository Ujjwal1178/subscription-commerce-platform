# ADR-001: Technology Stack Selection

## Status
Accepted

## Date
2024-01-XX

---

## Context

We are building a subscription commerce platform that needs to:
- Handle high traffic (target: 1M+ req/sec)
- Process payments reliably
- Maintain high availability
- Support async operations (notifications, recurring payments)
- Be developer-friendly and maintainable

---

## Decisions

### 1. Web Framework: FastAPI

**Decision**: Use FastAPI for all Python microservices.

**Alternatives Considered**:
| Framework | Pros | Cons |
|-----------|------|------|
| FastAPI | Async, fast, auto-docs, type hints | Newer, smaller community than Django |
| Flask | Simple, flexible | No async, manual everything |
| Django | Batteries included, ORM | Heavy, synchronous, overkill for microservices |

**Why FastAPI?**
- Native async/await support (critical for I/O bound operations)
- Automatic OpenAPI documentation (team collaboration)
- Pydantic validation (catch errors early)
- Performance comparable to Node.js and Go
- Used by Netflix, Uber, Microsoft in production

---

### 2. Database: PostgreSQL

**Decision**: Use PostgreSQL for all relational data.

**Alternatives Considered**:
| Database | Pros | Cons |
|----------|------|------|
| PostgreSQL | ACID, JSON support, mature | Slightly complex setup |
| MySQL | Popular, easy | Weaker ACID, less features |
| MongoDB | Flexible schema | Not ideal for transactions |

**Why PostgreSQL?**
- ACID compliance (critical for payments)
- Excellent support for complex queries
- JSON columns for flexibility when needed
- Battle-tested at scale (Instagram uses it)
- Strong ecosystem (extensions, tools)

---

### 3. ORM: SQLAlchemy + Alembic

**Decision**: Use SQLAlchemy as ORM with Alembic for migrations.

**Why?**
- Industry standard for Python
- Supports both sync and async
- Alembic provides version-controlled migrations
- Flexible: can drop to raw SQL when needed

---

### 4. Cache & Distributed Locks: Redis

**Decision**: Use Redis for caching, rate limiting, and distributed locks.

**Why Redis?**
- Sub-millisecond latency
- Rich data structures (strings, hashes, lists, sets)
- Built-in TTL (time-to-live)
- Pub/Sub for simple messaging
- Industry standard for:
  - Session storage
  - Rate limiting (token bucket)
  - Distributed locks (SETNX)
  - Caching

---

### 5. Message Queue: Apache Kafka

**Decision**: Use Kafka for async inter-service communication.

**Alternatives Considered**:
| Queue | Pros | Cons |
|-------|------|------|
| Kafka | High throughput, persistent, replay | Complex setup |
| RabbitMQ | Simple, flexible routing | Lower throughput |
| AWS SQS | Managed, easy | Vendor lock-in |

**Why Kafka?**
- Messages persist (can replay if consumer fails)
- High throughput (millions of events/sec)
- Consumer groups (parallel processing)
- Used by LinkedIn, Netflix, Uber
- Learning value: Most distributed systems use it

---

### 6. Containerization: Docker + Docker Compose

**Decision**: Containerize all services using Docker.

**Why?**
- Consistent environments (dev = prod)
- Easy local development with docker-compose
- Kubernetes-ready for production
- Isolation between services

---

## Consequences

### Positive
- Modern, performant stack
- Strong learning value for distributed systems
- Industry-relevant skills
- Production-ready patterns

### Negative
- Learning curve for Kafka
- Multiple databases to manage
- Complexity of microservices

### Mitigations
- Start with docker-compose for local dev (hides complexity)
- Thorough documentation
- Step-by-step implementation

---

## References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
