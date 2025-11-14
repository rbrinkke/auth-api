# 🚀 Quick Start Guide - MSW Auth Handlers

Get up and running with mock auth handlers in **5 minutes**!

## Step 1: Install Dependencies

```bash
npm install --save-dev msw uuid
```

## Step 2: Copy Handlers to Your Project

```bash
# From your frontend project root
cp /path/to/auth-api/frontend-mocks/src/mocks/handlers.ts src/mocks/
```

## Step 3: Setup MSW

Create `src/mocks/browser.ts`:

```typescript
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export const worker = setupWorker(...handlers)
```

## Step 4: Start MSW in Development

In your app entry point (`src/main.tsx` or `src/index.tsx`):

```typescript
async function enableMocking() {
  if (process.env.NODE_ENV !== 'development') {
    return
  }

  const { worker } = await import('./mocks/browser')

  return worker.start({
    onUnhandledRequest: 'bypass'
  })
}

enableMocking().then(() => {
  // Your app initialization
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <App />
  )
})
```

## Step 5: Generate MSW Service Worker

```bash
npx msw init public/ --save
```

## Step 6: Test It!

```typescript
// In your React component
const handleLogin = async () => {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'test@example.com',
      password: 'Password123!'
    })
  })

  const data = await response.json()
  console.log('Login response:', data)
  // Should see: { message: "...", requires_code: true, ... }
}
```

## 🎉 That's It!

You now have a fully-mocked authentication backend!

### Available Test Accounts

```typescript
const TEST_ACCOUNTS = {
  MULTI_ORG: {
    email: 'test@example.com',
    password: 'Password123!',
    note: 'Has 3 organizations - triggers org selection'
  },
  SINGLE_ORG: {
    email: 'singleorg@example.com',
    password: 'Password123!',
    note: 'Auto-selects organization'
  },
  ADMIN: {
    email: 'admin@acme.com',
    password: 'Password123!',
    note: 'Admin role in Acme Corp'
  },
  UNVERIFIED: {
    email: 'unverified@example.com',
    password: 'Password123!',
    note: 'Email not verified - will get 403 on login'
  }
}
```

### Test Login Flow

```typescript
import { useState } from 'react'

function LoginForm() {
  const [email, setEmail] = useState('test@example.com')
  const [password, setPassword] = useState('Password123!')
  const [code, setCode] = useState('')
  const [response, setResponse] = useState<any>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, code: code || null })
    })

    const data = await res.json()
    setResponse(data)
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        placeholder="Password"
      />
      {response?.requires_code && (
        <input
          type="text"
          value={code}
          onChange={e => setCode(e.target.value)}
          placeholder="Verification Code (use: 123456)"
        />
      )}
      <button type="submit">Login</button>

      {response && (
        <pre>{JSON.stringify(response, null, 2)}</pre>
      )}
    </form>
  )
}
```

## Common Flows

### Complete Login Flow

```typescript
// 1. Initial login - sends code
const step1 = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'Password123!'
  })
})
// Response: { requires_code: true, user_id: "...", ... }

// 2. Login with code - shows orgs (if multiple)
const step2 = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'Password123!',
    code: '123456'
  })
})
// Response: { organizations: [...], user_token: "..." }

// 3. Login with org_id - gets tokens
const step3 = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'Password123!',
    code: '123456',
    org_id: '650e8400-e29b-41d4-a716-446655440001'
  })
})
// Response: { access_token: "...", refresh_token: "...", ... }
```

### Force Scenarios for Testing

```typescript
// Force error scenarios using X-Mock-Scenario header

// Test invalid credentials
await fetch('/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Mock-Scenario': 'invalid-credentials'
  },
  body: JSON.stringify({ email: 'any', password: 'any' })
})
// Response: 401 { detail: "Invalid credentials" }

// Test org selection
await fetch('/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Mock-Scenario': 'org-selection'
  },
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'Password123!',
    code: '123456'
  })
})
// Response: { organizations: [...], ... }

// Test single-org auto-login
await fetch('/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Mock-Scenario': 'single-org-login'
  },
  body: JSON.stringify({
    email: 'singleorg@example.com',
    password: 'Password123!',
    code: '123456'
  })
})
// Response: { access_token: "...", ... }
```

## Debugging Tips

### Check if MSW is running

```typescript
// In browser console
console.log('MSW Active:', window.msw !== undefined)
```

### See which requests are intercepted

```typescript
// In worker.start()
worker.start({
  onUnhandledRequest: 'warn' // Logs unhandled requests to console
})
```

### Inspect mock responses

```typescript
const response = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ ... })
})

console.log('Status:', response.status)
console.log('Headers:', Object.fromEntries(response.headers))
console.log('Body:', await response.json())
```

## Next Steps

1. ✅ Read the [full README](./README.md) for all endpoints
2. ✅ Check [test examples](./src/mocks/handlers.test.ts)
3. ✅ Explore all [test accounts](./README.md#test-accounts)
4. ✅ Learn [scenario testing](./README.md#scenario-testing)

## Need Help?

- 📖 [MSW Documentation](https://mswjs.io/docs/)
- 📖 [Backend API Docs](../README.md)
- 💬 Contact: Activity App Team

---

**Happy Mocking! 🎭✨**
