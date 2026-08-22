# Docker Networking

## Question
"How do Docker containers communicate with each other? If my app is in one container and database in another, how does the connection work?"

---

## Answer

> "Docker containers are isolated by default - they can't communicate directly. To enable communication, we put them on the same **Docker network**.
>
> Docker Compose automatically creates a network for all services defined in the same file. Containers can then communicate using **service names as hostnames**.
>
> For example, if I have a `postgres` service and an `auth-service`, the auth service can connect to `postgres:5432` - Docker's internal DNS resolves the service name to the container's IP."

---

## Visual Explanation

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HOST MACHINE                                │
│                                                                     │
│   WITHOUT NETWORK (Default - Isolated):                             │
│   ┌─────────────────┐         ┌─────────────────┐                   │
│   │   Container A   │   ❌    │   Container B   │                   │
│   │   (App)         │ ─ ─ ─ ─▶│   (Database)    │                   │
│   │                 │         │                 │                   │
│   └─────────────────┘         └─────────────────┘                   │
│   Can't communicate! Each thinks IT is localhost.                   │
│                                                                     │
│   ─────────────────────────────────────────────────────────────     │
│                                                                     │
│   WITH DOCKER NETWORK:                                              │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    app-network                              │   │
│   │                   (172.18.0.0/16)                           │   │
│   │                                                             │   │
│   │   ┌─────────────────┐         ┌─────────────────┐           │   │
│   │   │   auth-service  │   ✅    │     postgres    │           │   │
│   │   │   172.18.0.2    │ ◀─────▶ │   172.18.0.3    │           │   │
│   │   │                 │         │                 │           │   │
│   │   │ connects to:    │         │                 │           │   │
│   │   │ postgres:5432   │         │                 │           │   │
│   │   └─────────────────┘         └─────────────────┘           │   │
│   │                                                             │   │
│   │   Docker DNS: "postgres" → 172.18.0.3                       │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Concept: Service Name = Hostname

```yaml
# docker-compose.yml
services:
  postgres:           # ← This name becomes the hostname!
    image: postgres:15
    
  auth-service:
    build: ./auth
    environment:
      DB_HOST: postgres   # ← Use service name, NOT localhost!
      DB_PORT: 5432
```

```python
# In your Python code
DATABASE_URL = "postgresql://postgres:password@postgres:5432/auth_db"
#                                              ^^^^^^^^
#                                         Service name, not localhost!
```

---

## Network Types

| Type | Description | Use Case |
|------|-------------|----------|
| **bridge** | Default, isolated network | Most common, container-to-container |
| **host** | No isolation, uses host network | Performance critical, rare |
| **none** | No networking | Security isolation |
| **overlay** | Multi-host networking | Docker Swarm, Kubernetes |

---

## Follow-up Questions

### Q1: "What's the difference between `localhost` and service name?"

**Answer**:
```
Inside auth-service container:
- localhost → Points to auth-service itself (127.0.0.1)
- postgres  → Points to postgres container (172.18.0.3)

Common mistake:
DB_HOST=localhost  ❌ Won't find postgres!
DB_HOST=postgres   ✅ Docker DNS resolves it!
```

### Q2: "How do I access containers from my laptop (host machine)?"

**Answer**:
```yaml
services:
  postgres:
    ports:
      - "5432:5432"   # host_port:container_port
```
- From laptop: `localhost:5432` (goes through port mapping)
- From another container: `postgres:5432` (uses Docker network)

### Q3: "How does this work in production (Kubernetes)?"

**Answer**:
```
Docker Compose:
  DB_HOST = "postgres"

Kubernetes:
  DB_HOST = "postgres-service.default.svc.cluster.local"
  
Same concept - service discovery via DNS!
Kubernetes has its own DNS for service names.
```

### Q4: "Can containers on different networks communicate?"

**Answer**: No, by default. You need to either:
1. Put them on the same network
2. Create a shared network and attach both
3. Use port mapping through host

---

## Interview Tips

1. **Draw the diagram** - Visualize networks during interview
2. **Explain DNS** - Docker has built-in DNS resolution
3. **Know the difference** - `localhost` vs service name
4. **Connect to production** - Same concept applies in Kubernetes
