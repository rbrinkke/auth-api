# 2FA/TOTP Implementation Guide

## Overview

This document describes the Two-Factor Authentication (2FA) implementation in the Auth API. The system provides email-based 2FA codes for all authentication flows (login, password reset, email verification) and TOTP support with authenticator apps.

## Architecture

### Components

1. **TwoFactorService** (`app/services/two_factor_service.py`)
   - Core service for 2FA operations
   - TOTP secret generation and encryption
   - Temporary code management in Redis
   - Backup code generation and management
   - Failed attempt tracking and lockout

2. **2FA Endpoints** (`app/routes/2fa.py`)
   - `/auth/enable-2fa` - Initialize 2FA setup
   - `/auth/verify-2fa-setup` - Confirm 2FA setup
   - `/auth/verify-2fa` - Verify codes during flows
   - `/auth/disable-2fa` - Disable 2FA
   - `/auth/2fa-status` - Get 2FA status

3. **Database Migration** (`migrations/001_add_two_factor_auth.sql`)
   - Adds 2FA columns to users table
   - Creates two_factor_codes table
   - Indexes for performance

4. **Enhanced Login Flow** (`app/routes/login.py`)
   - Checks two_factor_enabled after password verification
   - Triggers 2FA code generation if enabled

## Security Features

### TOTP (Time-based One-Time Password)
- **Authenticator App Support**: Google Authenticator, Authy, etc.
- **Secret Encryption**: TOTP secrets encrypted with Fernet (AES 128)
- **QR Code Generation**: Visual setup for authenticator apps
- **Clock Drift Tolerance**: 1 time step (30 seconds) allowed

### Email-based 2FA Codes
- **6-digit codes** sent via email
- **5-minute expiry** for all codes
- **Single-use**: Codes consumed after successful verification
- **Redis storage**: Fast, ephemeral storage with TTL

### Backup Codes
- **8 single-use codes** generated during 2FA setup
- **Hashed storage**: SHA-256 hashing before database storage
- **Emergency access**: Use when authenticator app unavailable

### Failed Attempt Protection
- **3-attempt limit** before lockout
- **5-minute lockout** period
- **Redis tracking**: Per-user, per-purpose attempt counting
- **Automatic reset**: On successful verification

### Login Session Management
- **15-minute sessions** after 2FA verification
- **Session-based auth**: Continue without re-entering 2FA
- **Redis-backed**: Fast session validation
- **Logout cleanup**: Sessions invalidated on logout

## Configuration

### Required Environment Variables

```bash
# Add to .env file
ENCRYPTION_KEY=<32+ character key for encrypting TOTP secrets>
```

The encryption key must be at least 32 characters. Example:
```bash
ENCRYPTION_KEY=my_super_secret_encryption_key_change_me_1234
```

### Dependencies

Added to `requirements.txt`:
```txt
pyotp==2.9.0          # TOTP generation and verification
qrcode==7.4.2         # QR code generation
cryptography==42.0.0  # Encryption for TOTP secrets
```

## API Usage

### Enable 2FA

**Request:**
```bash
POST /auth/enable-2fa
Authorization: Bearer <access_token>

{
  # Empty body - uses authenticated user
}
```

**Response:**
```json
{
  "qr_code_url": "data:image/png;base64,iVBORw0KG...",
  "backup_codes": ["12345678", "87654321", ...],
  "secret": "JBSWY3DPEHPK3PXP",
  "message": "2FA setup initiated. Scan QR code with authenticator app."
}
```

**Important:** Store backup codes securely! They won't be shown again.

### Verify 2FA Setup

After scanning QR code with authenticator app:

**Request:**
```bash
POST /auth/verify-2fa-setup

{
  "code": "123456"
}
```

**Response:**
```json
{
  "verified": true,
  "message": "2FA enabled successfully"
}
```

### Login with 2FA

**Step 1: Initial Login**

```bash
POST /auth/login

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response (if 2FA enabled):**
```json
{
  "detail": {
    "message": "Two-factor authentication required. Check your email for a 6-digit code.",
    "two_factor_required": true,
    "user_id": "uuid-here"
  }
}
```

**Step 2: Verify 2FA Code**

```bash
POST /auth/login-2fa

{
  "user_id": "uuid-from-step-1",
  "code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Verify 2FA Code (Generic)

For other flows (password reset, email verification):

```bash
POST /auth/verify-2fa

{
  "user_identifier": "user@example.com",
  "code": "123456",
  "purpose": "login|reset|verify",
  "session_id": null
}
```

### Disable 2FA

**Request:**
```bash
POST /auth/disable-2fa

{
  "password": "current_password",
  "code": "123456"
}
```

**Response:**
```json
{
  "disabled": true,
  "message": "2FA disabled successfully"
}
```

### Get 2FA Status

**Request:**
```bash
GET /auth/2fa-status
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "two_factor_enabled": true
}
```

## Database Schema

### users table (updated)

```sql
ALTER TABLE activity.users ADD:
  two_factor_enabled BOOLEAN DEFAULT FALSE,
  two_factor_secret VARCHAR(255),  -- Encrypted TOTP secret
  two_factor_backup_codes JSONB,  -- Hashed backup codes
  backup_codes_used INT DEFAULT 0;
```

### two_factor_codes table (new)

```sql
CREATE TABLE activity.two_factor_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES activity.users(id) ON DELETE CASCADE,
  code VARCHAR(10) NOT NULL,  -- 6-digit temporary code
  purpose VARCHAR(20) NOT NULL CHECK (purpose IN ('login', 'reset', 'verify')),
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Redis Keys

### Temporary Codes
```
2FA:{user_id}:{purpose}
```
- Format: 6-digit code
- TTL: 300 seconds (5 minutes)
- Usage: Single-use

### Failed Attempts
```
2FA_ATTEMPTS:{user_id}:{purpose}
```
- Value: Integer (number of failed attempts)
- TTL: 300 seconds (5 minutes) after max attempts
- Purpose: Rate limiting

### Login Sessions
```
LOGIN_SESSION:{session_id}
```
- Value: user_id
- TTL: 900 seconds (15 minutes)
- Purpose: Post-2FA session management

## Testing

### Running Tests

```bash
# Unit tests (fast, mocked)
make test-unit

# Integration tests (with Redis/DB)
make test-integration

# E2E tests (full API)
make test-e2e

# All tests
make test
```

### Test Coverage

**Unit Tests** (`tests/unit/test_two_factor_service.py`):
- TOTP secret generation and encryption
- QR code generation
- Backup code generation and hashing
- Temporary code creation and verification
- Failed attempt tracking
- Login session management
- Encryption/decryption validation

**Integration Tests** (`tests/integration/test_2fa_endpoints.py`):
- Complete endpoint functionality
- Redis operations
- Database operations
- Security validations
- Lockout mechanisms

**E2E Tests** (`tests/e2e/test_2fa_flow.py`):
- Complete user workflows
- 2FA setup and login flow
- Backup code usage
- Session management
- Error scenarios
- Security testing

### Running the Migration

```bash
# Apply migration
docker compose exec postgres psql -U activity_user -d activitydb -f /docker-entrypoint-initdb.d/001_add_two_factor_auth.sql

# Or manually
psql -h localhost -U activity_user -d activitydb -f migrations/001_add_two_factor_auth.sql
```

## Security Best Practices

### For Users

1. **Enable 2FA immediately** after account creation
2. **Store backup codes securely** (password manager, safe, etc.)
3. **Use authenticator app** when possible (more secure than email)
4. **Never share 2FA codes** with anyone
5. **Report suspicious activity** immediately

### For Developers

1. **Encryption key management**:
   - Use strong, random encryption keys
   - Rotate keys periodically
   - Never commit keys to version control
   - Use environment variables

2. **Code storage**:
   - All codes stored in Redis (ephemeral)
   - TOTP secrets encrypted at rest
   - Backup codes hashed (SHA-256)

3. **Rate limiting**:
   - Built-in 3-attempt limit
   - 5-minute lockout period
   - Reset on successful verification

4. **Session security**:
   - 15-minute session TTL
   - Automatic cleanup on logout
   - No sensitive data in sessions

5. **Monitoring**:
   - Log all 2FA attempts (success and failure)
   - Alert on repeated failures
   - Track unusual patterns

## Troubleshooting

### Common Issues

**1. "Invalid verification code" error**
- Check if code is expired (5-minute TTL)
- Ensure correct purpose (login vs reset vs verify)
- Verify code hasn't been used already

**2. "Too many failed attempts" error**
- Wait 5 minutes for lockout to expire
- Or use backup codes if available

**3. QR code not scanning**
- Ensure authenticator app supports TOTP
- Check time synchronization on device
- Try manual entry using the secret

**4. Lost authenticator device**
- Use backup codes
- Contact support to disable 2FA

**5. Encryption errors**
- Verify ENCRYPTION_KEY is set correctly
- Ensure key is at least 32 characters
- Check key hasn't changed (would need re-setup)

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('app.services.two_factor_service').setLevel(logging.DEBUG)
```

Check Redis for active codes:
```bash
docker compose exec redis redis-cli keys "2FA:*"
```

## Future Enhancements

Planned improvements (Phase 2):

1. **TOTP-only mode**: Support for authenticator apps without email
2. **Hardware key support**: YubiKey, FIDO2
3. **SMS codes**: Backup for email delivery failures
4. **Admin dashboard**: Manage user 2FA settings
5. **Audit logging**: Detailed 2FA event logging
6. **Recovery codes**: Enhanced backup code system
7. **Device trust**: Remember trusted devices
8. **Biometric integration**: WebAuthn support

## Compliance

This implementation follows:
- **OWASP Authentication Guidelines**
- **NIST SP 800-63B** (Digital Identity Guidelines)
- **RFC 6238** (TOTP Algorithm)
- **RFC 4226** (HOTP Algorithm)

## Support

For issues or questions:
1. Check this documentation
2. Review test cases
3. Check logs for error details
4. Open GitHub issue

---

**Version**: 1.0.0
**Last Updated**: 2025-11-05
**Implementation Status**: ✅ Complete
