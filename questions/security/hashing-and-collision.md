# Hashing & Collision - Interview Questions

## Q1: Why is hashing NOT reversible?

**Answer:**

Hashing intentionally **destroys information**.

**Analogy:**
```
Encryption = Locking a box with key → Can unlock with same key
Hashing = Grinding meat into keema → Can't get chicken back
```

**Technical reason:**
```
Infinite possible inputs → Fixed size output (256 bits for SHA256)

"a"                    → "ca978112..." (64 chars)
"ujjwal@gmail.com"     → "8f4e3d2a..." (64 chars)  
"very-long-text..."    → "1a2b3c4d..." (64 chars)

Information is LOST in compression!
```

---

## Q2: What is a Hash Collision?

**Answer:**

Collision = Two different inputs produce the SAME hash output.

```
hash("input1") = "abc123..."
hash("input2") = "abc123..."  ← SAME! Collision!
```

**Why possible?**
- Infinite inputs → Finite outputs
- Pigeonhole principle: If you have more pigeons than holes, some hole will have 2+ pigeons

---

## Q3: Is SHA256 collision a real risk?

**Answer:**

**Theoretically possible, practically impossible.**

```
SHA256 possible outputs = 2^256
                        = 115,792,089,237,316,195,423,570,985,008,687,907,853,269,984,665,640,564,039,457,584,007,913,129,639,936

Atoms in observable universe ≈ 10^80
SHA256 outputs ≈ 10^77
```

**Probability of collision:** 1 in 2^128 (birthday attack)

Finding SHA256 collision would require more computing power than exists on Earth. **No SHA256 collision has ever been found.**

---

## Q4: Which hashing algorithms have known collisions?

**Answer:**

| Algorithm | Output Size | Collision Found? | Recommendation |
|-----------|-------------|-----------------|----------------|
| MD5 | 128 bits | ✅ Yes (2004) | ❌ Never use |
| SHA1 | 160 bits | ✅ Yes (2017) | ❌ Don't use |
| SHA256 | 256 bits | ❌ Not found | ✅ Safe |
| SHA512 | 512 bits | ❌ Not found | ✅ Safe |
| SHA3-256 | 256 bits | ❌ Not found | ✅ Safe (newer) |

**Rule:** Always use SHA256 or better for security-critical applications.

---

## Q5: What is Birthday Attack?

**Answer:**

A method to find hash collisions faster than brute force.

**Birthday Paradox:**
- In a room of 23 people, probability of 2 sharing birthday > 50%
- You don't need 365 people!

**Applied to hashing:**
```
Brute force collision: Need ~2^256 attempts
Birthday attack: Need ~2^128 attempts (square root)
```

Still, 2^128 is astronomical - not practically achievable.

---

## Q6: If collision is possible, why use hashing for email lookup?

**Answer:**

**Probability is negligible.**

```
Your app has 1 million users = 10^6 emails
Collision probability with SHA256 ≈ 10^6 / 2^256 ≈ 0.0000....(70 zeros)...001%
```

**Also:**
- We store encrypted email too
- After hash lookup, we decrypt and verify actual email
- Double verification!

```python
# Lookup flow:
user = db.query(User).filter(User.email_hash == hash(input_email)).first()
actual_email = decrypt(user.email_encrypted)
if actual_email == input_email:  # Extra verification
    return user
```

---

## Q7: Encryption vs Hashing - When to use which?

**Answer:**

| Use Case | Use | Why |
|----------|-----|-----|
| Passwords | Hashing (bcrypt) | Never need original |
| Email storage | Encryption (AES) | Need to display/send |
| Email lookup | Hashing (SHA256) | Fast indexed search |
| File integrity | Hashing | Just verify, not decrypt |
| Secure data storage | Encryption | Need data back |

**Rule of thumb:**
- Need original back? → Encryption
- Just verify/compare? → Hashing

---

## Q8: What makes a hash function "cryptographically secure"?

**Answer:**

Three properties:

| Property | Meaning |
|----------|---------|
| **Pre-image resistance** | Given hash, can't find input |
| **Second pre-image resistance** | Given input1, can't find input2 with same hash |
| **Collision resistance** | Can't find ANY two inputs with same hash |

**MD5 and SHA1 failed collision resistance** → No longer secure.

---

## Q9: Code example - SHA256 hashing

**Answer:**

```python
import hashlib

def generate_hash(data: str) -> str:
    """
    Generate SHA256 hash of input data.
    
    Same input always gives same output.
    Used for lookups and verification.
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# Usage
email = "ujjwal@gmail.com"
email_hash = generate_hash(email)
# Always: "8f4e3d2a1b5c..." (same output for same input)

# Lookup in DB
user = db.query(User).filter(User.email_hash == email_hash).first()
```

---

## Follow-up Questions:

1. "How would quantum computers affect SHA256?"
   → Grover's algorithm could reduce security from 2^256 to 2^128, still safe for now

2. "What's the difference between SHA256 and SHA3-256?"
   → Different internal structure, SHA3 is newer (2015), both equally secure

3. "Why not just encrypt everything instead of hashing?"
   → Encryption is slower, needs key management, hashing is simpler for verification

4. "How do rainbow tables attack hashes?"
   → Pre-computed hash→password mappings. Defeated by salting (adding random data before hashing)
