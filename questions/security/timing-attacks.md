# Timing Attacks - Interview Questions

## Q1: What is a Timing Attack?

**Answer:**

A timing attack exploits the **time difference** in operations to extract sensitive information.

**Example with string comparison:**

```python
# Normal == comparison (vulnerable)
"abc123" == "abc999"
   ↓
'a' == 'a' ✅ continue (1ms)
'b' == 'b' ✅ continue (1ms)
'c' == 'c' ✅ continue (1ms)
'1' == '9' ❌ STOP! (total: 4ms)

"abc123" == "xyz999"
   ↓
'a' == 'x' ❌ STOP! (total: 1ms)
```

**Attacker measures response time:**
```
Input "a00000" → 50ms response (first char matched!)
Input "b00000" → 45ms response (faster = no match)
Input "ab0000" → 55ms response (two chars matched!)
...slowly guesses entire secret!
```

---

## Q2: How to prevent Timing Attacks?

**Answer:**

Use **constant-time comparison** - always takes same time regardless of input.

```python
# VULNERABLE (variable time):
if user_input == secret:
    return True

# SAFE (constant time):
import secrets
if secrets.compare_digest(user_input, secret):
    return True
```

**How `compare_digest` works:**
- Always compares ALL characters
- Uses XOR bitwise operation
- Same time whether match or no match
- Attacker learns nothing from timing

---

## Q3: Where are Timing Attacks applicable?

**Answer:**

Any comparison of sensitive data:

| Scenario | Vulnerable Code | Safe Code |
|----------|-----------------|-----------|
| OTP verification | `otp == stored_otp` | `secrets.compare_digest()` |
| API key check | `key == api_key` | `secrets.compare_digest()` |
| Token validation | `token == valid_token` | `secrets.compare_digest()` |
| Password hash compare | `hash1 == hash2` | `hmac.compare_digest()` |

**Note:** bcrypt's `checkpw()` is already constant-time internally.

---

## Q4: Code example - Safe OTP verification

**Answer:**

```python
import secrets
import hashlib

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

def verify_otp(input_otp: str, stored_hash: str) -> bool:
    """
    Constant-time OTP verification.
    
    Even if attacker measures timing:
    - Correct OTP: 5ms
    - Wrong OTP: 5ms  (same!)
    
    No information leaked!
    """
    input_hash = hash_otp(input_otp)
    return secrets.compare_digest(input_hash, stored_hash)
```

---

## Q5: Why not just add random delay to prevent timing attacks?

**Answer:**

```python
# Bad solution - adding random delay
import random
import time

def check_secret(input, secret):
    result = (input == secret)
    time.sleep(random.uniform(0.01, 0.05))  # Random delay
    return result
```

**Problems:**
1. Statistical analysis can still extract timing (average over many requests)
2. Adds latency to ALL requests
3. Not a real fix, just obscuring the problem

**Correct solution:** Use constant-time comparison from the start.

---

## Q6: What is a Side-Channel Attack?

**Answer:**

Timing attack is one type of **side-channel attack**.

Side-channel = Extracting information from physical implementation, not algorithm itself.

| Side-Channel Type | What it Exploits |
|-------------------|------------------|
| **Timing** | Time taken for operations |
| **Power analysis** | Power consumption patterns |
| **Electromagnetic** | EM radiation from CPU |
| **Cache** | CPU cache hit/miss patterns |
| **Acoustic** | Sound from hardware |

**Software developers mainly worry about timing attacks.**

---

## Follow-up Questions:

1. "Is HTTPS enough to prevent timing attacks?"
   → No, attacker measures server response time, not network

2. "Do all crypto libraries use constant-time operations?"
   → Good ones do, always use well-known libraries (cryptography, bcrypt)

3. "Can timing attacks work over the internet?"
   → Yes, but need many requests to average out network noise
