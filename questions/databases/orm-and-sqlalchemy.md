# ORM & SQLAlchemy Interview Questions

## Q1: What is ORM? Why use it?

**ORM = Object Relational Mapping**

Maps database tables to Python classes.

**Benefits:**
| Benefit | Explanation |
|---------|-------------|
| Type safety | `User.email` typo caught by IDE, not at runtime |
| No SQL injection | ORM handles escaping automatically |
| Python objects | Row = Object, easy to work with |
| Database agnostic | Same code for PostgreSQL, MySQL, SQLite |
| Migrations | Schema changes tracked in code |

**Example:**
```python
# Without ORM (raw SQL)
cursor.execute("INSERT INTO users (name) VALUES ('Ujjwal')")

# With ORM
user = User(name="Ujjwal")
db.add(user)
db.commit()
```

---

## Q2: What is autocommit=False and why?

**Answer:** We disable autocommit for **transaction control**.

```python
try:
    user = User(name="Ujjwal")
    db.add(user)
    
    session = Session(user_id=user.id)
    db.add(session)
    
    db.commit()    # Both saved together ✅
except:
    db.rollback()  # Nothing saved, clean state ✅
```

**ACID Atomicity:** Either ALL operations succeed, or NONE.

**Use case:** Bank transfer - debit one account, credit another. If credit fails, debit should rollback.

---

## Q3: What does cascade="all, delete-orphan" mean?

**Answer:** When parent is deleted, automatically delete all children.

```python
class User(Base):
    sessions = relationship("UserSession", cascade="all, delete-orphan")

# When user is deleted:
db.delete(user)  # All user's sessions also deleted automatically
```

**Note:** In soft-delete systems (is_active=False), cascade doesn't trigger. It's for actual DELETE operations.

---

## Q4: Why use index=True on email_hash?

**Answer:** B-tree index for fast lookups.

```
Without index: Full table scan → O(n) → 1M comparisons
With index: B-tree search → O(log n) → ~20 comparisons
```

**When to index:**
- Columns used in WHERE clauses frequently (email, user_id)
- Columns used in JOIN conditions
- Columns used in ORDER BY

**When NOT to index:**
- Columns rarely searched
- Tables with heavy INSERT/UPDATE (index slows writes)

---

## Q5: Why hash OTP instead of storing plain text?

**Answer:** Defense in depth - protect even if database is compromised.

**Plain OTP stored:**
```
| user_id | otp    |
| usr_123 | 482956 |

Database leaked → Attacker uses OTP before expiry! 😱
```

**Hashed OTP stored:**
```
| user_id | otp_hash                    |
| usr_123 | sha256(482956) = a8f5f1... |

Database leaked → Attacker gets useless hash 😢
```

**Verification flow:**
1. User enters OTP: 482956
2. Server hashes input: sha256(482956)
3. Compare with stored hash
4. Match → Verified!

---

## Q6: What is connection pooling? (pool_size=5)

**Answer:** Reuse database connections instead of creating new ones.

**Without pool:**
```
Request 1 → Create connection → Query → Close connection
Request 2 → Create connection → Query → Close connection
(Each connection takes ~50-100ms to establish)
```

**With pool:**
```
App starts → Create 5 connections (pool)
Request 1 → Borrow from pool → Query → Return to pool
Request 2 → Borrow from pool → Query → Return to pool
(Connections already exist, instant!)
```

**Parameters:**
- `pool_size=5`: Keep 5 connections ready
- `max_overflow=10`: Allow 10 extra when pool is full
- `pool_pre_ping=True`: Check connection is alive before using

---

## Q7: Soft Delete vs Hard Delete

**Hard Delete:**
```sql
DELETE FROM users WHERE user_id = 'xxx'
```
- Data gone forever
- Cascade deletes children
- Can't recover

**Soft Delete:**
```sql
UPDATE users SET is_active = false WHERE user_id = 'xxx'
```
- Data preserved
- Can recover/audit
- Filter in queries: `WHERE is_active = true`

**When to use:**
- Soft delete: Users, orders, anything with history value
- Hard delete: Temporary data, logs cleanup, GDPR "right to be forgotten"
