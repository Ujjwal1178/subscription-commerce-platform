# SQLAlchemy Internals - Interview Questions

## Q1: How does `db.add(user)` know which table to insert into?

**Answer:**

SQLAlchemy reads the **class definition** of the object.

```python
class User(Base):
    __tablename__ = "users"  # ← TABLE NAME
    user_name = Column(String)  # ← COLUMN MAPPING
```

**When you do:**
```python
user = User(user_name="Ujjwal")
db.add(user)
```

**Internally:**
```python
# SQLAlchemy checks:
type(user)              # → User class
User.__tablename__      # → "users"
User.__table__.columns  # → [user_id, user_name, email_hash, ...]

# Now it knows: INSERT INTO users (...)
```

**Key point:** The `User(...)` object carries metadata about its table through the class definition.

---

## Q2: What's the difference between `db.flush()` and `db.commit()`?

**Answer:**

| Method | What it does | Transaction |
|--------|--------------|-------------|
| `flush()` | Sends SQL to database | ❌ Still OPEN |
| `commit()` | Makes changes permanent | ✅ CLOSED |

**flush() = Execute SQL but keep transaction open:**
```python
user = User(user_name="Ujjwal")
db.add(user)
db.flush()  # SQL runs, user_id generated
            # But can still ROLLBACK!
print(user.user_id)  # ← Available now!
```

**commit() = Finalize everything:**
```python
db.commit()  # Transaction closed
             # Changes are PERMANENT
             # Cannot rollback
```

**Use case:**
```python
db.add(user)
db.flush()           # Get user.user_id
otp = OTP(user_id=user.user_id)  # Need user_id here!
db.add(otp)
db.commit()          # Both saved together
                     # If OTP fails, user also rolls back!
```

---

## Q3: How does `relationship()` work internally?

**Answer:**

`relationship()` is a **lazy query shortcut**.

**Definition:**
```python
class User(Base):
    sessions = relationship("UserSession", back_populates="user")
```

**This tells SQLAlchemy:**
> "When someone accesses `user.sessions`, run a query on UserSession table matching user_id"

**What happens when you access `user.sessions`:**
```python
user = db.query(User).first()
user.sessions  # ← This line triggers internal query

# Internally SQLAlchemy does:
# 1. Check: "sessions" is a relationship to "UserSession"
# 2. Check: UserSession has ForeignKey to users.user_id
# 3. Generate: SELECT * FROM user_sessions WHERE user_id = {user.user_id}
# 4. Execute query
# 5. Convert rows to UserSession objects
# 6. Return list of objects
```

**Without relationship (manual way):**
```python
sessions = db.query(UserSession).filter(UserSession.user_id == user.user_id).all()
```

**With relationship (automatic):**
```python
sessions = user.sessions  # Same result, less code!
```

---

## Q4: What is `back_populates` in relationship?

**Answer:**

`back_populates` creates **two-way navigation** between related models.

```python
# In User model:
sessions = relationship("UserSession", back_populates="user")

# In UserSession model:
user = relationship("User", back_populates="sessions")
```

**Now you can navigate BOTH directions:**
```python
# User → Sessions
user = db.query(User).first()
print(user.sessions)  # [Session1, Session2]

# Session → User
session = db.query(UserSession).first()
print(session.user)  # User object
print(session.user.user_name)  # "Ujjwal"
```

**Without back_populates:** Only one-way navigation works.

---

## Q5: What is ForeignKey vs relationship?

**Answer:**

| Concept | Level | Purpose |
|---------|-------|---------|
| **ForeignKey** | Database | Creates actual link in DB, enforces constraint |
| **relationship()** | Python/ORM | Makes navigation easy in code |

**ForeignKey (in UserSession):**
```python
user_id = Column(UUID, ForeignKey("users.user_id"))
# This creates DB constraint:
# user_id MUST exist in users table
```

**relationship() (in User):**
```python
sessions = relationship("UserSession")
# This creates Python shortcut:
# user.sessions auto-queries UserSession table
```

**You need BOTH:**
- ForeignKey = Database knows the link
- relationship() = Python code is cleaner

---

## Q6: What is `cascade="all, delete-orphan"`?

**Answer:**

Cascade defines what happens to children when parent changes.

```python
sessions = relationship("UserSession", cascade="all, delete-orphan")
```

| Cascade Option | What it does |
|----------------|--------------|
| `all` | All operations cascade (save, update, delete) |
| `delete-orphan` | Delete child if removed from parent's collection |

**Example:**
```python
user = db.query(User).first()

# With cascade="all, delete-orphan":
db.delete(user)  # Automatically deletes all user's sessions too!

# Without cascade:
db.delete(user)  # Error! Sessions still reference this user
```

---

## Q7: How does SQLAlchemy generate SQL from Python objects?

**Answer:**

SQLAlchemy uses **metadata** from model classes.

**Step-by-step:**
```python
user = User(user_name="Ujjwal", email_hash="abc123")
db.add(user)
db.flush()
```

**Internal process:**
```
1. db.add(user)
   → SQLAlchemy marks object as "pending insert"
   → Stores in session's internal list

2. db.flush()
   → Loops through pending objects
   → For each object:
      a. Get class: User
      b. Get table: User.__tablename__ = "users"
      c. Get columns: User.__table__.columns
      d. Get values from object attributes
      e. Check for defaults (uuid, timestamp)
      f. Generate SQL:
         INSERT INTO users (user_id, user_name, email_hash, created_at)
         VALUES ('uuid', 'Ujjwal', 'abc123', 'now')
      g. Execute SQL
      h. Get returned values (like auto-generated ID)
      i. Update Python object with returned values
```

---

## Q8: What is "lazy loading" in relationships?

**Answer:**

Lazy loading = Query runs ONLY when you access the attribute.

```python
user = db.query(User).first()  # Only SELECT from users table

# At this point, sessions NOT loaded yet!

print(user.sessions)  # NOW the sessions query runs
                      # SELECT * FROM user_sessions WHERE user_id = ...
```

**Other loading strategies:**
```python
# Eager loading - load sessions WITH user in one query
sessions = relationship("UserSession", lazy="joined")

# user = db.query(User).first()
# This does JOIN and loads sessions immediately
```

---

## Follow-up Questions:

1. "What's the difference between `lazy='select'` and `lazy='joined'`?"
   → select = separate query when accessed (default)
   → joined = JOIN in same query, loads immediately

2. "How to see what SQL SQLAlchemy generates?"
   → Set `echo=True` in create_engine(), or use logging

3. "What happens if you forget ForeignKey but have relationship?"
   → Error! SQLAlchemy won't know how to join tables
