# Connection Pooling - Redis & Database

## Question 1: Connection Pool kya hai aur kyun zaroori hai?

### Answer:

**Connection Pool = Pre-created connections ka collection jo reuse hote hain**

**Without Pool (Bad):**
```
Request 1:
  Create TCP connection  ← 10-50ms (SLOW!)
  Send query             ← 0.1ms
  Close connection       ← 1ms

Request 2:
  Create NEW connection  ← 10-50ms again!
  Send query
  Close connection
```

**With Pool (Good):**
```
Application Start:
  Create 10 connections → Pool

Request 1:
  Borrow from pool      ← INSTANT!
  Send query            ← 0.1ms
  Return to pool        ← INSTANT!

Request 2:
  Borrow same connection ← INSTANT!
  ...
```

**Why creating connection is expensive:**
- TCP 3-way handshake (SYN, SYN-ACK, ACK)
- TLS/SSL handshake (if encrypted)
- Authentication
- Memory allocation on both client & server

---

## Question 2: max_connections=10 set kiya. 15 requests aaye toh kya hoga?

### Answer:

**5 requests WAIT karenge** until a connection becomes free.

```
Pool: [C1, C2, C3, ... C10]

Requests 1-10: Each borrows one connection ✅
Request 11-15: Wait in queue... ⏳

When Request 1 finishes:
  → Returns C1 to pool
  → Request 11 gets C1 ✅
```

**If wait time exceeds timeout → Error**

```python
# Redis example
ConnectionPool(
    max_connections=10,
    timeout=5,  # Wait max 5 seconds for connection
)
```

---

## Question 3: Pool size kitna rakhna chahiye?

### Answer:

**Rule of thumb:**
```
pool_size = (number_of_cores * 2) + effective_spindle_count
```

For most apps:
- **min_pool_size:** 5-10 (always ready)
- **max_pool_size:** 20-50 (burst handling)

**Too few connections:**
- Requests wait in queue
- Higher latency

**Too many connections:**
- Server memory exhausted
- Context switching overhead
- Database overwhelmed

**Interview tip:** "It depends on load testing results for your specific workload"

---

## Question 4: PostgreSQL pool vs Redis pool - difference?

### Answer:

| Aspect | PostgreSQL Pool | Redis Pool |
|--------|-----------------|------------|
| Connection cost | Very high (50-100ms) | Medium (10-20ms) |
| Why expensive | Complex auth, SSL, session setup | TCP + optional auth |
| Typical pool size | 10-50 | 10-100 |
| Connection per request | No (session-based) | Yes (borrowed per op) |

**Both use same concept, but PostgreSQL connections are MORE expensive to create.**

---

## Question 5: Singleton pattern pool mein kyun use karte hain?

### Answer:

**Singleton = Only ONE pool instance for entire application**

```python
# BAD - Multiple pools created!
def get_redis():
    pool = ConnectionPool(...)  # New pool every time!
    return Redis(connection_pool=pool)

# GOOD - Single pool reused
_pool = None

def get_redis():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(...)  # Created only once
    return Redis(connection_pool=_pool)  # Same pool reused
```

**Without singleton:**
- Multiple pools = Multiple sets of connections
- Memory waste
- Connection limit hit faster
- Defeats purpose of pooling!

---

## Question 6: Connection leak kya hai?

### Answer:

**Leak = Connection borrowed but never returned to pool**

```python
# BAD - Connection leak!
def get_user():
    conn = pool.get_connection()
    result = conn.execute("SELECT * FROM users")
    # Forgot to return connection!
    return result

# After 10 requests, pool exhausted! 💀
```

```python
# GOOD - Using context manager
def get_user():
    with pool.get_connection() as conn:
        result = conn.execute("SELECT * FROM users")
    # Automatically returned when block exits
    return result
```

**Our code uses dependency injection which handles this:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Always returns connection!
```

---

## Question 7: What happens when database restarts but pool has stale connections?

### Answer:

**Stale connection = Connection object exists but actual TCP connection is dead**

```
App Pool: [C1, C2, C3, C4, C5]  ← Thinks these work
Database: Restarted, all connections dropped!

Request uses C1 → ERROR! Connection is dead!
```

**Solutions:**

1. **Connection validation (ping before use):**
```python
pool = create_engine(
    url,
    pool_pre_ping=True  # Test connection before using
)
```

2. **Connection recycling:**
```python
pool = create_engine(
    url,
    pool_recycle=3600  # Replace connections older than 1 hour
)
```

3. **Automatic reconnection in library**

---

## Summary Table

| Concept | Purpose |
|---------|---------|
| Pool | Reuse connections, avoid creation overhead |
| max_connections | Limit concurrent connections |
| Singleton | One pool per application |
| Context manager | Prevent connection leaks |
| pre_ping | Detect stale connections |
| pool_recycle | Replace old connections |

---

## Tags
`connection-pool` `redis` `postgresql` `database` `performance` `singleton`
