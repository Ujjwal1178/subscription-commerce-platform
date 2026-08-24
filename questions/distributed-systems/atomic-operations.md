# Atomic Operations in Redis

## Question 1: "Atomic operation" ka kya matlab hai?

### Answer:

**Atomic = Indivisible, uninterruptible operation**

Ek atomic operation ya toh **completely execute hoti hai** ya **bilkul nahi hoti**. Beech mein koi interrupt nahi kar sakta.

### Non-Atomic Example (Problem):

```python
# Two requests trying to increment same counter

# Request A                    # Request B
count = redis.get("visits")    # Gets 100
                               count = redis.get("visits")  # Gets 100
count = count + 1              # 101
                               count = count + 1            # 101
redis.set("visits", count)     # Sets 101
                               redis.set("visits", count)   # Sets 101 ❌

# Expected: 102
# Got: 101 (Lost one increment!)
```

### Atomic Example (Solution):

```python
# Request A                    # Request B
redis.incr("visits")           # Redis does: read(100) + add(1) + write(101)
                               # Returns 101, ALL IN ONE OPERATION
                               
                               redis.incr("visits")  # read(101) + add(1) + write(102)
                               # Returns 102 ✅
```

---

## Question 2: Redis mein kaunsi commands atomic hain?

### Answer:

| Command | Description | Atomic? |
|---------|-------------|---------|
| `INCR` | Increment by 1 | ✅ Yes |
| `INCRBY` | Increment by N | ✅ Yes |
| `DECR` | Decrement by 1 | ✅ Yes |
| `SETNX` | Set if not exists | ✅ Yes |
| `GETSET` | Get old, set new | ✅ Yes |
| `LPUSH/RPUSH` | Add to list | ✅ Yes |
| `GET` + `SET` | Two commands | ❌ No |

**Rule:** Single Redis command = Atomic. Multiple commands = Not atomic (unless using transactions).

---

## Question 3: Atomicity kyun important hai rate limiting mein?

### Answer:

**Rate limiting needs accurate count!**

```
Scenario: 10 requests/minute limit

Without atomicity:
  Request 1-8: count = 8
  Request 9 & 10 (same millisecond):
    Both read: 8
    Both increment: 9
    Both write: 9
  Request 11: count = 10 (allowed!) ❌
  
With atomicity (INCR):
  Request 1-8: count = 8
  Request 9: INCR → 9
  Request 10: INCR → 10
  Request 11: INCR → 11 (blocked!) ✅
```

**Without atomicity:** User could sneak in extra requests during race condition.

---

## Question 4: Redis transactions (MULTI/EXEC) kya hain?

### Answer:

When you need multiple commands to be atomic together:

```python
# Without transaction (NOT atomic)
redis.set("balance", 100)
redis.set("last_updated", "2024-01-01")
# Another request could read between these!

# With transaction (Atomic)
pipe = redis.pipeline()
pipe.multi()
pipe.set("balance", 100)
pipe.set("last_updated", "2024-01-01")
pipe.execute()  # Both execute together!
```

**MULTI/EXEC** groups commands into a single atomic operation.

---

## Question 5: Compare atomicity in Redis vs Database

### Answer:

| Aspect | Redis | Database (SQL) |
|--------|-------|----------------|
| Single operation | Atomic by default | Atomic by default |
| Multiple operations | MULTI/EXEC | Transaction (BEGIN/COMMIT) |
| Performance | Microseconds | Milliseconds |
| Lock mechanism | Single-threaded | Row/Table locks |
| Rollback | Limited (DISCARD) | Full rollback (ROLLBACK) |

**Why Redis is faster for atomic ops?**
- Redis is single-threaded (one command at a time)
- No lock contention
- In-memory (no disk I/O)

---

## Question 6: What is CAS (Compare-And-Swap)?

### Answer:

**CAS = Check value, only update if unchanged**

```python
# Optimistic locking pattern
# "I'll update only if no one else changed it"

# Redis WATCH + MULTI pattern
redis.watch("counter")
current = redis.get("counter")

if current < 100:
    pipe = redis.pipeline()
    pipe.multi()
    pipe.incr("counter")
    pipe.execute()  # Fails if counter changed since WATCH!
```

**Use case:** When you need to check a condition before atomic update.

---

## Summary

| Concept | Key Point |
|---------|-----------|
| Atomic | All-or-nothing, uninterruptible |
| INCR | Single command = atomic |
| Race condition | Multiple non-atomic ops = data corruption |
| MULTI/EXEC | Group commands for atomicity |
| Redis single-thread | Natural atomicity for single commands |

---

## Tags
`redis` `atomic` `race-condition` `distributed-systems` `concurrency`
