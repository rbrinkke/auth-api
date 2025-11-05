# 2FA/TOTP Implementation Plan

## 🎯 Overview
Implement Time-based One-Time Password (TOTP) authentication as a second factor for all critical actions.

## 🔒 Authentication Flow

### Login with 2FA
```
1. User enters email + password
2. System validates credentials ✅
3. If 2FA enabled:
   - Generate 6-digit TOTP code
   - Send code via EMAIL (no links!)
   - Return 202 "2FA required" status
4. User enters TOTP code from authenticator app
5. Validate TOTP code ✅
6. Generate JWT tokens
```

### Password Reset with 2FA
```
1. User enters email
2. System validates email exists ✅
3. If 2FA enabled:
   - Generate 6-digit TOTP code
   - Send via EMAIL
   - Return 202 "2FA required" status
4. User enters TOTP code
5. Validate TOTP code ✅
6. Send password reset token
```

### Email Verification with 2FA (Enhanced)
```
1. User registers
2. Generate verification token
3. Generate 6-digit TOTP code
4. Send BOTH via email (token in link, code for TOTP)
5. User can verify EITHER:
   a) Click link (token-based)
   b) Enter code on login screen (TOTP-based)
```

## 📋 Technical Implementation

### Database Changes

#### 1. Add 2FA fields to users table
```sql
ALTER TABLE activity.users ADD COLUMN:
  - two_factor_enabled BOOLEAN DEFAULT FALSE
  - two_factor_secret VARCHAR(255)  -- Encrypted TOTP secret
  - two_factor_backup_codes JSONB   -- Backup codes (hashed)
  - backup_codes_used INT DEFAULT 0
```

#### 2. Create 2FA verification codes table
```sql
CREATE TABLE activity.two_factor_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES activity.users(id) ON DELETE CASCADE,
  code VARCHAR(10) NOT NULL,  -- 6-digit code
  purpose VARCHAR(20) NOT NULL,  -- 'login', 'reset', 'verify'
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Redis Schema

```
# Temporary 2FA codes (TTL: 5 minutes)
2FA:{user_id}:{purpose} = {6_digit_code}
EXPIRE: 300 seconds

# TOTP secret (encrypted)
TOTP_SECRET:{user_id} = {encrypted_secret}
TTL: none (permanent until disabled)

# Login session (to prevent re-entering code)
LOGIN_SESSION:{session_id} = {user_id}
EXPIRE: 900 seconds (15 min)
```

### API Endpoints

#### POST /auth/register-2fa
Enable 2FA for logged-in user
```json
Request: {}
Response: {
  "qr_code_url": "data:image/png;base64,...",
  "backup_codes": ["123456", "789012", ...]
}
```

#### POST /auth/verify-2fa
Verify TOTP code during login/reset
```json
Request: {
  "user_identifier": "email or session_id",
  "code": "123456",
  "purpose": "login|reset|verify"
}
Response: {
  "verified": true,
  "session_id": "abc123"  // For login flow
}
```

#### POST /auth/disable-2fa
Disable 2FA (requires password + TOTP)
```json
Request: {
  "password": "current_password",
  "code": "123456"
}
Response: { "disabled": true }
```

### Service Layer

#### TwoFactorService
```python
class TwoFactorService:
    async def generate_totp_secret() -> str
    async def generate_qr_code(secret: str, email: str) -> str
    async def verify_totp_code(secret: str, code: str) -> bool
    async def generate_backup_codes() -> List[str]
    async def create_temp_code(user_id: str, purpose: str) -> str
    async def verify_temp_code(user_id: str, code: str, purpose: str) -> bool
    async def generate_login_session(user_id: str) -> str
```

#### Enhanced EmailService
```python
async def send_2fa_code_email(email: str, code: str, purpose: str)
# Purpose: login | reset | verify
# Email template for each purpose
```

### Changes to Existing Endpoints

#### POST /auth/login (Enhanced)
```python
# Step 1: Validate credentials
if user.two_factor_enabled:
    # Generate temp code
    code = await twofa_service.create_temp_code(user.id, "login")
    await email_service.send_2fa_code_email(user.email, code, "login")
    return 202 "2FA required"

# Step 2: Check TOTP if provided
if "two_factor_code" in request_data:
    verified = await twofa_service.verify_temp_code(
        user.id,
        request_data["two_factor_code"],
        "login"
    )
    if not verified:
        raise HTTPException(401, "Invalid 2FA code")

# Step 3: Issue tokens
return generate_jwt_tokens(user)
```

#### POST /auth/request-password-reset (Enhanced)
```python
if user.two_factor_enabled:
    code = await twofa_service.create_temp_code(user.id, "reset")
    await email_service.send_2fa_code_email(user.email, code, "reset")
    return 202 "2FA required"

# Continue with existing flow
```

### Frontend (If Needed)

#### Enable 2FA Flow
1. User clicks "Enable 2FA" in profile
2. API returns QR code + backup codes
3. User scans QR with authenticator app (Google Auth, Authy, etc.)
4. User enters code from app to verify setup
5. Save backup codes securely

#### Login with 2FA Flow
1. User enters email + password
2. If 2FA enabled, show "Enter 6-digit code" field
3. User enters code from authenticator app
4. Validate and login

## 🧪 Testing Strategy

### Unit Tests
- TOTP secret generation and encryption
- Code validation (valid, invalid, expired, used)
- Backup code validation
- QR code generation

### Integration Tests
- Complete 2FA setup flow
- Login with 2FA enabled
- Password reset with 2FA
- Disable 2FA flow
- Backup code usage

### Edge Cases
- Code expiry (5 minutes)
- Code single-use only
- Too many failed attempts (rate limiting)
- Email delivery failure handling
- Secret encryption/decryption

## 🔐 Security Considerations

1. **TOTP Secret Encryption**: Encrypt secret before DB storage
2. **Rate Limiting**: 3 attempts per 5 minutes for code entry
3. **Backup Codes**: Hash before storage, single-use
4. **Code Expiry**: 5 minutes for temporary codes
5. **Audit Logging**: Log all 2FA events
6. **HTTPS Only**: TOTP codes only over secure connections

## 📊 Migration Strategy

### For Existing Users
1. **Optional Enrollment**: 2FA disabled by default
2. **Prompt in UI**: "Enable 2FA for extra security"
3. **Admin Enforcement**: Optional policy to require 2FA for certain users
4. **Grace Period**: Users have 30 days to enable before enforcement

### Rollout Plan
1. **Week 1**: Implement core 2FA service
2. **Week 2**: Add API endpoints
3. **Week 3**: Update login/reset flows
4. **Week 4**: Add tests and documentation
5. **Week 5**: Deploy to staging, test
6. **Week 6**: Deploy to production, gradual rollout

## 📧 Email Templates

### Login 2FA Code
```
Subject: Your login verification code

Your verification code is: 123456

This code expires in 5 minutes.
If you didn't attempt to login, please ignore this email.
```

### Password Reset 2FA Code
```
Subject: Password reset verification code

Your password reset verification code is: 789012

Use this code to proceed with your password reset.
This code expires in 5 minutes.
```

### Registration 2FA Code
```
Subject: Verify your email

Welcome! Please verify your email address using one of these methods:

Option 1 - Click this link:
https://app.example.com/verify?token=abc123

Option 2 - Enter this code in the app:
123456

Your verification code expires in 24 hours.
```

## ✅ Benefits

1. **Security**: 10x stronger than password-only
2. **Industry Standard**: Expected by users
3. **Compliance**: Meets security standards
4. **User Control**: Optional, can be disabled
5. **Backup Codes**: Prevents lockout
6. **No Links**: All codes via email
7. **Redis Storage**: Fast, scalable
8. **Audit Trail**: Full logging

## 🎯 Next Steps

1. **Approval** of this plan
2. **Database migration** script
3. **Implementation** of TwoFactorService
4. **API endpoints** development
5. **Integration** with existing flows
6. **Testing** and validation
7. **Documentation** updates
8. **Staging** deployment
9. **Production** rollout
