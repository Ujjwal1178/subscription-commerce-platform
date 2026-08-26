# OTP Edge Cases - Production-Ready Implementation

## Question
**"What edge cases did you handle in your OTP system? How did you make it production-ready?"**

---

## Edge Cases We Handled

### 1. OTP Reuse (Don't Waste!)

**Problem:** User registers, gets OTP, closes tab, tries to login. Should we send NEW OTP?

**Bad approach:**
```python
# WASTEFUL - Always generates new OTP
def login(email, password):
    if not user.is_email_verified:
        otp = generate_otp()  # New OTP every time!
        send_otp_email(otp)   # Costs money (SMS/Email)
```

**Our approach:**
```python
# SMART - Reuse valid OTP
def login(email, password):
    if not user.is_email_verified:
        existing_otp = get_active_otp(user_id)
        
        if existing_otp and not expired(existing_otp):
            # Reuse existing OTP
            remaining = (existing_otp.expires_at - now()).seconds
            return {
                "message": "OTP already sent",
                "otp_expires_in": remaining  # Show countdown!
            }
        
        # Only generate new if none exists or expired
        otp = generate_otp()
```

**Benefits:**
- Saves SMS/Email cost (real money in production!)
- Better UX - user might have OTP open in another tab
- Frontend can show accurate countdown

---

### 2. Block Status Check

**Problem:** User is blocked for OTP verification. They try to login. What happens?

**Bad approach:**
```python
# BYPASSES BLOCK - Dangerous!
def login(email, password):
    if not user.is_email_verified:
        otp = generate_otp()  # Ignores block status!
        send_otp_email(otp)
```

**Our approach:**
```python
# CHECKS BLOCK STATUS
def login(email, password):
    if not user.is_email_verified:
        existing_otp = get_active_otp(user_id)
        
        if existing_otp and existing_otp.is_user_blocked:
            unblock_time = existing_otp.blocked_at + timedelta(minutes=20)
            if now() < unblock_time:
                remaining_mins = (unblock_time - now()).minutes
                raise AppException(
                    message=f"Too many failed attempts. Try in {remaining_mins} minutes",
                    error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                    status_code=403
                )
            else:
                # Block expired - unblock user
                existing_otp.is_user_blocked = False
                existing_otp.remaining_retry = 3
```

---

### 3. Resend Cooldown

**Problem:** User can spam resend button, generating thousands of OTPs.

**Our approach:**
```python
# 60 SECOND COOLDOWN
OTP_RESEND_COOLDOWN = 60  # seconds

def resend_otp(email):
    existing_otp = get_active_otp(user_id)
    
    if existing_otp:
        time_since_created = (now() - existing_otp.created_at).seconds
        
        if time_since_created < OTP_RESEND_COOLDOWN:
            wait_seconds = OTP_RESEND_COOLDOWN - time_since_created
            return {
                "success": False,
                "message": f"Wait {wait_seconds} seconds",
                "can_resend_in": wait_seconds
            }
    
    # Cooldown passed - generate new OTP
    otp = generate_otp()
```

**Plus Rate Limiting:**
```python
# Redis-based: 3 resends per 10 minutes
rate_result = check_rate_limit(
    action=RateLimitAction.OTP_RESEND,
    identifier=email,
    limit=3,
    window_seconds=600
)
```

---

### 4. Expiry Time in Response

**Problem:** Frontend needs to show countdown. Are we sending expiry time?

**Our approach:**
```python
# ALWAYS send remaining time
return LoginResponse(
    requires_otp=True,
    otp_expires_in=remaining_seconds,  # For countdown
    masked_email="uj****@gmail.com"    # For display
)
```

Frontend can show:
```
OTP sent to uj****@gmail.com
Expires in: 5:43
[Resend OTP] (disabled for 34 more seconds)
```

---

## Summary Table

| Edge Case | Bad Approach | Our Approach |
|-----------|--------------|--------------|
| Valid OTP exists | Generate new | Reuse, show remaining time |
| User blocked | Ignore, send OTP | Check block, return retry_after |
| Resend spam | No protection | 60s cooldown + rate limit |
| Expiry display | Don't send | Send `otp_expires_in` |
| User enumeration | Different messages | Identical responses |

---

## Follow-up Questions

### Q1: "Why 60 seconds cooldown?"
- Balances UX (not too long) vs spam protection
- User might genuinely not receive email (spam folder)
- Configurable via `OTP_RESEND_COOLDOWN` env var

### Q2: "Why reuse OTP instead of generating new?"
- Cost: SMS costs $0.01-0.05 per message. At scale = thousands of dollars
- Security: New OTP invalidates old one. User with old OTP open gets confused
- UX: Accurate countdown instead of "wait 10 mins" every time

### Q3: "How do you handle OTP for password reset vs email verification?"
```python
# Different verification_type
create_otp_record(user_id, otp, verification_type="email_verification")
create_otp_record(user_id, otp, verification_type="password_reset")

# Query by type - both can exist simultaneously
get_active_otp(user_id, verification_type="email_verification")
```

---

## Interview Answer Template

> "I handled several OTP edge cases to make the system production-ready:
> 
> 1. **OTP Reuse** - If user has valid OTP, I reuse it instead of generating new. Saves SMS/email cost and provides accurate expiry countdown.
> 
> 2. **Block Status** - Before sending OTP on login, I check if user is blocked from OTP verification. Prevents block bypass.
> 
> 3. **Resend Cooldown** - 60 second minimum between resends, plus rate limiting (3 per 10 minutes) to prevent spam.
> 
> 4. **Expiry Time** - Always return `otp_expires_in` so frontend can show countdown and `can_resend_in` for resend button state.
> 
> 5. **User Enumeration** - Same response whether email exists or not.
> 
> These edge cases are what separates a tutorial project from production-grade code."

---

## Code Reference
- File: `backend/services/auth_service/app/services/auth_service.py`
- Methods: `login()`, `resend_otp()`, `verify_otp()`
- Config: `backend/services/auth_service/app/config.py`
