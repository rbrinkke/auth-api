import { http, HttpResponse, delay } from 'msw'
import { v4 as uuidv4 } from 'uuid'

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

type UserRole = 'owner' | 'admin' | 'member'

interface MockUser {
  id: string
  email: string
  password: string
  isVerified: boolean
  is2FAEnabled: boolean
  totp_secret?: string
  organizations: MockOrganization[]
  verificationToken?: string
  verificationCode?: string
  resetToken?: string
  resetCode?: string
}

interface MockOrganization {
  id: string
  name: string
  slug: string
  role: UserRole
  member_count: number
  description?: string
  created_at: string
}

interface MockGroup {
  id: string
  org_id: string
  name: string
  description?: string
  member_count: number
  created_at: string
  updated_at: string
}

interface MockPermission {
  id: string
  resource: string
  action: string
  description?: string
  permission_string: string
}

// ============================================================================
// MOCK DATA STORE
// ============================================================================

/**
 * Mock user database with comprehensive test accounts
 * Password: All users use 'Password123!' for testing
 */
const mockUsers: Record<string, MockUser> = {
  'test@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440000',
    email: 'test@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    organizations: [
      {
        id: '650e8400-e29b-41d4-a716-446655440001',
        name: 'Acme Corporation',
        slug: 'acme-corp',
        role: 'owner',
        member_count: 42,
        description: 'Leading technology company',
        created_at: '2025-01-01T10:00:00Z'
      },
      {
        id: '650e8400-e29b-41d4-a716-446655440002',
        name: 'Beta Industries',
        slug: 'beta-industries',
        role: 'admin',
        member_count: 15,
        created_at: '2025-02-15T14:30:00Z'
      },
      {
        id: '650e8400-e29b-41d4-a716-446655440003',
        name: 'Gamma Solutions',
        slug: 'gamma-solutions',
        role: 'member',
        member_count: 8,
        created_at: '2025-03-20T09:15:00Z'
      }
    ]
  },
  'admin@acme.com': {
    id: '550e8400-e29b-41d4-a716-446655440010',
    email: 'admin@acme.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    organizations: [
      {
        id: '650e8400-e29b-41d4-a716-446655440001',
        name: 'Acme Corporation',
        slug: 'acme-corp',
        role: 'admin',
        member_count: 42,
        created_at: '2025-01-01T10:00:00Z'
      }
    ]
  },
  'member@acme.com': {
    id: '550e8400-e29b-41d4-a716-446655440011',
    email: 'member@acme.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    organizations: [
      {
        id: '650e8400-e29b-41d4-a716-446655440001',
        name: 'Acme Corporation',
        slug: 'acme-corp',
        role: 'member',
        member_count: 42,
        created_at: '2025-01-01T10:00:00Z'
      }
    ]
  },
  'singleorg@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440020',
    email: 'singleorg@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    organizations: [
      {
        id: '650e8400-e29b-41d4-a716-446655440001',
        name: 'Acme Corporation',
        slug: 'acme-corp',
        role: 'admin',
        member_count: 42,
        created_at: '2025-01-01T10:00:00Z'
      }
    ]
  },
  'unverified@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440030',
    email: 'unverified@example.com',
    password: 'Password123!',
    isVerified: false,
    is2FAEnabled: false,
    organizations: [],
    verificationToken: 'VERIFY_TOKEN_ABC123456789',
    verificationCode: '123456'
  },
  'existing@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440040',
    email: 'existing@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    organizations: []
  },
  '2fa-user@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440050',
    email: '2fa-user@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: true,
    totp_secret: 'JBSWY3DPEHPK3PXP',
    organizations: [
      {
        id: '650e8400-e29b-41d4-a716-446655440001',
        name: 'Acme Corporation',
        slug: 'acme-corp',
        role: 'owner',
        member_count: 42,
        created_at: '2025-01-01T10:00:00Z'
      }
    ]
  }
}

/**
 * Mock organizations database
 */
const mockOrganizations: Record<string, MockOrganization & { members: Array<{ user_id: string; role: UserRole; joined_at: string }> }> = {
  '650e8400-e29b-41d4-a716-446655440001': {
    id: '650e8400-e29b-41d4-a716-446655440001',
    name: 'Acme Corporation',
    slug: 'acme-corp',
    role: 'owner',
    member_count: 42,
    description: 'Leading technology company',
    created_at: '2025-01-01T10:00:00Z',
    members: [
      { user_id: '550e8400-e29b-41d4-a716-446655440000', role: 'owner', joined_at: '2025-01-01T10:00:00Z' },
      { user_id: '550e8400-e29b-41d4-a716-446655440010', role: 'admin', joined_at: '2025-01-02T11:00:00Z' },
      { user_id: '550e8400-e29b-41d4-a716-446655440011', role: 'member', joined_at: '2025-01-03T12:00:00Z' }
    ]
  }
}

/**
 * Mock groups database
 */
const mockGroups: Record<string, MockGroup & { members: string[]; permissions: string[] }> = {
  '750e8400-e29b-41d4-a716-446655440001': {
    id: '750e8400-e29b-41d4-a716-446655440001',
    org_id: '650e8400-e29b-41d4-a716-446655440001',
    name: 'Administrators',
    description: 'Full system administrators',
    member_count: 5,
    created_at: '2025-01-01T10:00:00Z',
    updated_at: '2025-01-01T10:00:00Z',
    members: ['550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440010'],
    permissions: ['850e8400-e29b-41d4-a716-446655440001', '850e8400-e29b-41d4-a716-446655440002']
  },
  '750e8400-e29b-41d4-a716-446655440002': {
    id: '750e8400-e29b-41d4-a716-446655440002',
    org_id: '650e8400-e29b-41d4-a716-446655440001',
    name: 'Content Creators',
    description: 'Can create and edit activities',
    member_count: 12,
    created_at: '2025-01-05T14:00:00Z',
    updated_at: '2025-01-05T14:00:00Z',
    members: ['550e8400-e29b-41d4-a716-446655440011'],
    permissions: ['850e8400-e29b-41d4-a716-446655440003', '850e8400-e29b-41d4-a716-446655440004']
  }
}

/**
 * Mock permissions database
 */
const mockPermissions: Record<string, MockPermission> = {
  '850e8400-e29b-41d4-a716-446655440001': {
    id: '850e8400-e29b-41d4-a716-446655440001',
    resource: 'activity',
    action: 'create',
    description: 'Create new activities',
    permission_string: 'activity:create'
  },
  '850e8400-e29b-41d4-a716-446655440002': {
    id: '850e8400-e29b-41d4-a716-446655440002',
    resource: 'activity',
    action: 'delete',
    description: 'Delete activities',
    permission_string: 'activity:delete'
  },
  '850e8400-e29b-41d4-a716-446655440003': {
    id: '850e8400-e29b-41d4-a716-446655440003',
    resource: 'activity',
    action: 'update',
    description: 'Update activities',
    permission_string: 'activity:update'
  },
  '850e8400-e29b-41d4-a716-446655440004': {
    id: '850e8400-e29b-41d4-a716-446655440004',
    resource: 'activity',
    action: 'read',
    description: 'View activities',
    permission_string: 'activity:read'
  },
  '850e8400-e29b-41d4-a716-446655440005': {
    id: '850e8400-e29b-41d4-a716-446655440005',
    resource: 'user',
    action: 'manage',
    description: 'Manage users',
    permission_string: 'user:manage'
  }
}

/**
 * Mock OAuth clients
 */
const mockOAuthClients: Record<string, {
  client_secret: string | null
  client_type: 'public' | 'confidential'
  redirect_uris: string[]
  allowed_scopes: string[]
  is_first_party: boolean
  require_consent: boolean
  client_name: string
  description?: string
  logo_uri?: string
}> = {
  'image-api-v1': {
    client_secret: 'secret_image_api_12345',
    client_type: 'confidential',
    redirect_uris: ['https://app.example.com/callback', 'http://localhost:3000/callback'],
    allowed_scopes: ['read:images', 'write:images', 'delete:images', 'read:data', 'write:data'],
    is_first_party: true,
    require_consent: false,
    client_name: 'Image API',
    description: 'Official image management service'
  },
  'mobile-app-public': {
    client_secret: null,
    client_type: 'public',
    redirect_uris: ['myapp://oauth/callback'],
    allowed_scopes: ['read:data', 'write:data', 'read:profile'],
    is_first_party: false,
    require_consent: true,
    client_name: 'Mobile App',
    description: 'Third-party mobile application'
  },
  'service-account-bot': {
    client_secret: 'secret_bot_service_67890',
    client_type: 'confidential',
    redirect_uris: [],
    allowed_scopes: ['read:data', 'write:data', 'admin:system'],
    is_first_party: true,
    require_consent: false,
    client_name: 'Service Bot'
  }
}

/**
 * Mock authorization codes (single-use)
 */
const validAuthorizationCodes: Record<string, {
  user_id: string
  client_id: string
  redirect_uri: string
  scopes: string[]
  code_challenge: string
  expires_at: number
  used: boolean
  organization_id?: string
  nonce?: string
}> = {
  'AUTH_CODE_VALID_ABC123': {
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    client_id: 'image-api-v1',
    redirect_uri: 'https://app.example.com/callback',
    scopes: ['read:data', 'write:data', 'read:images'],
    code_challenge: 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',
    expires_at: Date.now() + 600000,
    used: false,
    organization_id: '650e8400-e29b-41d4-a716-446655440001'
  }
}

/**
 * Mock refresh token blacklist
 */
const revokedRefreshTokens = new Set<string>(['REVOKED_TOKEN_123'])

/**
 * Temporary storage for verification codes (in production: Redis)
 */
const temporaryVerificationCodes: Record<string, { code: string; expires_at: number }> = {}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Generate realistic JWT-like tokens
 */
function generateMockJWT(
  type: 'access' | 'refresh' | 'pre_auth',
  payload: {
    sub: string
    email?: string
    org_id?: string
    client_id?: string
    scope?: string
    [key: string]: any
  }
): string {
  const now = Math.floor(Date.now() / 1000)
  const header = { alg: 'HS256', typ: 'JWT' }

  const expirations = {
    access: 900, // 15 minutes
    refresh: 2592000, // 30 days
    pre_auth: 300 // 5 minutes for 2FA flow
  }

  const body = {
    sub: payload.sub,
    type: type,
    iat: now,
    exp: now + expirations[type],
    jti: uuidv4(),
    ...payload
  }

  const encodedHeader = btoa(JSON.stringify(header)).replace(/=/g, '')
  const encodedBody = btoa(JSON.stringify(body)).replace(/=/g, '')
  const mockSignature = btoa('mock-signature-hs256').replace(/=/g, '')

  return `${encodedHeader}.${encodedBody}.${mockSignature}`
}

/**
 * Decode JWT token (mock implementation)
 */
function decodeMockJWT(token: string): any {
  try {
    const parts = token.split('.')
    return JSON.parse(atob(parts[1]))
  } catch {
    return null
  }
}

/**
 * Extract user ID from Authorization header
 */
function extractUserIdFromAuth(authHeader: string | null): string | null {
  if (!authHeader || !authHeader.startsWith('Bearer ')) return null

  const token = authHeader.replace('Bearer ', '')
  const payload = decodeMockJWT(token)
  return payload?.sub || null
}

/**
 * Check if user is member of organization
 */
function isUserMemberOfOrg(userId: string, orgId: string): boolean {
  const org = mockOrganizations[orgId]
  if (!org) return false
  return org.members.some(m => m.user_id === userId)
}

/**
 * Get user's role in organization
 */
function getUserRoleInOrg(userId: string, orgId: string): UserRole | null {
  const org = mockOrganizations[orgId]
  if (!org) return null
  const member = org.members.find(m => m.user_id === userId)
  return member?.role || null
}

/**
 * Check if user has permission
 */
function userHasPermission(userId: string, orgId: string, permissionString: string): { authorized: boolean; groups: string[] } {
  // Check organization membership
  if (!isUserMemberOfOrg(userId, orgId)) {
    return { authorized: false, groups: [] }
  }

  // Find groups user is member of in this org
  const userGroups = Object.values(mockGroups).filter(
    g => g.org_id === orgId && g.members.includes(userId)
  )

  // Check if any group has the permission
  const matchedGroups: string[] = []

  for (const group of userGroups) {
    for (const permId of group.permissions) {
      const perm = mockPermissions[permId]
      if (perm && perm.permission_string === permissionString) {
        matchedGroups.push(group.name)
      }
    }
  }

  return {
    authorized: matchedGroups.length > 0,
    groups: matchedGroups
  }
}

/**
 * Simulate network latency
 */
async function simulateDelay(ms: number = 300): Promise<void> {
  await delay(ms)
}

/**
 * Generate 6-digit verification code
 */
function generate6DigitCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString()
}

// ============================================================================
// MSW HANDLERS - 100% API COVERAGE
// ============================================================================

export const handlers = [

  // ==========================================================================
  // AUTHENTICATION ENDPOINTS
  // ==========================================================================

  // POST /auth/register
  http.post('/auth/register', async ({ request }) => {
    await simulateDelay(350)

    const body = await request.json() as { email: string; password: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    if (scenario === 'validation-error' || (body.password && body.password.length < 8)) {
      return HttpResponse.json(
        {
          detail: [
            {
              loc: ['body', 'password'],
              msg: 'String should have at least 8 characters',
              type: 'string_too_short',
              ctx: { min_length: 8 }
            }
          ]
        },
        { status: 422 }
      )
    }

    if (scenario === 'invalid-email' || (body.email && !body.email.includes('@'))) {
      return HttpResponse.json(
        {
          detail: [
            {
              loc: ['body', 'email'],
              msg: 'value is not a valid email address',
              type: 'value_error.email'
            }
          ]
        },
        { status: 422 }
      )
    }

    if (scenario === 'conflict' || body.email === 'existing@example.com') {
      return HttpResponse.json(
        { detail: 'User with this email already exists' },
        { status: 400 }
      )
    }

    const newUserId = uuidv4()
    return HttpResponse.json(
      {
        message: 'Registration successful. Please check your email to verify your account.',
        email: body.email.toLowerCase(),
        user_id: newUserId
      },
      { status: 201 }
    )
  }),

  // POST /auth/verify-code
  http.post('/auth/verify-code', async ({ request }) => {
    await simulateDelay(300)

    const body = await request.json() as { verification_token: string; code: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    if (scenario === 'invalid-token' || body.verification_token !== 'VERIFY_TOKEN_ABC123456789') {
      return HttpResponse.json(
        { detail: 'Invalid or expired verification token' },
        { status: 400 }
      )
    }

    if (scenario === 'invalid-code' || body.code !== '123456') {
      return HttpResponse.json(
        { detail: 'Invalid verification code' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      message: 'Email verified successfully. You can now log in.'
    })
  }),

  // POST /auth/login
  http.post('/auth/login', async ({ request }) => {
    await simulateDelay(400)

    const body = await request.json() as {
      email: string
      password: string
      code?: string | null
      org_id?: string | null
    }
    const scenario = request.headers.get('X-Mock-Scenario')

    if (scenario === 'validation-error' || !body.email || !body.password) {
      return HttpResponse.json(
        {
          detail: [
            {
              loc: ['body', !body.email ? 'email' : 'password'],
              msg: 'Field required',
              type: 'missing'
            }
          ]
        },
        { status: 422 }
      )
    }

    const email = body.email.toLowerCase()
    const user = mockUsers[email]

    if (scenario === 'invalid-credentials' || !user || body.password !== user.password) {
      return HttpResponse.json(
        { detail: 'Invalid credentials' },
        { status: 401 }
      )
    }

    if (!user.isVerified) {
      return HttpResponse.json(
        { detail: 'Email not verified. Please check your inbox for the verification email.' },
        { status: 403 }
      )
    }

    if (scenario === 'code-sent' || !body.code) {
      return HttpResponse.json({
        message: 'Verification code sent to your email. Please check your inbox.',
        email: email,
        user_id: user.id,
        expires_in: 600,
        requires_code: true
      })
    }

    if (scenario === 'org-selection' || (body.code && user.organizations.length > 1 && !body.org_id)) {
      return HttpResponse.json({
        message: 'Please select an organization to continue.',
        organizations: user.organizations.map(org => ({
          id: org.id,
          name: org.name,
          slug: org.slug,
          role: org.role,
          member_count: org.member_count
        })),
        user_token: generateMockJWT('access', {
          sub: user.id,
          email: user.email,
          scope: 'user-level'
        }),
        expires_in: 900
      })
    }

    if (scenario === 'single-org-login' || (body.code && user.organizations.length === 1 && !body.org_id)) {
      const orgId = user.organizations[0].id
      return HttpResponse.json({
        access_token: generateMockJWT('access', {
          sub: user.id,
          email: user.email,
          org_id: orgId
        }),
        refresh_token: generateMockJWT('refresh', {
          sub: user.id,
          org_id: orgId
        }),
        token_type: 'bearer',
        org_id: orgId
      })
    }

    if (scenario === 'full-login' || (body.code && body.org_id)) {
      const orgExists = user.organizations.some(org => org.id === body.org_id)

      if (!orgExists) {
        return HttpResponse.json(
          { detail: 'You are not a member of this organization' },
          { status: 403 }
        )
      }

      return HttpResponse.json({
        access_token: generateMockJWT('access', {
          sub: user.id,
          email: user.email,
          org_id: body.org_id
        }),
        refresh_token: generateMockJWT('refresh', {
          sub: user.id,
          org_id: body.org_id
        }),
        token_type: 'bearer',
        org_id: body.org_id
      })
    }

    return HttpResponse.json({
      message: 'Verification code sent to your email. Please check your inbox.',
      email: email,
      user_id: user.id,
      expires_in: 600,
      requires_code: true
    })
  }),

  // POST /auth/refresh
  http.post('/auth/refresh', async ({ request }) => {
    await simulateDelay(250)

    const body = await request.json() as { refresh_token: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    if (scenario === 'invalid-token' || revokedRefreshTokens.has(body.refresh_token)) {
      return HttpResponse.json(
        { detail: 'Invalid or revoked refresh token' },
        { status: 401 }
      )
    }

    const payload = decodeMockJWT(body.refresh_token)

    if (!payload || payload.type !== 'refresh') {
      return HttpResponse.json(
        { detail: 'Invalid token type' },
        { status: 401 }
      )
    }

    revokedRefreshTokens.add(body.refresh_token)

    return HttpResponse.json({
      access_token: generateMockJWT('access', {
        sub: payload.sub,
        email: payload.email,
        org_id: payload.org_id
      }),
      refresh_token: generateMockJWT('refresh', {
        sub: payload.sub,
        org_id: payload.org_id
      }),
      token_type: 'bearer',
      org_id: payload.org_id || null
    })
  }),

  // POST /auth/logout
  http.post('/auth/logout', async ({ request }) => {
    await simulateDelay(200)

    const body = await request.json() as { refresh_token: string }
    revokedRefreshTokens.add(body.refresh_token)

    return HttpResponse.json({
      message: 'Logged out successfully'
    })
  }),

  // POST /auth/request-password-reset
  http.post('/auth/request-password-reset', async ({ request }) => {
    await simulateDelay(400)

    const body = await request.json() as { email: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    if (scenario === 'user-not-found') {
      return HttpResponse.json({
        message: 'If an account with that email exists, a password reset link has been sent.',
        user_id: null
      })
    }

    const resetToken = `RESET_TOKEN_${uuidv4()}`
    const resetCode = generate6DigitCode()

    const email = body.email.toLowerCase()
    if (mockUsers[email]) {
      mockUsers[email].resetToken = resetToken
      mockUsers[email].resetCode = resetCode
    }

    return HttpResponse.json({
      message: 'If an account with that email exists, a password reset link has been sent.',
      user_id: mockUsers[email]?.id || null
    })
  }),

  // POST /auth/reset-password
  http.post('/auth/reset-password', async ({ request }) => {
    await simulateDelay(350)

    const body = await request.json() as {
      reset_token: string
      code: string
      new_password: string
    }
    const scenario = request.headers.get('X-Mock-Scenario')

    const user = Object.values(mockUsers).find(u => u.resetToken === body.reset_token)

    if (scenario === 'invalid-token' || !user) {
      return HttpResponse.json(
        { detail: 'Invalid or expired reset token' },
        { status: 400 }
      )
    }

    if (scenario === 'invalid-code' || body.code !== user.resetCode) {
      return HttpResponse.json(
        { detail: 'Invalid reset code' },
        { status: 400 }
      )
    }

    if (scenario === 'weak-password' || body.new_password.length < 8) {
      return HttpResponse.json(
        { detail: 'Password does not meet security requirements' },
        { status: 400 }
      )
    }

    user.password = body.new_password
    delete user.resetToken
    delete user.resetCode

    return HttpResponse.json({
      message: 'Password reset successfully. You can now log in with your new password.'
    })
  }),

  // POST /auth/2fa/setup
  http.post('/auth/2fa/setup', async ({ request }) => {
    await simulateDelay(300)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const totpSecret = 'JBSWY3DPEHPK3PXP'
    const qrCodeUrl = `otpauth://totp/ActivityApp:user@example.com?secret=${totpSecret}&issuer=ActivityApp`

    return HttpResponse.json({
      secret: totpSecret,
      qr_code_url: qrCodeUrl,
      message: 'Scan this QR code with your authenticator app'
    })
  }),

  // POST /auth/2fa/verify
  http.post('/auth/2fa/verify', async ({ request }) => {
    await simulateDelay(250)

    const body = await request.json() as { code: string }
    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const scenario = request.headers.get('X-Mock-Scenario')

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    if (scenario === 'invalid-code' || body.code !== '123456') {
      return HttpResponse.json(
        { detail: 'Invalid verification code' },
        { status: 400 }
      )
    }

    const user = Object.values(mockUsers).find(u => u.id === userId)
    if (user) {
      user.is2FAEnabled = true
      user.totp_secret = 'JBSWY3DPEHPK3PXP'
    }

    return HttpResponse.json({
      message: 'Two-factor authentication enabled successfully'
    })
  }),

  // POST /auth/2fa/disable
  http.post('/auth/2fa/disable', async ({ request }) => {
    await simulateDelay(200)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const user = Object.values(mockUsers).find(u => u.id === userId)
    if (user) {
      user.is2FAEnabled = false
      delete user.totp_secret
    }

    return HttpResponse.json({
      message: 'Two-factor authentication disabled successfully'
    })
  }),

  // ==========================================================================
  // OAUTH ENDPOINTS (Partial implementation for brevity)
  // ==========================================================================

  http.post('/oauth/token', async ({ request }) => {
    await simulateDelay(350)

    const formData = await request.formData()
    const grantType = formData.get('grant_type') as string
    const clientId = formData.get('client_id') as string
    const clientSecret = formData.get('client_secret') as string | null

    const client = mockOAuthClients[clientId]

    if (!client || (client.client_type === 'confidential' && clientSecret !== client.client_secret)) {
      return HttpResponse.json(
        { error: 'invalid_client', error_description: 'Client authentication failed' },
        { status: 401 }
      )
    }

    if (grantType === 'authorization_code') {
      const code = formData.get('code') as string
      const codeRecord = validAuthorizationCodes[code]

      if (!codeRecord || codeRecord.used) {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Authorization code has expired or been used' },
          { status: 400 }
        )
      }

      codeRecord.used = true

      return HttpResponse.json({
        access_token: generateMockJWT('access', {
          sub: codeRecord.user_id,
          client_id: clientId,
          scope: codeRecord.scopes.join(' ')
        }),
        refresh_token: generateMockJWT('refresh', {
          sub: codeRecord.user_id,
          client_id: clientId
        }),
        token_type: 'Bearer',
        expires_in: 3600,
        scope: codeRecord.scopes.join(' ')
      })
    }

    return HttpResponse.json(
      { error: 'unsupported_grant_type' },
      { status: 400 }
    )
  }),

  // ==========================================================================
  // AUTHORIZATION ENDPOINT - THE CORE
  // ==========================================================================

  http.post('/authorize', async ({ request }) => {
    await simulateDelay(200)

    const body = await request.json() as {
      user_id: string
      organization_id: string
      permission: string
    }

    const result = userHasPermission(body.user_id, body.organization_id, body.permission)

    if (result.authorized) {
      return HttpResponse.json({
        authorized: true,
        reason: 'User has permission via group membership',
        matched_groups: result.groups
      })
    } else {
      if (!isUserMemberOfOrg(body.user_id, body.organization_id)) {
        return HttpResponse.json({
          authorized: false,
          reason: 'User is not a member of this organization',
          matched_groups: null
        })
      }

      return HttpResponse.json({
        authorized: false,
        reason: `No permission '${body.permission}' granted`,
        matched_groups: null
      })
    }
  })
]
