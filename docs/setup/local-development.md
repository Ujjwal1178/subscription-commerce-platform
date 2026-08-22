# Local Development Setup

## Prerequisites

Before starting, ensure you have installed:

- [ ] Python 3.11+
- [ ] Docker Desktop
- [ ] Git
- [ ] VS Code (recommended) or any IDE

---

## Quick Start

```bash
# 1. Clone the repository
git clone git@github.com-personal:Ujjwal1178/subscription-commerce-platform.git
cd subscription-commerce-platform

# 2. Start infrastructure (Postgres, Redis, Kafka)
docker-compose up -d

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run migrations
alembic upgrade head

# 6. Start services
# (Each service in separate terminal)
uvicorn services.api_gateway.main:app --port 8000 --reload
uvicorn services.auth_service.main:app --port 8001 --reload
uvicorn services.user_subscription_service.main:app --port 8002 --reload
uvicorn services.payment_service.main:app --port 8003 --reload
```

---

## Project Structure

```
subscription-commerce-platform/
├── docs/                    # Documentation
│   ├── architecture/
│   ├── decisions/
│   └── setup/
├── questions/               # Interview Q&A
├── services/
│   ├── api_gateway/
│   ├── auth_service/
│   ├── user_subscription_service/
│   ├── payment_service/
│   └── notification_service/
├── shared/                  # Common code
│   ├── config/
│   ├── database/
│   ├── models/
│   └── utils/
├── workers/
│   └── payment_scheduler/
├── infrastructure/
│   ├── docker/
│   └── kubernetes/
├── tests/
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# JWT
JWT_SECRET=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=30

# Stripe (Test Mode)
STRIPE_API_KEY=sk_test_xxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
```

---

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache, Rate Limiting |
| Kafka | 9092 | Message Queue |
| Zookeeper | 2181 | Kafka coordination |

---

## Useful Commands

```bash
# View logs
docker-compose logs -f postgres
docker-compose logs -f kafka

# Reset database
docker-compose down -v  # Removes volumes
docker-compose up -d

# Run tests
pytest tests/ -v

# Format code
black .
isort .

# Type checking
mypy services/
```

---

## API Documentation

Once services are running:

| Service | Swagger UI | ReDoc |
|---------|------------|-------|
| API Gateway | http://localhost:8000/docs | http://localhost:8000/redoc |
| Auth Service | http://localhost:8001/docs | http://localhost:8001/redoc |
| User-Subs Service | http://localhost:8002/docs | http://localhost:8002/redoc |
| Payment Service | http://localhost:8003/docs | http://localhost:8003/redoc |

---

## Troubleshooting

### Port already in use
```bash
# Find process using port
netstat -ano | findstr :8000
# Kill process
taskkill /PID <PID> /F
```

### Database connection failed
```bash
# Check if postgres is running
docker-compose ps
# Restart postgres
docker-compose restart postgres
```

### Kafka not connecting
```bash
# Kafka needs Zookeeper - check both are healthy
docker-compose logs kafka
docker-compose logs zookeeper
```
