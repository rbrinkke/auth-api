# Activity Frontend

React/Next.js frontend for Activity App authentication testing.

## Features

- Register new user accounts
- Email verification via MailHog
- Login with JWT tokens
- Token refresh functionality
- Dashboard with user info

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

## Docker

```bash
# Build container
docker build -t activity-frontend .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 activity-frontend
```

## Pages

- `/` - Home page with API status
- `/register` - Register new user
- `/login` - Login with credentials
- `/dashboard` - Protected dashboard (requires login)

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
