# Redis Fundamentals - Interview Questions

## Question 1: Redis kya hai?

### Answer:

**Redis = Remote Dictionary Server**

An **in-memory data store** used for:
- Caching
- Session storage
- Rate limiting
- Real-time analytics
- Message queues (Pub/Sub)
- Leaderboards

**Key characteristics:**
- Data stored in RAM (super fast)
- Key-value store (like Python dict)
- Single-threaded (no locks needed)
- Optional persistence (RDB, AOF)

---

## Question 2: Redis itna fast kyun hai compared to PostgreSQL?

### Answer:

| Factor | PostgreSQL | Redis |
|--------|-----------|-------|
| **Storage** | Disk (SSD/HDD) | RAM |
| **Access time** | ~5-50ms | ~0.1-1ms |
| **Threading** | Multi-threaded (locks) | Single-threaded (no locks) |
| **Query parsing** | Complex SQL parsing | Simple commands |
| **Data structures** | Tables, indexes, joins | Simple key-value |

**Speed comparison:**
```
Disk access:    ~5,000,000 nanoseconds (5ms)
RAM access:     ~100 nanoseconds (0.0001ms)

RAM is 50,000x faster than disk!
```

---

## Question 3: Redis single-threaded hai toh slow nahi hona chahiye?

### Answer:

**Counter-intuitive but NO!**

**Why single-thread works for Redis:**

1. **Operations are microseconds** (RAM access)
   - 1 thread doing 100K ops/sec > 10 threads doing 10K each

2. **No lock contention**
   - Multi-threading needs locks → waiting → slow

3. **No context switching**
   - Thread switching has overhead (~1-10 microseconds each)

4. **I/O multiplexing (epoll/kqueue)**
   - Single thread handles thousands of connections efficiently

**Benchmark:**
- Single Redis instance: 100,000+ operations/second
- Most apps never need more!

---

## Question 4: Redis restart hone pe data lost ho jata hai?

### Answer:

**By default, yes (in-memory).** But Redis has persistence options:

**1. RDB (Snapshotting):**
```
Every N minutes, dump entire dataset to disk
+ Fast restart
- Lose data since last snapshot
```

**2. AOF (Append Only File):**
```
Log every write operation to file
+ Minimal data loss (configurable)
- Slower than RDB
```

**3. Hybrid (RDB + AOF):**
```
Best of both worlds
Used in production
```

**For rate limiting?**
- Data loss acceptable (worst case: user gets extra attempts)
- TTL is 60 seconds anyway - data was temporary

---

## Question 5: Redis data types kaunse hain?

### Answer:

| Type | Example | Use Case |
|------|---------|----------|
| **String** | `SET name "Ujjwal"` | Caching, counters |
| **Hash** | `HSET user:1 name "Ujjwal" age 25` | Object storage |
| **List** | `LPUSH queue "task1"` | Message queues |
| **Set** | `SADD tags "python" "redis"` | Unique collections |
| **Sorted Set** | `ZADD leaderboard 100 "user1"` | Leaderboards, rankings |
| **Stream** | Event logging | Event sourcing |

**Our rate limiter uses String:**
```
SET rate:user123 "5"  # 5 attempts
EXPIRE rate:user123 60  # TTL 60 seconds
```

---

## Question 6: INCR command atomic kyun hai?

### Answer:

**Atomic = All-or-nothing, uninterruptible**

**Non-atomic (Bad):**
```python
# Two requests at same time
# Request A              # Request B
count = redis.get(key)   # Gets 5
                         count = redis.get(key)  # Gets 5
count = count + 1        # 6
                         count = count + 1       # 6
redis.set(key, count)    # Sets 6
                         redis.set(key, count)   # Sets 6 ❌
# Expected 7, got 6!
```

**Atomic (Good):**
```python
redis.incr(key)  # Redis does GET + ADD + SET in ONE operation
                 # No other command can interfere!
```

**Why Redis INCR is atomic:**
- Single-threaded - one command at a time
- Command executes completely before next one starts

---

## Question 7: Redis vs Memcached - difference?

### Answer:

| Feature | Redis | Memcached |
|---------|-------|-----------|
| Data types | Rich (String, Hash, List, Set...) | Only String |
| Persistence | Yes (RDB, AOF) | No |
| Replication | Yes | No |
| Pub/Sub | Yes | No |
| Lua scripting | Yes | No |
| Max value size | 512MB | 1MB |
| Multi-threaded | No (single) | Yes |

**When to use Memcached:**
- Simple caching only
- Need multi-threaded performance

**When to use Redis:**
- Need data structures
- Need persistence
- Need pub/sub, queues

**Most teams choose Redis** - more versatile

---

## Question 8: Redis can get overwhelmed too. How to protect?

### Answer:

**Multi-layer defense:**

```
Attacker: 1 Million requests/second
                │
                ▼
┌─────────────────────────────────────┐
│  LAYER 1: CDN/WAF (Cloudflare)     │
│  - Block at network edge            │
│  - 99% traffic blocked here         │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  LAYER 2: Load Balancer            │
│  - IP-based rate limiting           │
│  - Connection limits                │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  LAYER 3: Application + Redis      │ ← We are here
│  - User-level rate limiting         │
└─────────────────────────────────────┘
```

**Redis rate limiting protects against:**
- ✅ Brute force from single user
- ✅ API abuse
- ❌ Large-scale DDoS (need CDN/WAF)

---

## Question 9: TTL (Time To Live) kya hai?

### Answer:

**TTL = Automatic expiry time for a key**

```python
# Set key with 60 second expiry
redis.setex("rate:user123", 60, "1")

# After 60 seconds:
# Key automatically deleted by Redis!
# No manual cleanup needed
```

**Use cases:**
- Rate limiting (reset after time window)
- Session tokens (expire after logout time)
- Cache (expire to get fresh data)
- OTP (expire after 10 minutes)

**TTL commands:**
```
EXPIRE key 60     # Set TTL on existing key
TTL key           # Get remaining TTL
PERSIST key       # Remove TTL (key won't expire)
```

---

## Summary

| Concept | Key Point |
|---------|-----------|
| In-memory | Data in RAM = super fast |
| Single-threaded | No locks, no contention |
| Atomic ops | INCR, DECR are safe |
| TTL | Auto-expire keys |
| Persistence | RDB/AOF for durability |
| Not for DDoS | Need CDN/WAF for that |

---

## Tags
`redis` `caching` `rate-limiting` `in-memory` `nosql`
