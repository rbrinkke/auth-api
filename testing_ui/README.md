# Authentication Testing UI

A standalone web-based interface for manually testing all authentication flows of the Auth API.

## 🎯 Purpose

This testing UI provides a visual, interactive way to test the complete authentication lifecycle without needing to write API calls or use tools like curl/Postman. Perfect for:

- **Manual QA Testing**: Test all auth flows visually
- **Development**: Quick feedback during development
- **Documentation**: Live demonstration of API flows
- **Debugging**: See exact requests/responses with timestamps

## 🚀 Quick Start

### Standalone Docker Container (Recommended)

Run the testing UI as a completely separate Docker container:

```bash
# 1. Make sure auth-api is running (required)
cd /mnt/d/activity && ./scripts/start-infra.sh
cd auth-api && docker compose up -d

# 2. Start standalone testing UI container
cd testing_ui
./start.sh
```

**What happens:**
- Builds dedicated Docker image for testing UI
- Starts container `auth-testing-ui` on port 8099
- Connects to `activity-network` to communicate with auth-api
- Runs completely independently from auth-api

**Access the testing page:**
```
http://localhost:8099/test/auth
```

**Useful commands:**
```bash
# View logs
docker logs -f auth-testing-ui

# Stop
cd testing_ui && docker compose down

# Rebuild after changes
cd testing_ui && docker compose build && docker compose restart

# Check status
curl http://localhost:8099/health
```

## 📋 Features

### Supported Authentication Flows

#### 1️⃣ **Registration Flow** (2 steps)
- **Step 1**: Create account with email & password
- **Step 2**: Verify email with 6-digit code

#### 2️⃣ **Login Flow** (2-3 steps)
- **Step 1**: Initial login (triggers email code)
- **Step 2**: Complete login with code
- **Step 3**: Organization selection (multi-org users only)

#### 3️⃣ **Password Reset Flow** (2 steps)
- **Step 1**: Request password reset
- **Step 2**: Complete reset with code & new password

#### 4️⃣ **Token Management**
- Refresh access tokens
- Logout (invalidate refresh tokens)

### UI Features

✅ **Auto-fill**: Automatically populates tokens/IDs from previous responses
✅ **Local Storage**: Stores tokens and credentials across page reloads
✅ **Response Display**: Shows formatted JSON responses with timestamps
✅ **Error Handling**: Clear error messages with status codes
✅ **Visual Feedback**: Color-coded success (green) / error (red) responses
✅ **Sticky Navigation**: Quick jump to different flows
✅ **Stored Data View**: See all currently stored tokens and session data

## 🎨 Interface Sections

### Navigation Bar
Quick jump links to all testing sections:
- 📝 Register
- 🔑 Login
- 🔄 Reset Password
- 🎫 Tokens
- 💾 Stored Data

### Registration Section
Test the complete registration flow:
1. Enter email and password
2. System sends verification code (check response for `verification_token`)
3. Enter token and 6-digit code to verify

### Login Section
Test all login scenarios:
- **Single Organization**: Get tokens directly after code verification
- **Multi-Organization**: Select organization after code verification
- **Development Mode** (`SKIP_LOGIN_CODE=true`): Get tokens immediately

### Password Reset Section
Test password recovery:
1. Request reset (sends email with token and code)
2. Complete reset with new password

### Token Management Section
Test token lifecycle:
- **Refresh Token**: Get new access token using refresh token
- **Logout**: Invalidate refresh token

### Stored Data Display
View all session data stored in browser localStorage:
- Access Token
- Refresh Token
- User ID
- Organization ID
- Email (for convenience)

## 🔧 Configuration

### Enable/Disable Testing UI

**Development** (`.env`):
```bash
ENABLE_TESTING_UI=true
```

**Production** (`.env`):
```bash
ENABLE_TESTING_UI=false
```

### Skip Login Codes (Development Only)

For faster testing, skip email verification codes:

```bash
SKIP_LOGIN_CODE=true
```

With this setting, you'll receive tokens directly from the first login request.

## 🏗️ Architecture

### Directory Structure

```
testing_ui/
├── __init__.py           # Module initialization
├── router.py             # FastAPI router
├── standalone.py         # Standalone FastAPI app
├── start.sh              # Quick start script (Docker)
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
├── .dockerignore         # Docker ignore file
├── templates/
│   └── auth_test.html    # Jinja2 template with Tailwind CSS
└── README.md            # This file
```

### Technology Stack

- **Backend**: FastAPI (serves the page)
- **Frontend**: Jinja2 Templates
- **Styling**: Tailwind CSS (via CDN)
- **JavaScript**: Vanilla JS (Fetch API)
- **Storage**: Browser localStorage

### Deployment Modes

The testing UI can run in two modes:

#### Standalone Mode (Recommended)
- Runs as separate FastAPI app on port 8099
- Zero integration with main auth-api
- Started with `./start.sh` or `python3 standalone.py`
- Best for development and testing isolation

#### Integrated Mode (Legacy)
- Runs within main auth-api app
- Shares same port (8000) and process
- Requires conditional import in `app/main.py`
- Can be disabled via `ENABLE_TESTING_UI=false`

## 📝 Usage Examples

### Example 1: Complete Registration Flow

1. Navigate to `/test/auth`
2. Scroll to "Registration Flow"
3. Enter email: `test@example.com`
4. Enter password: `Password123!`
5. Click "Register Account"
6. Copy `verification_token` from response (auto-filled)
7. Enter 6-digit code from email
8. Click "Verify Email"
9. ✅ Account created and verified!

### Example 2: Login with Organization Selection

1. Use registered account from Example 1
2. Scroll to "Login Flow"
3. Enter email and password
4. Click "Send Login Code"
5. Enter 6-digit code from email
6. Click "Complete Login"
7. If multi-org user: Select organization ID and click "Select Organization"
8. ✅ Access and refresh tokens stored!

### Example 3: Token Refresh

1. After successful login (Example 2)
2. Scroll to "Token Management"
3. Click "Use stored refresh token" button
4. Click "Refresh Token"
5. ✅ New tokens received and stored!

## 🔒 Security Considerations

### Development Only
This testing UI is **INTENDED FOR DEVELOPMENT/TESTING ONLY**:

- ⚠️ Stores credentials in browser localStorage
- ⚠️ Displays full tokens in clear text
- ⚠️ No authentication required to access the page
- ⚠️ Should **NEVER** be enabled in production

### Production Deployment

**CRITICAL**: Set `ENABLE_TESTING_UI=false` in production `.env`:

```bash
# Production .env
ENABLE_TESTING_UI=false
```

When disabled:
- Testing UI router is not imported
- `/test/auth` endpoint returns 404
- Zero overhead on production deployments

## 🧪 Testing Scenarios

### Test Case 1: Email Verification Required
- Register new account
- Try to login without verifying email
- **Expected**: "Account not verified" error

### Test Case 2: Invalid Credentials
- Enter wrong password
- **Expected**: "Invalid credentials" (generic message to prevent enumeration)

### Test Case 3: Expired Verification Code
- Wait 10 minutes after registration
- Try to verify with old code
- **Expected**: "Code expired" error

### Test Case 4: Token Rotation
- Login successfully
- Refresh token
- Try to use old refresh token again
- **Expected**: "Invalid token" (single-use tokens)

### Test Case 5: Rate Limiting
- Attempt 6 login requests in 1 minute
- **Expected**: HTTP 429 "Too many requests"

## 🛠️ Development

### Adding New Flows

To add a new authentication flow to the testing UI:

1. **Add HTML section** to `templates/auth_test.html`:
   ```html
   <section id="new-flow" class="flow-section bg-white rounded-lg shadow-lg p-6">
       <h2>New Flow</h2>
       <!-- Form fields here -->
   </section>
   ```

2. **Add JavaScript function**:
   ```javascript
   async function newFlow() {
       const result = await apiCall('/api/auth/new-endpoint', 'POST', { ... });
       displayResponse('new_flow_response', result.data);
   }
   ```

3. **Add navigation link**:
   ```html
   <a href="#new-flow">🆕 New Flow</a>
   ```

### Customizing Styles

The UI uses **Tailwind CSS via CDN**. To customize:

1. Modify Tailwind classes in HTML
2. Add custom CSS in `<style>` tag (for complex styles)
3. Or replace CDN with local Tailwind build

### API Base URL

The JavaScript automatically detects the API base URL:

```javascript
const API_BASE = window.location.origin; // http://localhost:8000
```

For testing against different environments:
```javascript
const API_BASE = 'https://auth-api-staging.example.com';
```

## 📊 Monitoring

### Check if Testing UI is Enabled

Check the logs when starting the app:

```
INFO: 🧪 Testing UI enabled at /test/auth
```

### Verify Route Registration

Check the OpenAPI schema at `/docs` (if `ENABLE_DOCS=true`):
- Look for "Testing UI" tag
- Endpoint: `GET /test/auth`

## 🤝 Contributing

When modifying the testing UI:

1. **Keep it standalone**: Don't couple with main application code
2. **Maintain documentation**: Update this README
3. **Test all flows**: Ensure all buttons/forms work
4. **Follow patterns**: Match existing UI/UX patterns
5. **Security first**: Never expose sensitive functionality

## 📄 License

This testing UI is part of the Activity Platform Auth API project and follows the same proprietary license.

---

**Created**: 2025-11-16
**Version**: 1.0.0
**Maintainer**: Activity Platform Team
