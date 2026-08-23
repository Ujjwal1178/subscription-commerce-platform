# Auth Service - API Documentation

> **Base URL:** `/api/v1/auth`

---

## API List

| # | Method | Endpoint | Auth Required | Status |
|---|--------|----------|---------------|--------|
| 1 | POST | /register | ❌ | ✅ Designed |
| 2 | POST | /login | ❌ | ✅ Designed |
| 3 | POST | /logout | ✅ | ✅ Designed |
| 4 | POST | /verify-email | ❌ | ✅ Designed |
| 5 | POST | /resend-otp | ❌ | ✅ Designed |
| 6 | POST | /refresh | ❌ | ✅ Designed |
| 7 | POST | /forgot-password | ❌ | ✅ Designed |
| 8 | POST | /reset-password | ❌ | ✅ Designed |
| 9 | GET | /profile/me | ✅ | ✅ Designed |
| 10 | PUT | /profile/me | ✅ | ✅ Designed |
| 11 | POST | /lookup | ❌ | 📝 Future (Multi-region) |

---

## Security Notes

- **PII Encryption:** Email and phone stored encrypted + hashed for lookup
- **Rate Limiting:** Applied on OTP endpoints
- **Attempt Limiting:** Max 3 wrong OTP attempts → 20 min block

---

# API Details

---

## 1. Register

**Endpoint:** `POST /api/v1/auth/register`

**Description:** Create a new user account. Sends OTP to email for verification.

### Request

```json
{
  "full_name": "Ujjwal Thakur",
  "email": "ujjwal@gmail.com",
  "phone_number": "+919876543210",
  "password": "Secret@123"
}
```

### Validations

| Field | Rules |
|-------|-------|
| full_name | Required, min 5 characters |
| email | Required, valid email format, unique |
| phone_number | Required, valid phone format |
| password | Required, min 8 chars, 1 uppercase, 1 special char, 1 number |

### Response - Success (201 Created)

```json
{
  "success": true,
  "message": "Registration successful. Please verify your email.",
  "user_id": "usr_abc123"
}
```

### Response - Email Exists (409 Conflict)

```json
{
  "success": false,
  "message": "Email already registered"
}
```

### Response - Validation Error (400 Bad Request)

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    {
      "field": "password",
      "message": "Password must contain at least 1 special character"
    }
  ]
}
```

### Flow

```
1. Validate input fields
2. Check if email already exists (by email_hash)
3. Hash password (bcrypt)
4. Encrypt email & phone, generate hashes
5. Create user record (email_verified = false)
6. Generate OTP (6 digits)
7. Store OTP with expiry (10 min)
8. Send OTP to email
9. Return success response
```

### Notes

- User cannot login until email is verified
- OTP valid for 10 minutes
- Tokens (access/refresh) are given only after email verification

---

## 2. Login

**Endpoint:** `POST /api/v1/auth/login`

**Description:** Authenticate user and get access/refresh tokens.

### Request

```json
{
  "email": "ujjwal@gmail.com",
  "password": "Secret@123",
  "device_name": "Chrome on Windows"
}
```

| Field | Rules |
|-------|-------|
| email | Required |
| password | Required |
| device_name | Optional (for login history display) |

### Response - Success (200 OK)

```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 420
}
```

### Response - Invalid Credentials (401 Unauthorized)

```json
{
  "success": false,
  "message": "Invalid email or password"
}
```

### Response - Email Not Verified (403 Forbidden)

```json
{
  "success": false,
  "message": "Email not verified",
  "action": "verify_email",
  "email": "ujjwal@gmail.com"
}
```

*Note: OTP auto-sent to email (rate limited: max 3 per 10 min)*

### Flow

```
1. Validate input
2. Find user by email_hash
3. If not found → "Invalid email or password"
4. Check password hash (bcrypt verify)
5. If wrong → "Invalid email or password"
6. Check email_verified
7. If not verified → Send OTP (if not rate limited), return 403
8. Generate device_id
9. Delete old device sessions (single device policy)
10. Create new session (device_id, device_name)
11. Generate access_token (7 min) with device_id
12. Generate refresh_token (2 hr) with device_id
13. Return tokens
```

### Security

- Same error message for wrong email/password (prevents enumeration)
- Single device login: old sessions deleted on new login
- Rate limiting on OTP sending

---

## 3. Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Description:** End user session. Supports single device or all devices logout.

### Request

**Header:** `Authorization: Bearer <access_token>`

**Body (optional):**
```json
{
  "device_id": "dev_abc123"
}
```

| Field | Rules |
|-------|-------|
| device_id | Optional. If provided, logout specific device. If not, logout all devices. |

### Response - Success (200 OK)

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### Response - Unauthorized (401)

```json
{
  "success": false,
  "message": "Invalid or expired token"
}
```

### Flow

```
1. Validate access_token from header
2. Extract user_id from token
3. If device_id provided:
   - Soft delete that session (is_active = false, ended_at = now)
4. If no device_id:
   - Soft delete ALL sessions for user
5. Return success
```

### Notes

- **Soft delete:** Sessions are not hard deleted, marked `is_active = false`
- **Login history:** User can see last 30 days of login history
- **Cleanup job:** Daily job deletes sessions older than 30 days

---

## 4. Verify Email

**Endpoint:** `POST /api/v1/auth/verify-email`

**Description:** Verify user's email with OTP. On success, returns tokens (same as login).

### Request

```json
{
  "email": "ujjwal@gmail.com",
  "otp": "123456",
  "device_name": "Chrome on Windows"
}
```

| Field | Rules |
|-------|-------|
| email | Required |
| otp | Required, 6 digits |
| device_name | Optional |

### Response - Success (200 OK)

```json
{
  "success": true,
  "message": "Email verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 420
}
```

### Response - Wrong OTP (400 Bad Request)

```json
{
  "success": false,
  "message": "Invalid OTP. Attempts remaining: 2"
}
```

### Response - Last Attempt Warning (400 Bad Request)

```json
{
  "success": false,
  "message": "Invalid OTP. Careful! 1 attempt remaining. After that, wait 20 minutes."
}
```

### Response - Blocked (429 Too Many Requests)

```json
{
  "success": false,
  "message": "Too many failed attempts. Try again after 20 minutes.",
  "retry_after": 1200
}
```

### Flow

```
1. Find user by email_hash
2. Check if blocked (3 failed attempts in last 20 min)
3. If blocked → return 429
4. Verify OTP matches and not expired (10 min validity)
5. If wrong OTP:
   - Increment attempt count
   - Return remaining attempts
6. If correct OTP:
   - Set email_verified = true
   - Reset attempt count
   - Create session (device_id, device_name)
   - Generate tokens
   - Return tokens (same as login response)
```

### Security

- Max 3 attempts per 20 minutes
- OTP expires in 10 minutes
- After 3 wrong attempts → 20 min block

---

## 5. Resend OTP

**Endpoint:** `POST /api/v1/auth/resend-otp`

**Description:** Resend OTP for email verification (not for password reset).

### Request

```json
{
  "email": "ujjwal@gmail.com"
}
```

| Field | Rules |
|-------|-------|
| email | Required |

### Response - Success (200 OK)

```json
{
  "success": true,
  "message": "OTP sent successfully"
}
```

### Response - Rate Limited (429 Too Many Requests)

```json
{
  "success": false,
  "message": "Too many requests. Try again after 10 minutes.",
  "retry_after": 600
}
```

### Response - Already Verified (400 Bad Request)

```json
{
  "success": false,
  "message": "Email already verified"
}
```

### Flow

```
1. Find user by email_hash
2. If not found → return success (don't reveal email doesn't exist)
3. If email already verified → return "already verified"
4. Check rate limit (max 3 per 10 min)
5. If rate limited → return 429
6. Generate new OTP (invalidate old one)
7. Send OTP to email
8. Return success
```

### Security

- Max 3 OTPs per email per 10 minutes
- Old OTP invalidated when new one sent
- Generic success for non-existent email (prevents enumeration)

---

## 6. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Description:** Get new access token using refresh token.

### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

| Field | Rules |
|-------|-------|
| refresh_token | Required |

### Response - Success (200 OK)

```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 420
}
```

### Response - Expired/Invalid (401 Unauthorized)

```json
{
  "success": false,
  "message": "Session expired. Please login again."
}
```

### Flow

```
1. Verify refresh_token signature
2. Extract user_id, device_id from token
3. Check token not expired
4. Check session exists in DB (device_id, is_active = true)
5. If any check fails:
   - Soft delete session (is_active = false, ended_at = now)
   - Return 401
6. If all valid:
   - Update session last_active timestamp
   - Generate new access_token
   - Return access_token
```

### Notes

- Only returns new access_token (not new refresh_token)
- Session is soft-deleted on invalid/expired refresh attempt
- `device_id` is extracted from refresh_token JWT, not from request body

---

## 7. Forgot Password

**Endpoint:** `POST /api/v1/auth/forgot-password`

**Description:** Request password reset OTP. Sends OTP to email.

### Request

```json
{
  "email": "ujjwal@gmail.com"
}
```

| Field | Rules |
|-------|-------|
| email | Required |

### Response - Success (200 OK)

```json
{
  "success": true,
  "message": "If email exists, OTP has been sent"
}
```

### Response - Rate Limited (429 Too Many Requests)

```json
{
  "success": false,
  "message": "Too many requests. Try again after 10 minutes.",
  "retry_after": 600
}
```

### Flow

```
1. Find user by email_hash
2. If not found → return success anyway (don't reveal)
3. Check rate limit (max 3 per 10 min)
4. If rate limited → return 429
5. Generate OTP for password reset
6. Send OTP to email
7. Return success
```

### Security

- Generic success message (prevents email enumeration)
- Max 3 requests per email per 10 minutes
- OTP valid for 10 minutes

---

## 8. Reset Password

**Endpoint:** `POST /api/v1/auth/reset-password`

**Description:** Reset password using OTP. Logs out all devices and returns new tokens.

### Request

```json
{
  "email": "ujjwal@gmail.com",
  "otp": "123456",
  "new_password": "NewSecret@123",
  "device_name": "Chrome on Windows"
}
```

| Field | Rules |
|-------|-------|
| email | Required |
| otp | Required, 6 digits |
| new_password | Required, min 8 chars, 1 uppercase, 1 special char, 1 number |
| device_name | Optional |

### Response - Success (200 OK)

```json
{
  "success": true,
  "message": "Password reset successful",
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 420
}
```

### Response - Wrong OTP (400 Bad Request)

```json
{
  "success": false,
  "message": "Invalid OTP. Attempts remaining: 2"
}
```

### Response - Blocked (429 Too Many Requests)

```json
{
  "success": false,
  "message": "Too many failed attempts. Try again after 20 minutes.",
  "retry_after": 1200
}
```

### Flow

```
1. Find user by email_hash
2. Check if blocked (3 failed attempts in last 20 min)
3. Verify OTP matches and not expired
4. If wrong OTP → increment attempts, return error
5. If correct OTP:
   - Update password hash
   - Soft delete ALL sessions (logout everywhere)
   - Create new session for current device
   - Generate new tokens
   - Return tokens
```

### Security

- Max 3 OTP attempts per 20 minutes
- All existing sessions terminated on password reset
- New session created for current device only

---

## 9. Get Profile

**Endpoint:** `GET /api/v1/auth/profile/me`

**Description:** Get current logged-in user's profile.

### Request

**Header:** `Authorization: Bearer <access_token>`

No body required.

### Response - Success (200 OK)

```json
{
  "success": true,
  "user": {
    "user_id": "usr_abc123",
    "full_name": "Ujjwal Thakur",
    "email": "ujjwal@gmail.com",
    "phone_number": "+919876543210",
    "email_verified": true,
    "created_at": "2026-08-23T10:00:00Z",
    "subscription": {
      "plan_name": "Pro",
      "features": ["feature1", "feature2"]
    }
  }
}
```

*Note: Subscription details will be added when we build subscription service*

### Response - Unauthorized (401)

```json
{
  "success": false,
  "message": "Invalid or expired token"
}
```

### Flow

```
1. Validate access_token
2. Extract user_id from token
3. Fetch user data (decrypt email, phone)
4. Fetch subscription data (from subscription service - later)
5. Return user profile
```

---

## 10. Update Profile

**Endpoint:** `PUT /api/v1/auth/profile/me`

**Description:** Update current user's profile (name, phone only).

### Request

**Header:** `Authorization: Bearer <access_token>`

```json
{
  "full_name": "Ujjwal Kumar Thakur",
  "phone_number": "+919876543211"
}
```

| Field | Rules |
|-------|-------|
| full_name | Optional, min 5 characters |
| phone_number | Optional, valid phone format |

*Note: Email cannot be updated (requires re-verification flow - future feature)*

### Response - Success (200 OK)

```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "user_id": "usr_abc123",
    "full_name": "Ujjwal Kumar Thakur",
    "phone_number": "+919876543211"
  }
}
```

### Response - Validation Error (400)

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    {
      "field": "full_name",
      "message": "Name must be at least 5 characters"
    }
  ]
}
```

### Flow

```
1. Validate access_token
2. Extract user_id from token
3. Validate input fields
4. Update user data (encrypt phone if changed)
5. Return updated profile
```

---

## 11. Lookup (Future)

📝 *Multi-region feature - Document only, not implementing now*

**Purpose:** Check if user exists and in which region, for multi-region deployments.

**Use case:** When we have users in multiple regions (IN, US, EU), this API checks global table and returns which region's API to hit.

---
