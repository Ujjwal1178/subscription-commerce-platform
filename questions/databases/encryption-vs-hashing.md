# Encryption vs Hashing - Interview Questions

## Q1: Why can't you put UNIQUE constraint on encrypted columns?

**Answer:**
Proper encryption uses a random **IV (Initialization Vector)** for each encryption operation. This means:

```
Same plaintext + Same key + Different IV = Different ciphertext!
```

Example:
```
"9876543210" + key + IV1 = "abc123xyz..."
"9876543210" + key + IV2 = "def456uvw..."  ← Different!
```

So even if two users have the same phone number, their encrypted values will be different. UNIQUE constraint won't catch duplicates.

**Solution:** Use a hash column for uniqueness checks:
- `phone_hash` (SHA256) - for UNIQUE constraint and lookups
- `phone_encrypted` (AES) - for storing/displaying actual value

---

## Q2: Encryption vs Hashing - What's the difference?

| Aspect | Hashing | Encryption |
|--------|---------|------------|
| **Reversible?** | No (one-way) | Yes (two-way) |
| **Same input = Same output?** | Yes | No (with IV) |
| **Use case** | Passwords, lookups | Storing PII to display later |
| **Example** | SHA256, bcrypt | AES, RSA |

**Key insight:**
- Hash = "I need to verify, not see original"
- Encrypt = "I need to get original back"

---

## Q3: Why do we store both email_hash AND email_encrypted?

**Answer:**
```python
email_hash = Column(String(64), unique=True, index=True)  # For lookups
email_encrypted = Column(Text)  # For displaying
```

| Column | Purpose |
|--------|---------|
| `email_hash` | Fast O(log n) lookups via index, uniqueness check |
| `email_encrypted` | Decrypt when we need to show/send email |

**Login flow:**
1. User enters email
2. Hash the input: `sha256("user@email.com")`
3. Query: `WHERE email_hash = ?`
4. Found? → Decrypt `email_encrypted` if needed

---

## Q4: What is IV (Initialization Vector)? Why is it important?

**Answer:**
IV is a random value used with encryption key to ensure:
- Same plaintext encrypted twice gives different ciphertext
- Attackers can't detect patterns (if two users have same data)

**Without IV:**
```
User1 phone: "9876543210" → "encrypted_abc"
User2 phone: "9876543210" → "encrypted_abc"  ← Same! Attacker knows they match
```

**With IV:**
```
User1 phone: "9876543210" + IV1 → "encrypted_abc"
User2 phone: "9876543210" + IV2 → "encrypted_xyz"  ← Different!
```

**Storage:** IV is stored alongside ciphertext (it's not secret, just needs to be unique).

---

## Q5: If data breach happens, what's exposed?

| Storage Method | If DB Leaked |
|----------------|--------------|
| Plain text | Full data exposed |
| Only hashed | Can't reverse, but rainbow table attacks possible |
| Only encrypted | Need key to decrypt (safer if key is in secrets manager) |
| Hash + Encrypted | Best - can't reverse hash, can't decrypt without key |

**Our approach:**
- Email: hash (lookups) + encrypted (display)
- Phone: encrypted only (no frequent lookups)
- Password: hash only (never need original)

---

## Q6: Why bcrypt for passwords instead of SHA256?

**Answer:**

| Algorithm | Speed | Salt | Iterations |
|-----------|-------|------|------------|
| SHA256 | Very fast | No built-in | 1 |
| bcrypt | Intentionally slow | Built-in | Configurable |

**Problem with fast hashing:**
- Attacker can try billions of passwords/second
- Rainbow tables pre-compute common passwords

**bcrypt advantages:**
1. **Slow by design** - ~100ms per hash (limits brute force)
2. **Built-in salt** - Each password gets unique salt
3. **Cost factor** - Can increase work as hardware improves

```python
# bcrypt example
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
# rounds=12 means 2^12 = 4096 iterations
```

---

## Q7: Can we use encryption for passwords instead of hashing?

**Answer:** No! Bad practice.

**Why?**
1. If encryption key is compromised, ALL passwords are exposed
2. You should NEVER need to know the original password
3. Verify by: hash(input) == stored_hash

**Rule:** 
- Passwords → Always HASH (bcrypt, argon2)
- PII (email, phone) → ENCRYPT (need to display/send)

---

## Follow-up Questions Interviewer May Ask:

1. "How do you store the encryption key securely?" 
   → AWS Secrets Manager, HashiCorp Vault, environment variables (never in code)

2. "What if you need to change the encryption key?"
   → Key rotation: decrypt with old, re-encrypt with new, update in batch

3. "How do you handle searching encrypted data?"
   → You can't search encrypted data directly. Use hash for exact match, or consider searchable encryption (complex).

4. "What's the difference between symmetric and asymmetric encryption?"
   → Symmetric: same key encrypt/decrypt (AES)
   → Asymmetric: public key encrypt, private key decrypt (RSA)
