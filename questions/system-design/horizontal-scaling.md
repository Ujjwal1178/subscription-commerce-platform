# Horizontal Scaling - Interview Questions

## Q1: What is Horizontal vs Vertical Scaling?

**Answer:**

| Type | What it means | Example |
|------|---------------|---------|
| **Vertical (Scale Up)** | Bigger machine | 4GB RAM → 16GB RAM |
| **Horizontal (Scale Out)** | More machines | 1 server → 4 servers |

```
Vertical Scaling:
┌─────────────┐      ┌─────────────┐
│   Server    │  →   │   Server    │
│   4GB RAM   │      │   16GB RAM  │
│   2 CPU     │      │   8 CPU     │
└─────────────┘      └─────────────┘
    BEFORE               AFTER

Horizontal Scaling:
┌─────────────┐      ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│   Server    │  →   │ Srv1 │ │ Srv2 │ │ Srv3 │ │ Srv4 │
│   4GB RAM   │      │ 4GB  │ │ 4GB  │ │ 4GB  │ │ 4GB  │
└─────────────┘      └──────┘ └──────┘ └──────┘ └──────┘
    BEFORE                      AFTER
```

---

## Q2: When to scale horizontally?

**Answer:**

Monitor these metrics:

| Metric | Threshold | Action |
|--------|-----------|--------|
| **CPU Usage** | > 70% for 5 min | Scale up |
| **Memory Usage** | > 80% | Scale up |
| **Response Time** | > 500ms average | Scale up |
| **Connection Pool** | Requests waiting | Scale up |
| **Error Rate** | > 1% | Investigate |

**Tools for monitoring:**
- Prometheus + Grafana
- AWS CloudWatch
- Datadog
- New Relic

---

## Q3: What is Auto-Scaling?

**Answer:**

Auto-scaling = System automatically adds/removes instances based on metrics.

**Kubernetes HPA Example:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    name: auth-service
  minReplicas: 2      # Always at least 2
  maxReplicas: 10     # Maximum 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          averageUtilization: 70  # Scale if CPU > 70%
```

**AWS Auto Scaling Group:**
- Scale out: Add instances when CPU > 70%
- Scale in: Remove instances when CPU < 30%
- Cooldown: Wait 5 min between scaling actions

---

## Q4: How does Load Balancer distribute traffic?

**Answer:**

```
                    ┌─────────────────┐
     Request ──────►│  Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │ Auth 1 │    │ Auth 2 │    │ Auth 3 │
         └────────┘    └────────┘    └────────┘
```

**Algorithms:**
| Algorithm | How it works |
|-----------|--------------|
| **Round Robin** | 1 → 2 → 3 → 1 → 2 → 3 |
| **Least Connections** | Send to server with fewest active requests |
| **IP Hash** | Same user IP → Same server (for sessions) |
| **Weighted** | Server1 gets 60%, Server2 gets 40% |

---

## Q5: What happens to database when you scale horizontally?

**Answer:**

**Problem:** Multiple app instances → One database → Bottleneck!

```
┌────────┐ ┌────────┐ ┌────────┐
│ Auth 1 │ │ Auth 2 │ │ Auth 3 │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┼──────────┘
               ▼
         ┌──────────┐
         │ Database │ ← Bottleneck!
         └──────────┘
```

**Solutions:**

1. **Connection Pooling** - Reuse connections (PgBouncer)
2. **Read Replicas** - Writes to master, reads from replicas
3. **Database Sharding** - Split data across multiple DBs
4. **Caching** - Redis for frequently accessed data

---

## Q6: Connection Pool with Multiple Instances?

**Answer:**

Each instance has its OWN connection pool:

```
┌─────────────┐     ┌─────────────┐
│   Auth 1    │     │   Auth 2    │
│ ┌─────────┐ │     │ ┌─────────┐ │
│ │Pool: 15 │ │     │ │Pool: 15 │ │
│ └────┬────┘ │     │ └────┬────┘ │
└──────┼──────┘     └──────┼──────┘
       │                   │
       └─────────┬─────────┘
                 ▼
           ┌──────────┐
           │ Postgres │
           │ max: 100 │
           └──────────┘
```

**Important:** Total connections = instances × pool_size
- 4 instances × 15 pool = 60 connections
- Postgres max_connections = 100
- Leave room for admin, monitoring, etc.

---

## Q7: What is "Stateless" and why important for scaling?

**Answer:**

**Stateless = Server doesn't remember previous requests**

```
Stateful (BAD for scaling):
User logs in → Server 1 stores session in memory
Next request goes to Server 2 → Session not found! ❌

Stateless (GOOD for scaling):
User logs in → Gets JWT token
Any server can verify JWT → Works! ✅
```

**Rule:** Store state externally (Redis, Database), not in server memory.

---

## Q8: What is "Sticky Sessions"? When to use?

**Answer:**

Sticky sessions = Same user always goes to same server.

```
User A → Always Server 1
User B → Always Server 2
User C → Always Server 1
```

**When to use:**
- Legacy apps with server-side sessions
- WebSocket connections
- Caching user data in server memory

**Problem:** If server dies, user loses session.

**Better approach:** Stateless with external session store (Redis).

---

## Q9: How to handle deployments with multiple instances?

**Answer:**

**Rolling Deployment:**
```
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ v1.0   │ │ v1.0   │ │ v1.0   │ │ v1.0   │
└────────┘ └────────┘ └────────┘ └────────┘

Step 1: Update one
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ v2.0 ✓ │ │ v1.0   │ │ v1.0   │ │ v1.0   │
└────────┘ └────────┘ └────────┘ └────────┘

Step 2: Update next
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ v2.0 ✓ │ │ v2.0 ✓ │ │ v1.0   │ │ v1.0   │
└────────┘ └────────┘ └────────┘ └────────┘

... until all updated
```

**Zero downtime:** Always some instances serving traffic.

---

## Q10: What metrics would you monitor for auth service?

**Answer:**

| Metric | Why |
|--------|-----|
| Request rate | Requests per second |
| Response time (p50, p95, p99) | User experience |
| Error rate | 4xx, 5xx responses |
| CPU/Memory | Resource utilization |
| DB connection pool | Waiting requests |
| Login success/failure rate | Security monitoring |
| OTP generation rate | Spam detection |

**Alerting rules:**
- p99 latency > 1s → Alert
- Error rate > 1% → Alert
- CPU > 80% for 5 min → Auto-scale

---

## Follow-up Questions:

1. "How would you scale a database?"
   → Read replicas, sharding, caching layer

2. "What's the difference between scaling and load balancing?"
   → Scaling = more instances, Load balancing = distributing traffic

3. "How do you handle shared state across instances?"
   → External store (Redis), Database, or make it stateless

4. "What's the cost implication of horizontal scaling?"
   → More instances = more cost, but can scale down when not needed
