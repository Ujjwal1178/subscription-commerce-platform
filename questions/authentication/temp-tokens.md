# Temporary Tokens - Purpose and Design

## Question
**"What are temporary tokens? When would you use them instead of regular JWT?"**

---

## What is a Temp Token?

A short-lived, restricted-purpose JWT used for specific one-time operations.

```python
# Regular Access Token
{
    "user_id": "uuid",
    "type": "access",
    "exp": 7 minutes,
    "device_id": "...",
    "user_name": "..."  # Has full user context
}

# Temp Token (Password Reset)
{
    "user_id": "uuid",
    "type": "password_reset",  # DIFFERENT type
    "exp": 10 minutes          # Short-lived
    # NO device_id, NO user_name - minimal data
}
```

---

## Why Not Just Use Access Token?

**Problem:** If we use access token for password reset:
```
User is logged in → Access token valid
User resets password → Still using same access token
Attacker has old access token → Can still access account!
```

**Solution:** Temp token is:
- **Different type** - Backend checks `type == "password_reset"`
- **Minimal scope** - Only allows password reset endpoint
- **No session** - Doesn't create/extend any session

---

## Use Cases for Temp Tokens

| Scenario | Token Type | Expiry | Purpose |
|----------|------------|--------|---------|
| Password Reset | `password_reset` | 10 min | One-time password change |
| Email Change | `email_change` | 15 min | Verify new email |
| Account Deletion | `account_delete` | 5 min | Confirm dangerous action |
| 2FA Setup | `2fa_setup` | 5 min | Complete 2FA enrollment |

---

## Implementation

```python
# Create temp token
def create_password_reset_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "type": "password_reset",  # Restricted type
        "exp": datetime.utcnow() + timedelta(minutes=10),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Verify temp token
def verify_password_reset_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    
    # TYPE CHECK - Critical!
    if payload.get("type") != "password_reset":
        raise ValueError("Invalid token type")
    
    return payload
```

---

## Security Benefits

1. **Type Isolation** - Access token can't be used for reset
2. **Short Expiry** - Reduces window of attack
3. **One-Time Use** - Token/OTP invalidated after use
4. **Minimal Data** - No unnecessary claims
5. **No Session Impact** - Doesn't affect login state

---

## Interview Answer

> "I use temporary tokens for sensitive one-time operations like password reset. They're different from access tokens in three ways:
> 
> 1. **Type field** - Token type is checked (`password_reset` vs `access`)
> 2. **Short expiry** - 10 minutes vs 7 minutes for access
> 3. **Minimal scope** - Only works for the specific operation
> 
> This prevents an attacker from using a stolen access token to reset passwords, or using a reset token to access the API."

---

## Code Reference
- File: `shared/utils/jwt.py`
- Functions: `create_password_reset_token()`, `verify_password_reset_token()`
- Token type enum: `TokenType.PASSWORD_RESET`
