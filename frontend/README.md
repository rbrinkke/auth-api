# Auth API Frontend

Enterprise-grade authentication frontend for the Auth API. Built with React, TypeScript, and Tailwind CSS.

## Features

### 🔐 Authentication
- **Login/Registration** - Complete auth flows with validation
- **Password Reset** - Request and confirm password resets
- **Two-Factor Authentication** - 2FA verification and setup
- **Token Management** - Automatic token refresh and storage

### ✅ Validation
- **Email Validation** - RFC-compliant email validation
- **Password Strength** - zxcvbn-powered strength checking
- **Real-time Feedback** - Live validation as you type
- **Enterprise Requirements** - Strong password policies

### 🎨 UI/UX
- **Modern Design** - Clean, professional interface
- **Responsive** - Works on all device sizes
- **Accessible** - WCAG compliant components
- **Error Handling** - Clear error messages and feedback

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **zxcvbn** - Password strength analysis
- **React Hook Form** - Form management
- **Lucide React** - Icon library

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Auth API running on http://localhost:8000

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable components
│   │   ├── auth/       # Authentication forms
│   │   └── ui/         # Base UI components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── hooks/          # Custom React hooks
│   ├── types/          # TypeScript types
│   ├── utils/          # Utility functions
│   └── main.tsx        # Entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Key Components

### Authentication Forms

**LoginForm** (`/src/components/auth/LoginForm.tsx`)
- Email and password authentication
- 2FA detection and handling
- Error handling for invalid credentials

**RegisterForm** (`/src/components/auth/RegisterForm.tsx`)
- Real-time password strength validation
- Email validation
- Password requirements checklist
- zxcvbn strength analysis

**TwoFactorForm** (`/src/components/auth/TwoFactorForm.tsx`)
- 2FA code verification
- Support for login, reset, and verify flows
- Code expiration handling

**PasswordResetForm** (`/src/components/auth/PasswordResetForm.tsx`)
- Request reset flow
- Token-based reset flow
- New password validation

### UI Components

**Button** - Styled button with loading state
**Input** - Form input with validation
**Alert** - Error/success message display

### Password Strength

**PasswordStrengthIndicator**
- Real-time strength analysis
- Visual progress bar
- Crack time estimates
- Security warnings

**PasswordRequirementsChecklist**
- Visual requirement checking
- Real-time feedback
- Enterprise-grade requirements

## Validation

### Email Validation
- RFC-compliant format checking
- Length validation
- Domain validation

### Password Validation
- Minimum 12 characters
- Uppercase, lowercase, numbers, special chars
- zxcvbn strength analysis (score 3+ required)
- HIBP integration on backend
- Real-time feedback

### Form Validation
- Real-time validation on change
- Clear error messages
- Prevention of invalid submissions

## API Integration

All API calls go through `apiService` (`/src/services/api.ts`):

```typescript
import apiService from '@/services/api';

// Register
await apiService.register({ email, password });

// Login
await apiService.login({ username, password });

// Two-factor
await apiService.loginWithTwoFactor({ user_id, code });

// Refresh token
await apiService.refreshToken(refreshToken);
```

## Authentication Flow

### 1. Registration
1. User enters email and password
2. Client validates email format
3. Client validates password strength (zxcvbn)
4. API call to register endpoint
5. Success message with verification email notice

### 2. Login
1. User enters credentials
2. Client validates email
3. API call to login endpoint
4. If 2FA required:
   - Navigate to 2FA page
   - User enters code from email
   - Complete login flow
5. If no 2FA:
   - Store tokens in localStorage
   - Navigate to dashboard

### 3. Password Reset
1. Request flow: User enters email
2. API sends reset email with token
3. User clicks link with token
4. Reset form accepts new password
5. Client validates new password strength
6. API resets password

### 4. Two-Factor Authentication
1. Enable 2FA (QR code + backup codes)
2. Verify setup with authenticator app
3. Login triggers 2FA requirement
4. User enters code from email
5. Login completes with tokens

## Security Features

### Client-Side
- Input sanitization
- XSS prevention
- CSRF protection (via same-origin)
- Secure token storage
- Automatic token refresh

### Server-Side (API)
- Argon2id password hashing
- JWT token rotation
- Rate limiting
- SQL injection prevention (stored procedures)
- 2FA with encrypted secrets
- HIBP integration

## Error Handling

Comprehensive error handling throughout:

```typescript
// Form validation errors
{ field: 'email', message: 'Invalid email format' }

// API errors
{ detail: 'Invalid credentials' }

// 2FA errors
{ detail: 'Invalid verification code' }

// Rate limiting
{ 
  detail: 'Too many attempts', 
  retry_after: 60 
}
```

## Development

### Linting
```bash
npm run lint
```

### Type Checking
```bash
npm run type-check
```

### Build
```bash
npm run build
```

## Proxy Configuration

Vite proxy is configured to forward `/api` requests to `http://localhost:8000`:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Modern mobile browsers

## Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Testing

To test the frontend:

1. Start the Auth API backend:
   ```bash
   cd /path/to/auth-api
   docker compose up -d
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open http://localhost:3000

4. Test flows:
   - Register new account
   - Verify email (simulate via backend)
   - Login
   - Set up 2FA
   - Login with 2FA
   - Reset password

## Production Deployment

Build the project:

```bash
npm run build
```

Deploy the `dist` folder to your hosting provider (Vercel, Netlify, etc.).

Configure environment variables:
- `VITE_API_URL` - Your Auth API URL

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions:
- Check the Auth API documentation
- Review the implementation guide
- Open a GitHub issue
