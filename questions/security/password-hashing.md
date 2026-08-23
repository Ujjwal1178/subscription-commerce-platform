# Password Hashing - Interview Questions

## Q1: Why use bcrypt instead of SHA256 for passwords?

**Answer:**

| Aspect | SHA256 | bcrypt |
|--------|--------|--------|
| **Speed** | ~1 million hashes/sec | ~100 hashes/sec |
| **Purpose** | Data integrity, lookups | Password hashing |
| **Salt** | No built-in | Built-in random salt |
| **Cost factor** | Fixed | Adjustable difficulty |

**Problem with SHA256:**
```
Attacker has leaked database
SHA256 is FAST → 1 million guesses/second
Common password cracked in SECONDS
```

**bcrypt solution:**
```
bcrypt is intentionally SLOW
100 hashes/second
Same attack takes HOURS instead of seconds
```

**Key insight:** For passwords, SLOW is a FEATURE, not a bug.

---

## Q2: What is Salt in password hashing?

**Answer:**

Salt = Random string added to password before hashing.

**Without salt:**
```
User1: password123 → hash("password123") = "abc123"
User2: password123 → hash("password123") = "abc123"  ← SAME!

Attacker: "If I crack one, I crack all users with same password!"
```

**With salt:**
```
User1: password123 + "random1" → hash("password123random1") = "xyz789"
User2: password123 + "random2" → hash("password123random2") = "def456"  ← DIFFERENT!

Attacker: "Even same passwords have different hashes. Must crack each separately."
```

**bcrypt auto-generates unique salt for each password!**

---

## Q3: What is a Rainbow Table attack? How does salt prevent it?

**Answer:**

**Rainbow Table:** Pre-computed table of hash → password mappings.

```
Attacker pre-computes:
hash("password") = "abc123"
hash("123456") = "def456"
hash("qwerty") = "ghi789"
... millions of common passwords

Then just looks up: "abc123" → "password" (instant crack!)
```

**Salt defeats this:**
```
With salt, attacker would need:
hash("password" + salt1) = ?
hash("password" + salt2) = ?
hash("password" + salt3) = ?
... for EVERY possible salt!

Rainbow table size becomes impractical (billions of entries per password)
```

---

## Q4: What is the "cost factor" in bcrypt?

**Answer:**

Cost factor (also called "rounds" or "work factor") controls how slow bcrypt is.

```python
bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
```

| Rounds | Iterations | Time per hash |
|--------|------------|---------------|
| 10 | 2^10 = 1,024 | ~100ms |
| 12 | 2^12 = 4,096 | ~300ms |
| 14 | 2^14 = 16,384 | ~1 second |

**Why adjustable?**
- Hardware gets faster every year
- Increase cost factor to maintain security
- Today: rounds=12 is recommended
- Future: May need rounds=14 or higher

**Trade-off:** Higher rounds = more secure but slower login.

---

## Q5: How does bcrypt verification work without storing the salt separately?

**Answer:**

bcrypt stores salt INSIDE the hash itself!

```
bcrypt hash format:
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qhJgWmNXPqu2a2
 │   │  │                                              │
 │   │  │                                              └── Hash
 │   │  └── Salt (22 characters)
 │   └── Cost factor (12)
 └── Algorithm version (2b)
```

**Verification:**
```python
# When user logs in:
stored_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qhJgWmNXPqu2a2"

# bcrypt extracts salt from stored_hash automatically
# Then: hash(input_password + extracted_salt) == stored_hash?

bcrypt.checkpw(input_password.encode(), stored_hash.encode())  # True/False
```

**No need to store salt separately!**

---

## Q6: bcrypt vs argon2 vs scrypt - Which to choose?

**Answer:**

| Algorithm | Memory Usage | Parallelism | Recommendation |
|-----------|--------------|-------------|----------------|
| **bcrypt** | Low | CPU only | Good, widely supported |
| **scrypt** | High (configurable) | CPU + Memory | Better against GPUs |
| **argon2** | High (configurable) | CPU + Memory + Parallelism | Best, winner of PHC |

**PHC = Password Hashing Competition (2015)**

**Recommendation:**
- New projects: argon2id (if library support available)
- Existing projects: bcrypt is still secure
- Avoid: MD5, SHA1, SHA256 (for passwords)

**Our choice:** bcrypt (widely supported, secure enough for most applications)

---

## Q7: What is "peppering"? How is it different from salt?

**Answer:**

| Aspect | Salt | Pepper |
|--------|------|--------|
| Storage | With hash in DB | In application config/secrets |
| Unique per user? | Yes | No, same for all users |
| If DB leaked | Attacker has salt | Attacker doesn't have pepper |

**Pepper adds extra layer:**
```python
# Salt: stored in DB with hash
# Pepper: stored in environment variable

hashed = bcrypt.hashpw((password + PEPPER).encode(), bcrypt.gensalt())
```

**Benefit:** Even if DB is leaked, attacker needs BOTH database AND application secrets.

**Downside:** If pepper is lost, ALL passwords become unverifiable.

---

## Q8: Code example - Password hashing with bcrypt

**Answer:**

```python
import bcrypt

# ----- HASHING (during registration) -----
def hash_password(plain_password: str) -> str:
    """
    Hash password using bcrypt.
    
    - Generates random salt automatically
    - Uses cost factor 12 (recommended)
    - Returns hash string to store in DB
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')  # Store as string in DB


# ----- VERIFICATION (during login) -----
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against stored hash.
    
    - Extracts salt from stored hash automatically
    - Returns True if match, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ----- USAGE -----
# Registration
stored_hash = hash_password("Secret@123")
# stored_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCO..."

# Login
is_valid = verify_password("Secret@123", stored_hash)  # True
is_valid = verify_password("wrong_password", stored_hash)  # False
```

---

## Q9: What happens if two users have the same password?

**Answer:**

**With bcrypt:** Different hashes!

```python
hash1 = bcrypt.hashpw(b"password123", bcrypt.gensalt())
hash2 = bcrypt.hashpw(b"password123", bcrypt.gensalt())

print(hash1)  # $2b$12$abc...xyz
print(hash2)  # $2b$12$def...uvw  ← DIFFERENT!
```

**Why?** Each call generates a NEW random salt.

**Security benefit:** Attacker can't tell if two users have the same password by looking at hashes.

---

## Q10: How to handle password hash migration (upgrading algorithm)?

**Answer:**

Scenario: Company decides to migrate from bcrypt (rounds=10) to argon2.

**Strategy: Lazy migration on login**

```python
def login(email: str, password: str):
    user = get_user_by_email(email)
    
    # Check if old algorithm
    if user.password_hash.startswith("$2b$10"):  # bcrypt rounds=10
        # Verify with old algorithm
        if bcrypt.checkpw(password, user.password_hash):
            # Re-hash with new algorithm
            user.password_hash = argon2.hash(password)
            save_user(user)
            return login_success()
    
    # New algorithm verification
    if argon2.verify(user.password_hash, password):
        return login_success()
    
    return login_failed()
```

**Benefit:** No downtime, gradual migration as users log in.

---

## Follow-up Questions:

1. "How do you handle users who never log in again after migration?"
   → Force password reset after X months, or accept legacy algorithm

2. "What's the maximum password length for bcrypt?"
   → 72 bytes. Longer passwords should be pre-hashed with SHA256.

3. "Should you hash passwords on client-side before sending?"
   → No, use HTTPS instead. Client-side hash becomes the "password" anyway.

4. "How often should you update the cost factor?"
   → Review every 1-2 years as hardware improves.
