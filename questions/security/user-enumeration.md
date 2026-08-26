# User Enumeration Attack - Prevention

## Question
**"How do you prevent user enumeration attacks in your authentication system?"**

---

## What is User Enumeration?

User enumeration is when an attacker can determine whether a specific email/username exists in your system by observing different responses.

### Example of VULNERABLE code:

```python
# BAD - Attacker can tell if email exists
if not user:
    return {"message": "Email not found"}  # Different response!
else:
    return {"message": "OTP sent to your email"}
```

**Attack scenario:**
1. Attacker tries `admin@company.com` → "Email not found"
2. Attacker tries `ceo@company.com` → "OTP sent to your email" 
3. Attacker now knows CEO's email exists! Can target with phishing.

---

## Our Implementation (SECURE)

```python
# GOOD - Same response for both cases
generic_message = "If the email is registered, a new OTP will be sent."

if not user:
    # User doesn't exist - but return SAME response
    return ResendOTPResponse(
        success=True,
        message=generic_message,
        masked_email=mask_email(email),
        otp_expires_in=600,
        can_resend_in=60,  # SAME fields as real response!
    )

# User exists - generate OTP
otp = generate_otp()
return ResendOTPResponse(
    success=True,
    message=generic_message,  # SAME message
    masked_email=mask_email(email),
    otp_expires_in=600,
    can_resend_in=60,
)
```

**Key points:**
- Same message for both cases
- Same fields in response (attacker can't detect missing fields)
- Same HTTP status code (200 for both)
- Only logs reveal the truth (for debugging)

---

## Where to Apply This?

| Endpoint | Vulnerable Response | Secure Response |
|----------|---------------------|-----------------|
| Login | "User not found" vs "Wrong password" | "Invalid email or password" |
| Forgot Password | "Email not registered" vs "Reset link sent" | "If registered, reset link will be sent" |
| Resend OTP | "User not found" vs "OTP sent" | "If registered, OTP will be sent" |
| Register | "Email already exists" | This one SHOULD tell! User needs to know |

**Note:** Registration is an exception - user legitimately needs to know if email is taken.

---

## Follow-up Questions

### Q1: "What about timing attacks?"
Even if responses are identical, if the existing user path takes 100ms and non-existing takes 10ms, attacker can measure!

**Solution:** Add artificial delay or use constant-time operations:
```python
# Always hash something (constant time)
_ = hash_password("dummy")  # Burn same CPU time
```

### Q2: "What about rate limiting?"
Even with identical responses, attacker can try millions of emails.

**Solution:** Rate limit by IP + global rate limit:
```python
# Our implementation
rate_result = check_rate_limit(
    action=RateLimitAction.OTP_RESEND,
    identifier=email,  # Per-email limit
    limit=3,
    window_seconds=600
)
```

### Q3: "Can attackers use the registration endpoint?"
Yes! Registration must tell if email exists. Mitigation:
- CAPTCHA on registration
- Rate limit registration attempts
- Monitor for bulk registration attempts

---

## Real-World Example

**Apple's Approach:**
- "If an Apple ID exists for this email, you will receive..."
- Never confirms or denies email existence
- Uses same response time for both cases

---

## Interview Answer Template

> "User enumeration is when attackers can determine if accounts exist by observing different API responses. I prevent this by:
> 
> 1. **Identical responses** - Same message, same fields, same status code for both existing and non-existing users
> 2. **Generic messages** - 'If the email is registered, you will receive...'
> 3. **Timing protection** - Constant-time operations to prevent timing attacks
> 4. **Rate limiting** - Prevent bulk enumeration attempts
> 5. **Logging** - Still log the real outcome for debugging, but don't expose to client
> 
> Exception: Registration endpoint must tell if email is taken, but we protect it with CAPTCHA and rate limiting."

---

## Code Reference
- File: `backend/services/auth_service/app/services/auth_service.py`
- Method: `resend_otp()`
- Similar pattern in: `login()`, `verify_otp()`
