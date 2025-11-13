# OAuth Test Users - Credentials

**⚠️ TEST ENVIRONMENT ONLY - NOT FOR PRODUCTION ⚠️**

These test users are created for OAuth 2.0 Authorization Server testing. All users are pre-verified and ready for immediate login.

---

## Test User Accounts

### 1. Alice Admin (Administrator)
- **Email:** `alice.admin@example.com`
- **Password:** `SecurePass123!Admin`
- **Role:** Admin
- **Use Case:** Full access testing, admin operations

### 2. Bob Developer (Developer)
- **Email:** `bob.developer@example.com`
- **Password:** `DevSecure2024!Bob`
- **Role:** Developer
- **Use Case:** API integration testing, development workflows

### 3. Carol Manager (Manager)
- **Email:** `carol.manager@example.com`
- **Password:** `Manager!Strong789`
- **Role:** Manager
- **Use Case:** Organization management, team permissions

### 4. David Tester (QA Tester)
- **Email:** `david.tester@example.com`
- **Password:** `Testing!Secure456`
- **Role:** Tester
- **Use Case:** Quality assurance, validation testing

### 5. Emma User (Regular User)
- **Email:** `emma.user@gmail.com`
- **Password:** `UserPass!2024Emma`
- **Role:** Regular User
- **Use Case:** Standard end-user workflows, external email domain

### 6. Frank Power (Power User)
- **Email:** `frank.power@outlook.com`
- **Password:** `PowerUser!Frank99`
- **Role:** Power User
- **Use Case:** Extended permissions, advanced features

### 7. Grace OAuth (OAuth Client)
- **Email:** `grace.oauth@yahoo.com`
- **Password:** `OAuth!Testing321`
- **Role:** OAuth Client
- **Use Case:** Dedicated OAuth flow testing, PKCE validation

### 8. Henry Mobile (Mobile User)
- **Email:** `henry.mobile@proton.me`
- **Password:** `Mobile!App2024Henry`
- **Role:** Mobile User
- **Use Case:** Mobile app integration, mobile-specific flows

### 9. Iris External (Partner)
- **Email:** `iris.external@partner.com`
- **Password:** `Partner!Secure555`
- **Role:** Partner
- **Use Case:** External partner integration, third-party access

### 10. Jack Demo (Demo Account)
- **Email:** `jack.demo@example.com`
- **Password:** `Demo!Account2024`
- **Role:** Demo
- **Use Case:** Presentations, demonstrations, public testing

---

## Quick Reference Table

| # | Name | Email | Password | Role |
|---|------|-------|----------|------|
| 1 | Alice Admin | alice.admin@example.com | SecurePass123!Admin | admin |
| 2 | Bob Developer | bob.developer@example.com | DevSecure2024!Bob | developer |
| 3 | Carol Manager | carol.manager@example.com | Manager!Strong789 | manager |
| 4 | David Tester | david.tester@example.com | Testing!Secure456 | tester |
| 5 | Emma User | emma.user@gmail.com | UserPass!2024Emma | regular |
| 6 | Frank Power | frank.power@outlook.com | PowerUser!Frank99 | power_user |
| 7 | Grace OAuth | grace.oauth@yahoo.com | OAuth!Testing321 | oauth_client |
| 8 | Henry Mobile | henry.mobile@proton.me | Mobile!App2024Henry | mobile_user |
| 9 | Iris External | iris.external@partner.com | Partner!Secure555 | partner |
| 10 | Jack Demo | jack.demo@example.com | Demo!Account2024 | demo |

---

## Usage Examples

### Manual OAuth Flow Testing

```bash
# Example: Test OAuth flow with Grace OAuth
1. Navigate to: http://localhost:8000/oauth/authorize?client_id=test-client-1&response_type=code&redirect_uri=http://localhost:3000/callback&scope=activity:read+profile:read&code_challenge=YOUR_CHALLENGE&code_challenge_method=S256&state=random123

2. Login with:
   Email: grace.oauth@yahoo.com
   Password: OAuth!Testing321

3. Approve consent screen

4. Receive authorization code in redirect
```

### Automated Testing with test.sh

```bash
# Setup all test users
./test_oauth.sh --setup-users

# Run OAuth tests with specific user
./test_oauth.sh --user grace.oauth@yahoo.com

# Run full test suite (uses all users)
./test_oauth.sh
```

### Direct API Testing

```bash
# Login with Alice Admin
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice.admin@example.com",
    "password": "SecurePass123!Admin"
  }'

# Response includes access_token, refresh_token, and token_type
# Example response:
# {
#   "access_token": "eyJhbGci...",
#   "refresh_token": "eyJhbGci...",
#   "token_type": "bearer",
#   "org_id": null
# }
```

---

## Password Policy Compliance

All passwords meet the auth-api security requirements:

✅ **Minimum 8 characters**
✅ **zxcvbn strength score 3-4** (strong passwords)
✅ **Argon2id hashing** (GPU-resistant)
✅ **Not in HIBP breach database** (verified secure)
✅ **Mixed case, numbers, special characters**

---

## Security Notes

- **🔒 Environment:** TEST ONLY - Never use these credentials in production
- **🔑 Storage:** Passwords are documented here for testing convenience
- **✅ Verification:** All users are pre-verified (is_verified=TRUE)
- **🔄 Reset:** Run `./test_oauth.sh --reset-users` to recreate all users
- **🗑️ Cleanup:** Run `./test_oauth.sh --cleanup-users` to remove test users

---

## Setup Instructions

### Automatic Setup (Recommended)

```bash
# Run test script with user setup
./test_oauth.sh --setup-users
```

This will:
1. Register all 10 test users via /auth/register
2. Automatically verify their emails
3. Create test OAuth client if needed
4. Validate all users can login

### Manual Setup

```bash
# Register each user
for user in $(jq -r '.test_users[] | @json' test_users.json); do
  email=$(echo "$user" | jq -r '.email')
  password=$(echo "$user" | jq -r '.password')

  curl -X POST http://localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"$password\"}"
done

# Verify emails (requires DB access or Redis token manipulation)
```

---

## Troubleshooting

### User Already Exists
If you see "Email already registered", the user exists. Use `--reset-users` to recreate.

### Login Failed
1. Verify API is running: `docker compose ps auth-api`
2. Check user is verified: `docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT email, is_verified FROM activity.users WHERE email='alice.admin@example.com'"`
3. Verify password meets requirements

### OAuth Flow Issues
1. Ensure test OAuth client exists: `test-client-1`
2. Check redirect_uri matches: `http://localhost:3000/callback`
3. Verify PKCE challenge is valid (43+ chars, base64url)

---

---

## Verification

All 10 test users have been verified in the database:

```bash
# Quick verification check
docker exec activity-postgres-db psql -U postgres -d activitydb -c \
  "SELECT email, is_verified, is_active, created_at FROM activity.users
   WHERE email IN (
     'alice.admin@example.com', 'bob.developer@example.com',
     'carol.manager@example.com', 'david.tester@example.com',
     'emma.user@gmail.com', 'frank.power@outlook.com',
     'grace.oauth@yahoo.com', 'henry.mobile@proton.me',
     'iris.external@partner.com', 'jack.demo@example.com'
   ) ORDER BY created_at;"
```

**Database Status:** ✅ All 10 users exist and are verified
**API Endpoint:** `/api/auth/login` (uses `email` field for authentication)
**Authentication:** Working and tested with all 10 user accounts

---

**Created:** 2025-11-12
**Last Updated:** 2025-11-12
**Purpose:** OAuth 2.0 Authorization Server Testing
**Maintained by:** Claude Code
**Status:** ✅ Production-Ready Test Suite - Database Verified
