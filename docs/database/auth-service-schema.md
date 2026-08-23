# Auth Service - Database Schema

## Database: auth_db

---

## Tables Overview

| Table | Purpose |
|-------|---------|
| users | User account data |
| user_sessions | Login sessions & device tracking |
| otp_verifications | OTP for email verification & password reset |

---

## 1. users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | PK | Unique user identifier |
| user_name | VARCHAR(100) | NOT NULL | Full name |
| email_hash | VARCHAR(64) | NOT NULL, UNIQUE, INDEX | SHA256 hash for lookup |
| email_encrypted | TEXT | NOT NULL | AES encrypted email |
| phone_encrypted | TEXT | NOT NULL | AES encrypted phone |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| is_email_verified | BOOLEAN | DEFAULT false | Email verification status |
| address | TEXT | NULL | User address (future) |
| pincode | VARCHAR(10) | NULL | Postal code (future) |
| preferences | JSONB | NULL | User preferences (theme, etc.) |
| created_at | TIMESTAMP | DEFAULT now() | Account creation time |
| updated_at | TIMESTAMP | DEFAULT now() | Last update time |

### Indexes
- `idx_users_email_hash` on `email_hash` (for login lookup)

---

## 2. user_sessions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| session_id | UUID | PK | Unique session identifier |
| user_id | UUID | FK → users.user_id | Reference to user |
| device_id | VARCHAR(50) | NOT NULL, UNIQUE | Device identifier (in JWT) |
| device_name | VARCHAR(100) | NULL | "Chrome on Windows" |
| is_session_active | BOOLEAN | DEFAULT true | Active or ended |
| session_started_at | TIMESTAMP | DEFAULT now() | Login time |
| session_ended_at | TIMESTAMP | NULL | Logout time |
| last_activity_at | TIMESTAMP | DEFAULT now() | Last refresh/activity |

### Indexes
- `idx_sessions_user_id` on `user_id` (for user's sessions)
- `idx_sessions_device_id` on `device_id` (for refresh token validation)

---

## 3. otp_verifications

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| otp_id | UUID | PK | Unique OTP record identifier |
| user_id | UUID | FK → users.user_id | Reference to user |
| otp_hash | VARCHAR(64) | NOT NULL | SHA256 hash of OTP |
| verification_type | VARCHAR(20) | NOT NULL | 'email_verification' or 'password_reset' |
| remaining_retry | INTEGER | DEFAULT 3 | Attempts left |
| is_user_blocked | BOOLEAN | DEFAULT false | Blocked after 3 fails |
| blocked_at | TIMESTAMP | NULL | When blocked |
| otp_created_at | TIMESTAMP | DEFAULT now() | OTP generation time |
| otp_expires_at | TIMESTAMP | NOT NULL | OTP expiry (10 min) |
| is_otp_valid | BOOLEAN | DEFAULT true | Invalidate on use/new OTP |

### Indexes
- `idx_otp_user_type` on `(user_id, verification_type)` (for lookup)

---

## ER Diagram

```
┌─────────────────────┐
│       users         │
├─────────────────────┤
│ user_id (PK)        │
│ user_name           │
│ email_hash          │───────┐
│ email_encrypted     │       │
│ phone_encrypted     │       │
│ password_hash       │       │
│ is_active           │       │
│ is_email_verified   │       │
│ address             │       │
│ pincode             │       │
│ preferences         │       │
│ created_at          │       │
│ updated_at          │       │
└─────────────────────┘       │
         │                    │
         │ 1:N                │ 1:N
         ▼                    ▼
┌─────────────────────┐  ┌─────────────────────┐
│   user_sessions     │  │  otp_verifications  │
├─────────────────────┤  ├─────────────────────┤
│ session_id (PK)     │  │ otp_id (PK)         │
│ user_id (FK)        │  │ user_id (FK)        │
│ device_id           │  │ otp_hash            │
│ device_name         │  │ verification_type   │
│ is_session_active   │  │ remaining_retry     │
│ session_started_at  │  │ is_user_blocked     │
│ session_ended_at    │  │ blocked_at          │
│ last_activity_at    │  │ otp_created_at      │
└─────────────────────┘  │ otp_expires_at      │
                         │ is_otp_valid        │
                         └─────────────────────┘
```

---

## Notes

### PII Encryption
- Email and phone stored encrypted (AES-256)
- Email hash for lookups (can't decrypt hash, only match)
- Phone not hashed (no lookup needed)

### Soft Delete
- `users.is_active = false` → User deactivated
- `user_sessions.is_session_active = false` → Session ended

### Cleanup Jobs
- Sessions older than 30 days with `is_session_active = false` → Delete
- OTPs older than 1 day → Delete

### Verification Types
- `email_verification` - After registration
- `password_reset` - Forgot password flow
