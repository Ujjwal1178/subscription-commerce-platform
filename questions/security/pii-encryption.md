# PII Encryption - Why and How?

## The Question
> "How do you store sensitive user data like email and phone number?"

## Quick Answer
**Never store PII in plain text. Encrypt + Hash.**

---

## What is PII?

**Personally Identifiable Information:**
- Email address
- Phone number
- Physical address
- Government IDs
- Credit card numbers

---

## The Problem

```
Database breach happens (it's not IF, it's WHEN)

Plain text storage:
| user_id | email              | phone        |
| usr_123 | ujjwal@gmail.com   | 9876543210   |

Attacker gets EVERYTHING. Can sell data, phish users, etc.
```

---

## The Solution: Encrypt + Hash

```
| user_id | email_encrypted      | email_hash    | phone_encrypted    | phone_hash  |
| usr_123 | aGVsbG8gd29ybGQ=... | sha256(email) | YmFzZTY0IGVuYy4=.. | sha256(phone)|
```

**Two fields per PII:**

1. **Encrypted value** (AES-256 with secret key)
   - For displaying back to user
   - Decrypt when needed

2. **Hash value** (SHA-256, one-way)
   - For searching/lookup
   - `WHERE email_hash = sha256('ujjwal@gmail.com')`
   - Can't reverse hash to get email

---

## Why Both?

| Operation | Use |
|-----------|-----|
| "Find user by email" | Search by `email_hash` (fast, indexed) |
| "Show user their email" | Decrypt `email_encrypted` |
| "Data breach" | Attacker gets encrypted gibberish + useless hashes |

---

## Code Example (Conceptual)

```python
# On registration
email_encrypted = aes_encrypt(email, SECRET_KEY)
email_hash = sha256(email.lower())  # lowercase for consistent hashing

# On login (find user)
input_hash = sha256(input_email.lower())
user = db.query("SELECT * FROM users WHERE email_hash = ?", input_hash)

# On profile view (show email)
decrypted_email = aes_decrypt(user.email_encrypted, SECRET_KEY)
```

---

## Interview Answer

> "We follow PII encryption best practices. Sensitive data like email and phone are stored encrypted using AES-256 with a secret key managed through environment variables or a secrets manager. 
>
> For lookups, we store a SHA-256 hash alongside the encrypted value. This allows us to search by email without decrypting every row, while ensuring that even if the database is compromised, attackers only get encrypted data they can't use.
>
> This is similar to how companies like Apple handle user data - encrypt at rest, minimize plain text exposure."

---

## Follow-up: Where to store the secret key?

**Never in code or database!**

Options:
- Environment variables (basic)
- AWS Secrets Manager / HashiCorp Vault (production)
- Hardware Security Module (HSM) for high security

---

## Key Takeaway

> **Assume breach will happen. Design so breach is useless.**
