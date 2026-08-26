# Forgot Password Flow - Production Design

## Question
**"How did you design the forgot password flow? What edge cases did you handle?"**

---

## Our 3-Step Flow

```
Step 1: POST /forgot-password { email }
        → Send OTP (type: password_reset)
        
Step 2: POST /verify-reset-otp { email, otp }
        → Verify OTP → Return temp token (10 min)
        
Step 3: POST /reset-password { reset_token, new_password }
        → Verify temp token → Update password → Invalidate all sessions
```

---

## Why 3 Steps Instead of 2?

**2-Step (Bad):**
```
POST /forgot-password { email } → Send OTP
POST /reset-password { email, otp, new_password }
```

**Problem:** Anyone can try password reset by guessing OTPs repeatedly.

**3-Step (Good):**
- Step 2 returns a **temp token** after OTP verification
- Step 3 requires this token (not email+OTP)
- Token is **single-use** - OTP invalidated after verification
- Token is **short-lived** (10 minutes)
- Token can ONLY be used for password reset (type check)

---

## Edge Cases Handled

### 1. User Not Verified
```python
if not user.is_email_verified:
    return {
        "success": False,
        "message": "Please verify your email first",
        "requires_email_verification": True  # Frontend redirects
    }
```
User must verify email before resetting password.

### 2. User Blocked (OTP failures)
```python
if otp_record.is_user_blocked:
    # Check if block period passed
    if now < unblock_time:
        raise AppException("Try again in X minutes")
```
Block carries across all OTP flows (verification + reset).

### 3. User Enumeration Prevention
```python
# Same response for existing and non-existing emails
generic_message = "If the email is registered, you will receive an OTP."
```

### 4. OTP Reuse
```python
# If valid OTP exists and within cooldown
if existing_otp and not expired:
    return "OTP already sent"  # Don't generate new
```

### 5. Sessions Invalidation
```python
# After password reset, log out from ALL devices
db.query(UserSession).filter(
    user_id == user_id,
    is_session_active == True
).update({"is_session_active": False})
```

---

## Temp Token Design

```python
# Token payload
{
    "user_id": "uuid-123",
    "type": "password_reset",  # NOT "access" or "refresh"
    "exp": 10 minutes
}
```

**Security:**
- Different token type prevents use as access token
- Short expiry (10 min)
- No device_id (not a session)
- One-time use (OTP invalidated)

---

## Follow-up Questions

### Q1: "Why not send reset link instead of OTP?"
Both approaches work:
- **OTP:** User stays on same page, enters code
- **Link:** User clicks link in email, redirected to reset page

We chose OTP for:
- Consistency with email verification flow
- Works better for mobile apps (no browser redirect)
- Link can be shared/forwarded accidentally

### Q2: "What if user clicks forgot password multiple times?"
```python
# Reuse existing OTP if within cooldown (60 seconds)
if time_since_created < cooldown:
    return "OTP already sent"
```

### Q3: "Should we lock account after failed resets?"
Yes! Same blocking logic as email verification:
- 3 wrong OTPs → Block for 20 minutes
- Prevents brute force attacks

---

## Interview Answer Template

> "I designed a 3-step forgot password flow:
> 
> 1. **Request OTP** - User enters email, gets OTP
> 2. **Verify OTP** - Returns temporary reset token (10 min, restricted)
> 3. **Reset Password** - Uses temp token, not email+OTP
> 
> Key security features:
> - Temp token prevents OTP guessing attacks
> - Token is single-use and short-lived
> - All sessions invalidated after reset
> - Same blocking logic as verification (3 attempts)
> - Unverified users must verify email first
> - Generic responses prevent user enumeration"

---

## Code Reference
- File: `backend/services/auth_service/app/services/auth_service.py`
- Methods: `forgot_password()`, `verify_reset_otp()`, `reset_password()`
- JWT: `shared/utils/jwt.py` - `create_password_reset_token()`
