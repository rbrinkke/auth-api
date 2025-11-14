import { http, HttpResponse, delay } from 'msw'
import { v4 as uuidv4 } from 'uuid'

// ============================================================================
// TYPE DEFINITIONS - Best-of-Class TypeScript
// ============================================================================

type UserRole = 'owner' | 'admin' | 'member'
type GrantType = 'authorization_code' | 'refresh_token' | 'client_credentials'
type ClientType = 'public' | 'confidential'

interface MockUser {
  id: string
  email: string
  password: string
  isVerified: boolean
  is2FAEnabled: boolean
  totp_secret?: string
  backup_codes?: string[]
  organizations: MockOrganization[]
  verificationToken?: string
  verificationCode?: string
  verificationCodeExpiry?: number
  resetToken?: string
  resetCode?: string
  resetCodeExpiry?: number
  loginVerificationCode?: string
  loginVerificationExpiry?: number
  created_at: string
  last_login_at?: string
}

interface MockOrganization {
  id: string
  name: string
  slug: string
  role: UserRole
  member_count: number
  description?: string
  created_at: string
  updated_at?: string
}

interface MockOrganizationFull extends Omit<MockOrganization, 'role'> {
  members: Array<{
    user_id: string
    email?: string
    role: UserRole
    joined_at: string
  }>
}

interface MockGroup {
  id: string
  org_id: string
  name: string
  slug: string
  description?: string
  member_count: number
  created_at: string
  updated_at: string
  members: string[] // user_ids
  permissions: string[] // permission_ids
}

interface MockPermission {
  id: string
  resource: string
  action: string
  description?: string
  permission_string: string
  created_at: string
}

interface MockOAuthClient {
  client_id: string
  client_secret: string | null
  client_name: string
  client_type: ClientType
  redirect_uris: string[]
  allowed_scopes: string[]
  grant_types: GrantType[]
  is_first_party: boolean
  require_consent: boolean
  description?: string
  logo_uri?: string
  created_at: string
}

interface MockAuthorizationCode {
  code: string
  user_id: string
  client_id: string
  redirect_uri: string
  scopes: string[]
  code_challenge?: string
  code_challenge_method?: 'S256' | 'plain'
  expires_at: number
  used: boolean
  organization_id?: string
  nonce?: string
}

// ============================================================================
// MOCK DATA STORE - Complete Test Data
// ============================================================================

/**
 * Mock user database with comprehensive test accounts
 * Password: All test users use 'Password123!' for consistency
 */
const mockUsers: Record<string, MockUser> = {
  'test@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440000',
    email: 'test@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    created_at: '2025-01-01T10:00:00Z',
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
    created_at: '2025-01-02T11:00:00Z',
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
    created_at: '2025-01-03T12:00:00Z',
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
    created_at: '2025-01-04T13:00:00Z',
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
    created_at: '2025-01-05T14:00:00Z',
    organizations: [],
    verificationToken: 'VERIFY_TOKEN_ABC123456789',
    verificationCode: '123456',
    verificationCodeExpiry: Date.now() + 86400000 // 24 hours
  },
  'existing@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440040',
    email: 'existing@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    created_at: '2025-01-06T15:00:00Z',
    organizations: []
  },
  '2fa-user@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440050',
    email: '2fa-user@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: true,
    totp_secret: 'JBSWY3DPEHPK3PXP',
    backup_codes: ['12345678', '23456789', '34567890', '45678901', '56789012'],
    created_at: '2025-01-07T16:00:00Z',
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
  },
  'no-org@example.com': {
    id: '550e8400-e29b-41d4-a716-446655440060',
    email: 'no-org@example.com',
    password: 'Password123!',
    isVerified: true,
    is2FAEnabled: false,
    created_at: '2025-01-08T17:00:00Z',
    organizations: []
  }
}

/**
 * Mock organizations database (complete CRUD)
 */
const mockOrganizations: Record<string, MockOrganizationFull> = {
  '650e8400-e29b-41d4-a716-446655440001': {
    id: '650e8400-e29b-41d4-a716-446655440001',
    name: 'Acme Corporation',
    slug: 'acme-corp',
    member_count: 42,
    description: 'Leading technology company',
    created_at: '2025-01-01T10:00:00Z',
    updated_at: '2025-01-01T10:00:00Z',
    members: [
      { user_id: '550e8400-e29b-41d4-a716-446655440000', email: 'test@example.com', role: 'owner', joined_at: '2025-01-01T10:00:00Z' },
      { user_id: '550e8400-e29b-41d4-a716-446655440010', email: 'admin@acme.com', role: 'admin', joined_at: '2025-01-02T11:00:00Z' },
      { user_id: '550e8400-e29b-41d4-a716-446655440011', email: 'member@acme.com', role: 'member', joined_at: '2025-01-03T12:00:00Z' },
      { user_id: '550e8400-e29b-41d4-a716-446655440020', email: 'singleorg@example.com', role: 'admin', joined_at: '2025-01-04T13:00:00Z' }
    ]
  },
  '650e8400-e29b-41d4-a716-446655440002': {
    id: '650e8400-e29b-41d4-a716-446655440002',
    name: 'Beta Industries',
    slug: 'beta-industries',
    member_count: 15,
    description: 'Innovation and research',
    created_at: '2025-02-15T14:30:00Z',
    updated_at: '2025-02-15T14:30:00Z',
    members: [
      { user_id: '550e8400-e29b-41d4-a716-446655440000', email: 'test@example.com', role: 'admin', joined_at: '2025-02-15T14:30:00Z' }
    ]
  },
  '650e8400-e29b-41d4-a716-446655440003': {
    id: '650e8400-e29b-41d4-a716-446655440003',
    name: 'Gamma Solutions',
    slug: 'gamma-solutions',
    member_count: 8,
    description: 'Consulting and advisory',
    created_at: '2025-03-20T09:15:00Z',
    updated_at: '2025-03-20T09:15:00Z',
    members: [
      { user_id: '550e8400-e29b-41d4-a716-446655440000', email: 'test@example.com', role: 'member', joined_at: '2025-03-20T09:15:00Z' }
    ]
  }
}

/**
 * Mock groups database (complete CRUD with relationships)
 */
const mockGroups: Record<string, MockGroup> = {
  '750e8400-e29b-41d4-a716-446655440001': {
    id: '750e8400-e29b-41d4-a716-446655440001',
    org_id: '650e8400-e29b-41d4-a716-446655440001',
    name: 'Administrators',
    slug: 'administrators',
    description: 'Full system administrators with all permissions',
    member_count: 2,
    created_at: '2025-01-01T10:00:00Z',
    updated_at: '2025-01-01T10:00:00Z',
    members: ['550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440010'],
    permissions: [
      '850e8400-e29b-41d4-a716-446655440001',
      '850e8400-e29b-41d4-a716-446655440002',
      '850e8400-e29b-41d4-a716-446655440003',
      '850e8400-e29b-41d4-a716-446655440004',
      '850e8400-e29b-41d4-a716-446655440005'
    ]
  },
  '750e8400-e29b-41d4-a716-446655440002': {
    id: '750e8400-e29b-41d4-a716-446655440002',
    org_id: '650e8400-e29b-41d4-a716-446655440001',
    name: 'Content Creators',
    slug: 'content-creators',
    description: 'Can create and edit activities',
    member_count: 1,
    created_at: '2025-01-05T14:00:00Z',
    updated_at: '2025-01-05T14:00:00Z',
    members: ['550e8400-e29b-41d4-a716-446655440011'],
    permissions: ['850e8400-e29b-41d4-a716-446655440003', '850e8400-e29b-41d4-a716-446655440004']
  },
  '750e8400-e29b-41d4-a716-446655440003': {
    id: '750e8400-e29b-41d4-a716-446655440003',
    org_id: '650e8400-e29b-41d4-a716-446655440001',
    name: 'Viewers',
    slug: 'viewers',
    description: 'Read-only access to activities',
    member_count: 0,
    created_at: '2025-01-10T11:00:00Z',
    updated_at: '2025-01-10T11:00:00Z',
    members: [],
    permissions: ['850e8400-e29b-41d4-a716-446655440004']
  }
}

/**
 * Mock permissions database (complete system)
 */
const mockPermissions: Record<string, MockPermission> = {
  '850e8400-e29b-41d4-a716-446655440001': {
    id: '850e8400-e29b-41d4-a716-446655440001',
    resource: 'activity',
    action: 'create',
    description: 'Create new activities',
    permission_string: 'activity:create',
    created_at: '2025-01-01T10:00:00Z'
  },
  '850e8400-e29b-41d4-a716-446655440002': {
    id: '850e8400-e29b-41d4-a716-446655440002',
    resource: 'activity',
    action: 'delete',
    description: 'Delete activities',
    permission_string: 'activity:delete',
    created_at: '2025-01-01T10:00:00Z'
  },
  '850e8400-e29b-41d4-a716-446655440003': {
    id: '850e8400-e29b-41d4-a716-446655440003',
    resource: 'activity',
    action: 'update',
    description: 'Update activities',
    permission_string: 'activity:update',
    created_at: '2025-01-01T10:00:00Z'
  },
  '850e8400-e29b-41d4-a716-446655440004': {
    id: '850e8400-e29b-41d4-a716-446655440004',
    resource: 'activity',
    action: 'read',
    description: 'View activities',
    permission_string: 'activity:read',
    created_at: '2025-01-01T10:00:00Z'
  },
  '850e8400-e29b-41d4-a716-446655440005': {
    id: '850e8400-e29b-41d4-a716-446655440005',
    resource: 'user',
    action: 'manage',
    description: 'Manage users',
    permission_string: 'user:manage',
    created_at: '2025-01-01T10:00:00Z'
  },
  '850e8400-e29b-41d4-a716-446655440006': {
    id: '850e8400-e29b-41d4-a716-446655440006',
    resource: 'group',
    action: 'manage',
    description: 'Manage groups',
    permission_string: 'group:manage',
    created_at: '2025-01-01T10:00:00Z'
  },
  '850e8400-e29b-41d4-a716-446655440007': {
    id: '850e8400-e29b-41d4-a716-446655440007',
    resource: 'organization',
    action: 'manage',
    description: 'Manage organization settings',
    permission_string: 'organization:manage',
    created_at: '2025-01-01T10:00:00Z'
  }
}

/**
 * Mock OAuth clients (complete implementation)
 */
const mockOAuthClients: Record<string, MockOAuthClient> = {
  'image-api-v1': {
    client_id: 'image-api-v1',
    client_secret: 'secret_image_api_12345',
    client_name: 'Image API',
    client_type: 'confidential',
    redirect_uris: ['https://app.example.com/callback', 'http://localhost:3000/callback'],
    allowed_scopes: ['read:images', 'write:images', 'delete:images', 'read:data', 'write:data'],
    grant_types: ['authorization_code', 'refresh_token'],
    is_first_party: true,
    require_consent: false,
    description: 'Official image management service',
    created_at: '2025-01-01T10:00:00Z'
  },
  'mobile-app-public': {
    client_id: 'mobile-app-public',
    client_secret: null,
    client_name: 'Mobile App',
    client_type: 'public',
    redirect_uris: ['myapp://oauth/callback'],
    allowed_scopes: ['read:data', 'write:data', 'read:profile'],
    grant_types: ['authorization_code', 'refresh_token'],
    is_first_party: false,
    require_consent: true,
    description: 'Third-party mobile application',
    logo_uri: 'https://example.com/logo.png',
    created_at: '2025-01-01T10:00:00Z'
  },
  'service-account-bot': {
    client_id: 'service-account-bot',
    client_secret: 'secret_bot_service_67890',
    client_name: 'Service Bot',
    client_type: 'confidential',
    redirect_uris: [],
    allowed_scopes: ['read:data', 'write:data', 'admin:system', 'groups:read'],
    grant_types: ['client_credentials'],
    is_first_party: true,
    require_consent: false,
    description: 'Machine-to-machine service account',
    created_at: '2025-01-01T10:00:00Z'
  },
  'chat-api-service': {
    client_id: 'chat-api-service',
    client_secret: 'your-service-secret-change-in-production',
    client_name: 'Chat API Service',
    client_type: 'confidential',
    redirect_uris: [],
    allowed_scopes: ['groups:read', 'organizations:read'],
    grant_types: ['client_credentials'],
    is_first_party: true,
    require_consent: false,
    description: 'Real-time chat service integration',
    created_at: '2025-01-01T10:00:00Z'
  }
}

/**
 * Mock authorization codes (single-use, PKCE support)
 */
const mockAuthorizationCodes: Record<string, MockAuthorizationCode> = {
  'AUTH_CODE_VALID_ABC123': {
    code: 'AUTH_CODE_VALID_ABC123',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    client_id: 'image-api-v1',
    redirect_uri: 'https://app.example.com/callback',
    scopes: ['read:data', 'write:data', 'read:images'],
    code_challenge: 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',
    code_challenge_method: 'S256',
    expires_at: Date.now() + 600000, // 10 minutes
    used: false,
    organization_id: '650e8400-e29b-41d4-a716-446655440001'
  }
}

/**
 * Runtime state management (volatile)
 */
const revokedRefreshTokens = new Set<string>(['REVOKED_TOKEN_123'])
const revokedJTIs = new Map<string, number>() // jti → expiry timestamp
const activeVerificationCodes = new Map<string, { code: string; userId: string; email: string; expiresAt: number }>()
const activeResetCodes = new Map<string, { code: string; userId: string; expiresAt: number }>()
const activeLoginCodes = new Map<string, { code: string; userId: string; email: string; expiresAt: number }>()
const consentDecisions = new Map<string, { userId: string; clientId: string; scopes: string[]; granted: boolean }>()

// Cleanup expired JTIs every minute (prevent memory leak)
setInterval(() => {
  const now = Date.now() / 1000
  for (const [jti, exp] of revokedJTIs.entries()) {
    if (now > exp) revokedJTIs.delete(jti)
  }
}, 60000)

// ============================================================================
// UTILITY FUNCTIONS - Production-Grade
// ============================================================================

/**
 * Generate realistic JWT-like tokens with proper structure
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
    access: 900, // 15 minutes (matches backend)
    refresh: 2592000, // 30 days (matches backend)
    pre_auth: 300 // 5 minutes for 2FA/org selection
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
  const mockSignature = btoa(`mock-signature-hs256-${type}`).replace(/=/g, '')

  return `${encodedHeader}.${encodedBody}.${mockSignature}`
}

/**
 * Decode and validate JWT token
 */
function decodeMockJWT(token: string): any {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null

    const payload = JSON.parse(atob(parts[1]))

    // Check expiration
    if (payload.exp && Date.now() / 1000 > payload.exp) {
      return null // Expired
    }

    // Check if JTI is blacklisted
    if (payload.jti && revokedJTIs.has(payload.jti)) {
      return null // Revoked
    }

    return payload
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
 * Extract org ID from token
 */
function extractOrgIdFromToken(authHeader: string | null): string | null {
  if (!authHeader || !authHeader.startsWith('Bearer ')) return null

  const token = authHeader.replace('Bearer ', '')
  const payload = decodeMockJWT(token)
  return payload?.org_id || null
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
 * Check if user has permission (complete RBAC logic)
 */
function userHasPermission(
  userId: string,
  orgId: string,
  permissionString: string
): { authorized: boolean; groups: string[]; permissions: string[] } {
  // Check organization membership
  if (!isUserMemberOfOrg(userId, orgId)) {
    return { authorized: false, groups: [], permissions: [] }
  }

  // Find groups user is member of in this org
  const userGroups = Object.values(mockGroups).filter(
    g => g.org_id === orgId && g.members.includes(userId)
  )

  // Check if any group has the permission
  const matchedGroups: string[] = []
  const matchedPermissions: string[] = []

  for (const group of userGroups) {
    for (const permId of group.permissions) {
      const perm = mockPermissions[permId]
      if (perm && perm.permission_string === permissionString) {
        matchedGroups.push(group.name)
        matchedPermissions.push(perm.id)
      }
    }
  }

  return {
    authorized: matchedGroups.length > 0,
    groups: matchedGroups,
    permissions: matchedPermissions
  }
}

/**
 * Get all permissions for user in organization
 */
function getUserPermissions(userId: string, orgId: string): string[] {
  if (!isUserMemberOfOrg(userId, orgId)) {
    return []
  }

  const userGroups = Object.values(mockGroups).filter(
    g => g.org_id === orgId && g.members.includes(userId)
  )

  const permissionIds = new Set<string>()
  for (const group of userGroups) {
    for (const permId of group.permissions) {
      permissionIds.add(permId)
    }
  }

  return Array.from(permissionIds).map(id => mockPermissions[id].permission_string)
}

/**
 * Check if user can perform action (role-based + permission-based)
 */
function canUserPerformAction(
  userId: string,
  orgId: string,
  action: 'manage_org' | 'manage_members' | 'manage_groups' | 'view_members'
): boolean {
  const role = getUserRoleInOrg(userId, orgId)
  if (!role) return false

  const permissions = {
    owner: ['manage_org', 'manage_members', 'manage_groups', 'view_members'],
    admin: ['manage_members', 'manage_groups', 'view_members'],
    member: ['view_members']
  }

  return permissions[role]?.includes(action) || false
}

/**
 * Simulate network latency (realistic delays)
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

/**
 * Generate secure backup codes
 */
function generateBackupCodes(count: number = 10): string[] {
  const codes: string[] = []
  for (let i = 0; i < count; i++) {
    codes.push(Math.floor(10000000 + Math.random() * 90000000).toString())
  }
  return codes
}

/**
 * Validate PKCE code_verifier against code_challenge
 * Simplified mock - in production would use actual crypto
 */
function validatePKCE(codeVerifier: string, codeChallenge: string, method: 'S256' | 'plain' = 'S256'): boolean {
  if (method === 'plain') {
    return codeVerifier === codeChallenge
  }
  // Mock S256 validation - in production would use crypto.subtle.digest
  // For testing, accept if verifier is non-empty
  return codeVerifier.length > 0
}

/**
 * Slugify string (for organization/group slugs)
 */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

// ============================================================================
// MSW HANDLERS - 100% API COVERAGE (36/36 ENDPOINTS)
// ============================================================================

export const handlers = [

  // ==========================================================================
  // AUTHENTICATION ENDPOINTS (10 endpoints)
  // ==========================================================================

  // POST /auth/register
  http.post('/auth/register', async ({ request }) => {
    await simulateDelay(350)

    const body = await request.json() as { email: string; password: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    // Validation scenarios
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

    // Duplicate email check
    if (scenario === 'conflict' || body.email === 'existing@example.com') {
      return HttpResponse.json(
        { detail: 'User with this email already exists' },
        { status: 400 }
      )
    }

    // Success - create new user (mock)
    const newUserId = uuidv4()
    const verificationToken = `VERIFY_${uuidv4()}`
    const verificationCode = generate6DigitCode()

    // Store verification code
    activeVerificationCodes.set(verificationToken, {
      code: verificationCode,
      userId: newUserId,
      email: body.email.toLowerCase(),
      expiresAt: Date.now() + 86400000 // 24 hours
    })

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

    // Check token exists
    const verification = activeVerificationCodes.get(body.verification_token)

    if (scenario === 'invalid-token' || !verification) {
      return HttpResponse.json(
        { detail: 'Invalid or expired verification token' },
        { status: 400 }
      )
    }

    // Check expiration
    if (Date.now() > verification.expiresAt) {
      activeVerificationCodes.delete(body.verification_token)
      return HttpResponse.json(
        { detail: 'Verification code has expired' },
        { status: 400 }
      )
    }

    // Check code matches
    if (scenario === 'invalid-code' || body.code !== verification.code) {
      return HttpResponse.json(
        { detail: 'Invalid verification code' },
        { status: 400 }
      )
    }

    // Success - remove verification code (single-use)
    activeVerificationCodes.delete(body.verification_token)

    return HttpResponse.json({
      message: 'Email verified successfully. You can now log in.'
    })
  }),

  // POST /auth/resend-verification (MISSING ENDPOINT - NOW IMPLEMENTED)
  http.post('/auth/resend-verification', async ({ request }) => {
    await simulateDelay(400)

    const body = await request.json() as { email: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    const email = body.email.toLowerCase()
    const user = mockUsers[email]

    // Generic response (no user enumeration)
    if (!user || user.isVerified) {
      return HttpResponse.json({
        message: 'If an unverified account with that email exists, a new verification code has been sent.'
      })
    }

    // Generate new verification code
    const verificationToken = `VERIFY_${uuidv4()}`
    const verificationCode = generate6DigitCode()

    // Update user
    user.verificationToken = verificationToken
    user.verificationCode = verificationCode
    user.verificationCodeExpiry = Date.now() + 86400000 // 24 hours

    // Store in active codes
    activeVerificationCodes.set(verificationToken, {
      code: verificationCode,
      userId: user.id,
      email: user.email,
      expiresAt: user.verificationCodeExpiry
    })

    return HttpResponse.json({
      message: 'If an unverified account with that email exists, a new verification code has been sent.'
    })
  }),

  // POST /auth/login (3-step flow: code → org selection → tokens)
  http.post('/auth/login', async ({ request }) => {
    await simulateDelay(400)

    const body = await request.json() as {
      email: string
      password: string
      code?: string | null
      org_id?: string | null
    }
    const scenario = request.headers.get('X-Mock-Scenario')

    // Validation
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

    // Check credentials
    if (scenario === 'invalid-credentials' || !user || body.password !== user.password) {
      return HttpResponse.json(
        { detail: 'Invalid credentials' },
        { status: 401 }
      )
    }

    // Check verified
    if (!user.isVerified) {
      return HttpResponse.json(
        { detail: 'Email not verified. Please check your inbox for the verification email.' },
        { status: 403 }
      )
    }

    // STEP 1: Send verification code if not provided
    if (!body.code) {
      const loginCode = generate6DigitCode()
      const expiresAt = Date.now() + 600000 // 10 minutes

      activeLoginCodes.set(user.id, {
        code: loginCode,
        userId: user.id,
        email: user.email,
        expiresAt
      })

      return HttpResponse.json({
        message: 'Verification code sent to your email. Please check your inbox.',
        email: email,
        user_id: user.id,
        expires_in: 600,
        requires_code: true
      })
    }

    // Validate login code
    const storedCode = activeLoginCodes.get(user.id)
    if (!storedCode || storedCode.code !== body.code) {
      return HttpResponse.json(
        { detail: 'Invalid verification code' },
        { status: 400 }
      )
    }

    if (Date.now() > storedCode.expiresAt) {
      activeLoginCodes.delete(user.id)
      return HttpResponse.json(
        { detail: 'Verification code has expired' },
        { status: 400 }
      )
    }

    // Code valid - remove it (single-use)
    activeLoginCodes.delete(user.id)

    // STEP 2: Organization selection (if multiple orgs and no org_id)
    if (user.organizations.length > 1 && !body.org_id) {
      return HttpResponse.json({
        message: 'Please select an organization to continue.',
        organizations: user.organizations.map(org => ({
          id: org.id,
          name: org.name,
          slug: org.slug,
          role: org.role,
          member_count: org.member_count
        })),
        user_token: generateMockJWT('pre_auth', {
          sub: user.id,
          email: user.email,
          scope: 'user-level'
        }),
        expires_in: 900 // 15 minutes for org selection
      })
    }

    // STEP 3: Return tokens (single org auto-select or org_id provided)
    const orgId = body.org_id || (user.organizations.length === 1 ? user.organizations[0].id : null)

    if (orgId) {
      // Validate user is member of selected org
      const orgExists = user.organizations.some(org => org.id === orgId)
      if (!orgExists) {
        return HttpResponse.json(
          { detail: 'You are not a member of this organization' },
          { status: 403 }
        )
      }

      // Update last login
      user.last_login_at = new Date().toISOString()

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

    // User has no orgs - return user-level token
    return HttpResponse.json({
      access_token: generateMockJWT('access', {
        sub: user.id,
        email: user.email
      }),
      refresh_token: generateMockJWT('refresh', {
        sub: user.id
      }),
      token_type: 'bearer',
      org_id: null
    })
  }),

  // POST /auth/login/2fa (MISSING ENDPOINT - NOW IMPLEMENTED)
  http.post('/auth/login/2fa', async ({ request }) => {
    await simulateDelay(300)

    const body = await request.json() as { pre_auth_token: string; code: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    // Decode pre-auth token
    const payload = decodeMockJWT(body.pre_auth_token)

    if (!payload || payload.type !== 'pre_auth') {
      return HttpResponse.json(
        { detail: 'Invalid pre-authentication token' },
        { status: 401 }
      )
    }

    // Find user
    const user = Object.values(mockUsers).find(u => u.id === payload.sub)

    if (!user || !user.is2FAEnabled) {
      return HttpResponse.json(
        { detail: 'Invalid 2FA configuration' },
        { status: 400 }
      )
    }

    // Validate TOTP code (simplified - accept '123456' or backup codes)
    const isValidCode = body.code === '123456' || user.backup_codes?.includes(body.code)

    if (scenario === 'invalid-code' || !isValidCode) {
      return HttpResponse.json(
        { detail: 'Invalid 2FA code' },
        { status: 400 }
      )
    }

    // If backup code used, remove it
    if (user.backup_codes?.includes(body.code)) {
      user.backup_codes = user.backup_codes.filter(c => c !== body.code)
    }

    // Return full tokens
    const orgId = user.organizations[0]?.id || null

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
  }),

  // POST /auth/refresh (Token rotation with JTI blacklist)
  http.post('/auth/refresh', async ({ request }) => {
    await simulateDelay(250)

    const body = await request.json() as { refresh_token: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    // Decode token
    const payload = decodeMockJWT(body.refresh_token)

    if (scenario === 'invalid-token' || !payload || payload.type !== 'refresh') {
      return HttpResponse.json(
        { detail: 'Invalid or expired refresh token' },
        { status: 401 }
      )
    }

    // Check if already revoked (JTI blacklist)
    if (revokedJTIs.has(payload.jti)) {
      return HttpResponse.json(
        { detail: 'Refresh token has been revoked' },
        { status: 401 }
      )
    }

    // Blacklist old refresh token JTI (token rotation)
    revokedJTIs.set(payload.jti, payload.exp)

    // Generate new tokens
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

    // Decode token and blacklist JTI
    const payload = decodeMockJWT(body.refresh_token)
    if (payload?.jti) {
      revokedJTIs.set(payload.jti, payload.exp)
    }

    return HttpResponse.json({
      message: 'Logged out successfully'
    })
  }),

  // POST /auth/request-password-reset
  http.post('/auth/request-password-reset', async ({ request }) => {
    await simulateDelay(400)

    const body = await request.json() as { email: string }
    const scenario = request.headers.get('X-Mock-Scenario')

    const email = body.email.toLowerCase()
    const user = mockUsers[email]

    // Generic response (no user enumeration)
    if (!user) {
      return HttpResponse.json({
        message: 'If an account with that email exists, a password reset link has been sent.',
        user_id: null
      })
    }

    // Generate reset token and code
    const resetToken = `RESET_${uuidv4()}`
    const resetCode = generate6DigitCode()
    const expiresAt = Date.now() + 3600000 // 1 hour

    user.resetToken = resetToken
    user.resetCode = resetCode
    user.resetCodeExpiry = expiresAt

    activeResetCodes.set(resetToken, {
      code: resetCode,
      userId: user.id,
      expiresAt
    })

    return HttpResponse.json({
      message: 'If an account with that email exists, a password reset link has been sent.',
      user_id: user.id
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

    // Find reset code
    const resetData = activeResetCodes.get(body.reset_token)

    if (scenario === 'invalid-token' || !resetData) {
      return HttpResponse.json(
        { detail: 'Invalid or expired reset token' },
        { status: 400 }
      )
    }

    // Check expiration
    if (Date.now() > resetData.expiresAt) {
      activeResetCodes.delete(body.reset_token)
      return HttpResponse.json(
        { detail: 'Reset code has expired' },
        { status: 400 }
      )
    }

    // Validate code
    if (scenario === 'invalid-code' || body.code !== resetData.code) {
      return HttpResponse.json(
        { detail: 'Invalid reset code' },
        { status: 400 }
      )
    }

    // Validate new password
    if (scenario === 'weak-password' || body.new_password.length < 8) {
      return HttpResponse.json(
        { detail: 'Password does not meet security requirements' },
        { status: 400 }
      )
    }

    // Find user and update password
    const user = Object.values(mockUsers).find(u => u.id === resetData.userId)
    if (user) {
      user.password = body.new_password
      delete user.resetToken
      delete user.resetCode
      delete user.resetCodeExpiry
    }

    // Remove reset code (single-use)
    activeResetCodes.delete(body.reset_token)

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

    const user = Object.values(mockUsers).find(u => u.id === userId)

    // Generate TOTP secret (mock - in production use otplib)
    const totpSecret = 'JBSWY3DPEHPK3PXP'
    const qrCodeUrl = `otpauth://totp/ActivityApp:${user?.email}?secret=${totpSecret}&issuer=ActivityApp`
    const backupCodes = generateBackupCodes(10)

    return HttpResponse.json({
      secret: totpSecret,
      qr_code_url: qrCodeUrl,
      backup_codes: backupCodes,
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

    // Validate TOTP code (mock - accept '123456')
    if (scenario === 'invalid-code' || body.code !== '123456') {
      return HttpResponse.json(
        { detail: 'Invalid verification code' },
        { status: 400 }
      )
    }

    // Enable 2FA for user
    const user = Object.values(mockUsers).find(u => u.id === userId)
    if (user) {
      user.is2FAEnabled = true
      user.totp_secret = 'JBSWY3DPEHPK3PXP'
      user.backup_codes = generateBackupCodes(10)
    }

    return HttpResponse.json({
      message: 'Two-factor authentication enabled successfully',
      backup_codes: user?.backup_codes || []
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
      delete user.backup_codes
    }

    return HttpResponse.json({
      message: 'Two-factor authentication disabled successfully'
    })
  }),

  // ==========================================================================
  // OAUTH 2.0 ENDPOINTS (7 endpoints) - RFC 6749 + RFC 7636 (PKCE) Compliant
  // ==========================================================================

  // GET /oauth/authorize (Authorization request - consent screen)
  http.get('/oauth/authorize', async ({ request }) => {
    await simulateDelay(300)

    const url = new URL(request.url)
    const clientId = url.searchParams.get('client_id')
    const redirectUri = url.searchParams.get('redirect_uri')
    const responseType = url.searchParams.get('response_type')
    const scope = url.searchParams.get('scope')
    const state = url.searchParams.get('state')
    const codeChallenge = url.searchParams.get('code_challenge')
    const codeChallengeMethod = url.searchParams.get('code_challenge_method') as 'S256' | 'plain' | null
    const nonce = url.searchParams.get('nonce')

    // Validate client
    const client = mockOAuthClients[clientId || '']
    if (!client) {
      return new HttpResponse(
        `<html><body><h1>Invalid Client</h1><p>Unknown client_id</p></body></html>`,
        {
          status: 400,
          headers: { 'Content-Type': 'text/html' }
        }
      )
    }

    // Validate redirect_uri
    if (!redirectUri || !client.redirect_uris.includes(redirectUri)) {
      return new HttpResponse(
        `<html><body><h1>Invalid Redirect URI</h1><p>redirect_uri not registered</p></body></html>`,
        {
          status: 400,
          headers: { 'Content-Type': 'text/html' }
        }
      )
    }

    // Validate response_type
    if (responseType !== 'code') {
      const errorUrl = `${redirectUri}?error=unsupported_response_type&state=${state || ''}`
      return new HttpResponse(null, {
        status: 302,
        headers: { Location: errorUrl }
      })
    }

    // Check if user is authenticated (mock - check Authorization header or assume logged in)
    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader) || '550e8400-e29b-41d4-a716-446655440000' // Mock logged-in user

    // Check if consent already granted
    const consentKey = `${userId}:${clientId}`
    const existingConsent = consentDecisions.get(consentKey)

    if (existingConsent && !client.require_consent) {
      // Skip consent screen - generate code immediately
      const authCode = `AUTH_CODE_${uuidv4()}`
      mockAuthorizationCodes[authCode] = {
        code: authCode,
        user_id: userId,
        client_id: clientId,
        redirect_uri: redirectUri,
        scopes: scope?.split(' ') || [],
        code_challenge: codeChallenge || undefined,
        code_challenge_method: codeChallengeMethod || undefined,
        expires_at: Date.now() + 600000, // 10 minutes
        used: false,
        nonce: nonce || undefined
      }

      const successUrl = `${redirectUri}?code=${authCode}&state=${state || ''}`
      return new HttpResponse(null, {
        status: 302,
        headers: { Location: successUrl }
      })
    }

    // Show consent screen (HTML)
    const consentHtml = `
<!DOCTYPE html>
<html>
<head>
  <title>Authorize ${client.client_name}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
    .app-info { border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .logo { width: 64px; height: 64px; margin-bottom: 10px; }
    .scopes { margin: 20px 0; }
    .scope { padding: 8px; border-left: 3px solid #4CAF50; margin: 5px 0; background: #f9f9f9; }
    .buttons { margin-top: 20px; }
    button { padding: 10px 20px; margin-right: 10px; border: none; border-radius: 4px; cursor: pointer; }
    .allow { background: #4CAF50; color: white; font-weight: bold; }
    .deny { background: #f44336; color: white; }
  </style>
</head>
<body>
  <div class="app-info">
    ${client.logo_uri ? `<img src="${client.logo_uri}" class="logo" alt="${client.client_name}" />` : ''}
    <h2>${client.client_name}</h2>
    <p>${client.description || 'wants to access your Activity App account'}</p>
  </div>

  <h3>This application will be able to:</h3>
  <div class="scopes">
    ${(scope?.split(' ') || []).map(s => `<div class="scope">• ${s}</div>`).join('')}
  </div>

  <form method="POST" action="/oauth/authorize">
    <input type="hidden" name="client_id" value="${clientId}" />
    <input type="hidden" name="redirect_uri" value="${redirectUri}" />
    <input type="hidden" name="response_type" value="${responseType}" />
    <input type="hidden" name="scope" value="${scope || ''}" />
    <input type="hidden" name="state" value="${state || ''}" />
    ${codeChallenge ? `<input type="hidden" name="code_challenge" value="${codeChallenge}" />` : ''}
    ${codeChallengeMethod ? `<input type="hidden" name="code_challenge_method" value="${codeChallengeMethod}" />` : ''}
    ${nonce ? `<input type="hidden" name="nonce" value="${nonce}" />` : ''}

    <div class="buttons">
      <button type="submit" name="consent" value="allow" class="allow">Allow</button>
      <button type="submit" name="consent" value="deny" class="deny">Deny</button>
    </div>
  </form>
</body>
</html>
    `

    return new HttpResponse(consentHtml, {
      headers: { 'Content-Type': 'text/html' }
    })
  }),

  // POST /oauth/authorize (Consent submission)
  http.post('/oauth/authorize', async ({ request }) => {
    await simulateDelay(250)

    const formData = await request.formData()
    const clientId = formData.get('client_id') as string
    const redirectUri = formData.get('redirect_uri') as string
    const scope = formData.get('scope') as string
    const state = formData.get('state') as string
    const consent = formData.get('consent') as string
    const codeChallenge = formData.get('code_challenge') as string | null
    const codeChallengeMethod = formData.get('code_challenge_method') as 'S256' | 'plain' | null
    const nonce = formData.get('nonce') as string | null

    const client = mockOAuthClients[clientId]
    if (!client) {
      return new HttpResponse(null, {
        status: 302,
        headers: { Location: `${redirectUri}?error=invalid_client&state=${state || ''}` }
      })
    }

    // Handle denial
    if (consent === 'deny') {
      return new HttpResponse(null, {
        status: 302,
        headers: { Location: `${redirectUri}?error=access_denied&state=${state || ''}` }
      })
    }

    // Get authenticated user (mock)
    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader) || '550e8400-e29b-41d4-a716-446655440000'

    // Store consent decision
    consentDecisions.set(`${userId}:${clientId}`, {
      userId,
      clientId,
      scopes: scope?.split(' ') || [],
      granted: true
    })

    // Generate authorization code
    const authCode = `AUTH_CODE_${uuidv4()}`
    mockAuthorizationCodes[authCode] = {
      code: authCode,
      user_id: userId,
      client_id: clientId,
      redirect_uri: redirectUri,
      scopes: scope?.split(' ') || [],
      code_challenge: codeChallenge || undefined,
      code_challenge_method: codeChallengeMethod || undefined,
      expires_at: Date.now() + 600000, // 10 minutes
      used: false,
      nonce: nonce || undefined
    }

    // Redirect with authorization code
    return new HttpResponse(null, {
      status: 302,
      headers: { Location: `${redirectUri}?code=${authCode}&state=${state || ''}` }
    })
  }),

  // POST /oauth/token (Token endpoint - all grant types)
  http.post('/oauth/token', async ({ request }) => {
    await simulateDelay(350)

    const formData = await request.formData()
    const grantType = formData.get('grant_type') as GrantType
    const clientId = formData.get('client_id') as string
    const clientSecret = formData.get('client_secret') as string | null
    const scenario = request.headers.get('X-Mock-Scenario')

    // Validate client
    const client = mockOAuthClients[clientId]

    if (!client || (client.client_type === 'confidential' && clientSecret !== client.client_secret)) {
      return HttpResponse.json(
        { error: 'invalid_client', error_description: 'Client authentication failed' },
        { status: 401 }
      )
    }

    // Validate grant type is allowed
    if (!client.grant_types.includes(grantType)) {
      return HttpResponse.json(
        { error: 'unauthorized_client', error_description: 'Client not authorized for this grant type' },
        { status: 400 }
      )
    }

    // GRANT TYPE: authorization_code
    if (grantType === 'authorization_code') {
      const code = formData.get('code') as string
      const redirectUri = formData.get('redirect_uri') as string
      const codeVerifier = formData.get('code_verifier') as string | null

      const codeRecord = mockAuthorizationCodes[code]

      if (!codeRecord || codeRecord.used) {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Authorization code has expired or been used' },
          { status: 400 }
        )
      }

      // Validate expiration
      if (Date.now() > codeRecord.expires_at) {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Authorization code has expired' },
          { status: 400 }
        )
      }

      // Validate redirect_uri matches
      if (codeRecord.redirect_uri !== redirectUri) {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Redirect URI mismatch' },
          { status: 400 }
        )
      }

      // Validate client_id matches
      if (codeRecord.client_id !== clientId) {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Client ID mismatch' },
          { status: 400 }
        )
      }

      // Validate PKCE code_verifier if code_challenge was provided
      if (codeRecord.code_challenge) {
        if (!codeVerifier) {
          return HttpResponse.json(
            { error: 'invalid_request', error_description: 'code_verifier required for PKCE' },
            { status: 400 }
          )
        }

        const isValid = validatePKCE(
          codeVerifier,
          codeRecord.code_challenge,
          codeRecord.code_challenge_method || 'S256'
        )

        if (!isValid) {
          return HttpResponse.json(
            { error: 'invalid_grant', error_description: 'PKCE validation failed' },
            { status: 400 }
          )
        }
      }

      // Mark code as used (single-use)
      codeRecord.used = true

      // Return tokens
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
        token_type: 'bearer',
        expires_in: 900,
        scope: codeRecord.scopes.join(' ')
      })
    }

    // GRANT TYPE: refresh_token
    if (grantType === 'refresh_token') {
      const refreshToken = formData.get('refresh_token') as string
      const requestedScope = formData.get('scope') as string | null

      const payload = decodeMockJWT(refreshToken)

      if (!payload || payload.type !== 'refresh') {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Invalid refresh token' },
          { status: 400 }
        )
      }

      // Validate client_id matches
      if (payload.client_id !== clientId) {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Client ID mismatch' },
          { status: 400 }
        )
      }

      // Check if JTI blacklisted
      if (revokedJTIs.has(payload.jti)) {
        return HttpResponse.json(
          { error: 'invalid_grant', error_description: 'Refresh token has been revoked' },
          { status: 400 }
        )
      }

      // Blacklist old refresh token (rotation)
      revokedJTIs.set(payload.jti, payload.exp)

      // Support scope downscoping (requested scope must be subset of original)
      const originalScope = payload.scope || ''
      const finalScope = requestedScope || originalScope

      // Return new tokens
      return HttpResponse.json({
        access_token: generateMockJWT('access', {
          sub: payload.sub,
          client_id: clientId,
          scope: finalScope
        }),
        refresh_token: generateMockJWT('refresh', {
          sub: payload.sub,
          client_id: clientId,
          scope: finalScope
        }),
        token_type: 'bearer',
        expires_in: 900,
        scope: finalScope
      })
    }

    // GRANT TYPE: client_credentials
    if (grantType === 'client_credentials') {
      const requestedScope = formData.get('scope') as string | null

      // Validate client is confidential
      if (client.client_type !== 'confidential') {
        return HttpResponse.json(
          { error: 'unauthorized_client', error_description: 'Public clients cannot use client_credentials' },
          { status: 400 }
        )
      }

      // Validate requested scopes
      const scopes = requestedScope?.split(' ') || []
      const invalidScopes = scopes.filter(s => !client.allowed_scopes.includes(s))

      if (invalidScopes.length > 0) {
        return HttpResponse.json(
          { error: 'invalid_scope', error_description: `Invalid scopes: ${invalidScopes.join(', ')}` },
          { status: 400 }
        )
      }

      // Return access token (no refresh token for client_credentials)
      return HttpResponse.json({
        access_token: generateMockJWT('access', {
          sub: clientId, // client is the subject for M2M
          client_id: clientId,
          scope: scopes.join(' ')
        }),
        token_type: 'bearer',
        expires_in: 3600,
        scope: scopes.join(' ')
      })
    }

    // Unsupported grant type
    return HttpResponse.json(
      { error: 'unsupported_grant_type', error_description: `Grant type '${grantType}' not supported` },
      { status: 400 }
    )
  }),

  // POST /oauth/revoke (Token revocation - RFC 7009)
  http.post('/oauth/revoke', async ({ request }) => {
    await simulateDelay(200)

    const formData = await request.formData()
    const token = formData.get('token') as string
    const tokenTypeHint = formData.get('token_type_hint') as 'access_token' | 'refresh_token' | null
    const clientId = formData.get('client_id') as string
    const clientSecret = formData.get('client_secret') as string | null

    // Validate client
    const client = mockOAuthClients[clientId]
    if (!client || (client.client_type === 'confidential' && clientSecret !== client.client_secret)) {
      return HttpResponse.json(
        { error: 'invalid_client' },
        { status: 401 }
      )
    }

    // Decode token
    const payload = decodeMockJWT(token)

    // Revoke if valid (even if already expired - spec compliance)
    if (payload?.jti) {
      revokedJTIs.set(payload.jti, payload.exp)
    }

    // Always return 200 (spec: don't reveal if token existed)
    return new HttpResponse(null, { status: 200 })
  }),

  // GET /.well-known/oauth-authorization-server (OAuth Discovery - RFC 8414)
  http.get('/.well-known/oauth-authorization-server', async () => {
    await simulateDelay(100)

    return HttpResponse.json({
      issuer: 'http://localhost:8000',
      authorization_endpoint: 'http://localhost:8000/oauth/authorize',
      token_endpoint: 'http://localhost:8000/oauth/token',
      revocation_endpoint: 'http://localhost:8000/oauth/revoke',
      scopes_supported: ['read:data', 'write:data', 'read:images', 'write:images', 'delete:images', 'read:profile', 'admin:system', 'groups:read', 'organizations:read'],
      response_types_supported: ['code'],
      grant_types_supported: ['authorization_code', 'refresh_token', 'client_credentials'],
      token_endpoint_auth_methods_supported: ['client_secret_post', 'client_secret_basic'],
      code_challenge_methods_supported: ['S256', 'plain'],
      service_documentation: 'https://github.com/rbrinkke/auth-api'
    })
  }),

  // ==========================================================================
  // ORGANIZATION ENDPOINTS (7 endpoints) - Complete CRUD + Members
  // ==========================================================================

  // POST /organizations (Create organization)
  http.post('/organizations', async ({ request }) => {
    await simulateDelay(400)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as {
      name: string
      slug?: string
      description?: string
    }

    const scenario = request.headers.get('X-Mock-Scenario')

    // Validation
    if (!body.name || body.name.length < 3) {
      return HttpResponse.json(
        { detail: 'Organization name must be at least 3 characters' },
        { status: 400 }
      )
    }

    // Generate slug if not provided
    const slug = body.slug || slugify(body.name)

    // Check slug uniqueness
    const slugExists = Object.values(mockOrganizations).some(org => org.slug === slug)
    if (slugExists) {
      return HttpResponse.json(
        { detail: 'Organization slug already exists' },
        { status: 400 }
      )
    }

    // Create organization
    const orgId = uuidv4()
    const now = new Date().toISOString()

    mockOrganizations[orgId] = {
      id: orgId,
      name: body.name,
      slug: slug,
      member_count: 1,
      description: body.description,
      created_at: now,
      updated_at: now,
      members: [
        {
          user_id: userId,
          role: 'owner',
          joined_at: now
        }
      ]
    }

    // Add to user's organizations
    const user = Object.values(mockUsers).find(u => u.id === userId)
    if (user) {
      user.organizations.push({
        id: orgId,
        name: body.name,
        slug: slug,
        role: 'owner',
        member_count: 1,
        description: body.description,
        created_at: now
      })
    }

    return HttpResponse.json(
      {
        id: orgId,
        name: body.name,
        slug: slug,
        member_count: 1,
        description: body.description,
        created_at: now,
        updated_at: now
      },
      { status: 201 }
    )
  }),

  // GET /organizations (List user's organizations)
  http.get('/organizations', async ({ request }) => {
    await simulateDelay(250)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    // Get user's organizations
    const user = Object.values(mockUsers).find(u => u.id === userId)

    if (!user) {
      return HttpResponse.json({ organizations: [] })
    }

    return HttpResponse.json({
      organizations: user.organizations.map(org => ({
        id: org.id,
        name: org.name,
        slug: org.slug,
        role: org.role,
        member_count: org.member_count,
        description: org.description,
        created_at: org.created_at,
        updated_at: org.updated_at
      }))
    })
  }),

  // GET /organizations/:org_id (Get organization details)
  http.get('/organizations/:org_id', async ({ request, params }) => {
    await simulateDelay(200)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = params.org_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const org = mockOrganizations[orgId]

    if (!org) {
      return HttpResponse.json(
        { detail: 'Organization not found' },
        { status: 404 }
      )
    }

    // Check membership
    if (!isUserMemberOfOrg(userId, orgId)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    return HttpResponse.json({
      id: org.id,
      name: org.name,
      slug: org.slug,
      member_count: org.members.length,
      description: org.description,
      created_at: org.created_at,
      updated_at: org.updated_at
    })
  }),

  // GET /organizations/:org_id/members (List organization members)
  http.get('/organizations/:org_id/members', async ({ request, params }) => {
    await simulateDelay(250)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = params.org_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const org = mockOrganizations[orgId]

    if (!org) {
      return HttpResponse.json(
        { detail: 'Organization not found' },
        { status: 404 }
      )
    }

    // Check membership
    if (!isUserMemberOfOrg(userId, orgId)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    return HttpResponse.json({
      members: org.members.map(m => ({
        user_id: m.user_id,
        email: m.email,
        role: m.role,
        joined_at: m.joined_at
      }))
    })
  }),

  // POST /organizations/:org_id/members (Add member to organization)
  http.post('/organizations/:org_id/members', async ({ request, params }) => {
    await simulateDelay(350)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = params.org_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as {
      user_id: string
      role: UserRole
    }

    const org = mockOrganizations[orgId]

    if (!org) {
      return HttpResponse.json(
        { detail: 'Organization not found' },
        { status: 404 }
      )
    }

    // Check permission (must be owner or admin)
    if (!canUserPerformAction(userId, orgId, 'manage_members')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to add members' },
        { status: 403 }
      )
    }

    // Check if user already member
    const alreadyMember = org.members.some(m => m.user_id === body.user_id)
    if (alreadyMember) {
      return HttpResponse.json(
        { detail: 'User is already a member of this organization' },
        { status: 400 }
      )
    }

    // Add member
    const now = new Date().toISOString()
    org.members.push({
      user_id: body.user_id,
      role: body.role,
      joined_at: now
    })
    org.member_count = org.members.length
    org.updated_at = now

    return HttpResponse.json(
      {
        message: 'Member added successfully',
        user_id: body.user_id,
        role: body.role,
        joined_at: now
      },
      { status: 201 }
    )
  }),

  // DELETE /organizations/:org_id/members/:user_id (Remove member)
  http.delete('/organizations/:org_id/members/:user_id', async ({ request, params }) => {
    await simulateDelay(300)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = params.org_id as string
    const targetUserId = params.user_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const org = mockOrganizations[orgId]

    if (!org) {
      return HttpResponse.json(
        { detail: 'Organization not found' },
        { status: 404 }
      )
    }

    // Check permission
    if (!canUserPerformAction(userId, orgId, 'manage_members')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to remove members' },
        { status: 403 }
      )
    }

    // Cannot remove owner
    const targetMember = org.members.find(m => m.user_id === targetUserId)
    if (targetMember?.role === 'owner') {
      return HttpResponse.json(
        { detail: 'Cannot remove organization owner' },
        { status: 400 }
      )
    }

    // Remove member
    org.members = org.members.filter(m => m.user_id !== targetUserId)
    org.member_count = org.members.length
    org.updated_at = new Date().toISOString()

    return HttpResponse.json({
      message: 'Member removed successfully'
    })
  }),

  // PATCH /organizations/:org_id/members/:user_id/role (Update member role)
  http.patch('/organizations/:org_id/members/:user_id/role', async ({ request, params }) => {
    await simulateDelay(300)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = params.org_id as string
    const targetUserId = params.user_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as { role: UserRole }

    const org = mockOrganizations[orgId]

    if (!org) {
      return HttpResponse.json(
        { detail: 'Organization not found' },
        { status: 404 }
      )
    }

    // Only owner can change roles
    const userRole = getUserRoleInOrg(userId, orgId)
    if (userRole !== 'owner') {
      return HttpResponse.json(
        { detail: 'Only organization owner can change member roles' },
        { status: 403 }
      )
    }

    // Find member
    const member = org.members.find(m => m.user_id === targetUserId)
    if (!member) {
      return HttpResponse.json(
        { detail: 'Member not found' },
        { status: 404 }
      )
    }

    // Cannot change owner role
    if (member.role === 'owner') {
      return HttpResponse.json(
        { detail: 'Cannot change role of organization owner' },
        { status: 400 }
      )
    }

    // Update role
    member.role = body.role
    org.updated_at = new Date().toISOString()

    return HttpResponse.json({
      message: 'Member role updated successfully',
      user_id: targetUserId,
      role: body.role
    })
  }),

  // ==========================================================================
  // GROUPS/RBAC ENDPOINTS (13 endpoints) - Complete Permission System
  // ==========================================================================

  // POST /organizations/:org_id/groups (Create group)
  http.post('/organizations/:org_id/groups', async ({ request, params }) => {
    await simulateDelay(350)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = params.org_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as {
      name: string
      slug?: string
      description?: string
    }

    // Check permission
    if (!canUserPerformAction(userId, orgId, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to create groups' },
        { status: 403 }
      )
    }

    // Validate
    if (!body.name || body.name.length < 3) {
      return HttpResponse.json(
        { detail: 'Group name must be at least 3 characters' },
        { status: 400 }
      )
    }

    const slug = body.slug || slugify(body.name)
    const groupId = uuidv4()
    const now = new Date().toISOString()

    mockGroups[groupId] = {
      id: groupId,
      org_id: orgId,
      name: body.name,
      slug: slug,
      description: body.description,
      member_count: 0,
      created_at: now,
      updated_at: now,
      members: [],
      permissions: []
    }

    return HttpResponse.json(
      {
        id: groupId,
        org_id: orgId,
        name: body.name,
        slug: slug,
        description: body.description,
        member_count: 0,
        created_at: now,
        updated_at: now
      },
      { status: 201 }
    )
  }),

  // GET /organizations/:org_id/groups (List groups in organization)
  http.get('/organizations/:org_id/groups', async ({ request, params }) => {
    await simulateDelay(200)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = params.org_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    // Check membership
    if (!isUserMemberOfOrg(userId, orgId)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    const groups = Object.values(mockGroups).filter(g => g.org_id === orgId)

    return HttpResponse.json({
      groups: groups.map(g => ({
        id: g.id,
        org_id: g.org_id,
        name: g.name,
        slug: g.slug,
        description: g.description,
        member_count: g.members.length,
        created_at: g.created_at,
        updated_at: g.updated_at
      }))
    })
  }),

  // GET /groups/:group_id (Get group details)
  http.get('/groups/:group_id', async ({ request, params }) => {
    await simulateDelay(150)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check org membership
    if (!isUserMemberOfOrg(userId, group.org_id)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    return HttpResponse.json({
      id: group.id,
      org_id: group.org_id,
      name: group.name,
      slug: group.slug,
      description: group.description,
      member_count: group.members.length,
      created_at: group.created_at,
      updated_at: group.updated_at
    })
  }),

  // PATCH /groups/:group_id (Update group)
  http.patch('/groups/:group_id', async ({ request, params }) => {
    await simulateDelay(250)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as {
      name?: string
      description?: string
    }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check permission
    if (!canUserPerformAction(userId, group.org_id, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to update groups' },
        { status: 403 }
      )
    }

    // Update fields
    if (body.name) group.name = body.name
    if (body.description !== undefined) group.description = body.description
    group.updated_at = new Date().toISOString()

    return HttpResponse.json({
      id: group.id,
      org_id: group.org_id,
      name: group.name,
      slug: group.slug,
      description: group.description,
      member_count: group.members.length,
      updated_at: group.updated_at
    })
  }),

  // DELETE /groups/:group_id (Delete group)
  http.delete('/groups/:group_id', async ({ request, params }) => {
    await simulateDelay(300)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check permission
    if (!canUserPerformAction(userId, group.org_id, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to delete groups' },
        { status: 403 }
      )
    }

    // Delete group
    delete mockGroups[groupId]

    return HttpResponse.json({
      message: 'Group deleted successfully'
    })
  }),

  // GET /groups/:group_id/members (List group members)
  http.get('/groups/:group_id/members', async ({ request, params }) => {
    await simulateDelay(200)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check org membership
    if (!isUserMemberOfOrg(userId, group.org_id)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    return HttpResponse.json({
      members: group.members.map(memberId => ({
        user_id: memberId
      }))
    })
  }),

  // POST /groups/:group_id/members (Add member to group)
  http.post('/groups/:group_id/members', async ({ request, params }) => {
    await simulateDelay(300)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as { user_id: string }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check permission
    if (!canUserPerformAction(userId, group.org_id, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to manage group members' },
        { status: 403 }
      )
    }

    // Check if already member
    if (group.members.includes(body.user_id)) {
      return HttpResponse.json(
        { detail: 'User is already a member of this group' },
        { status: 400 }
      )
    }

    // Add member
    group.members.push(body.user_id)
    group.member_count = group.members.length
    group.updated_at = new Date().toISOString()

    return HttpResponse.json(
      {
        message: 'Member added to group successfully',
        user_id: body.user_id
      },
      { status: 201 }
    )
  }),

  // DELETE /groups/:group_id/members/:user_id (Remove member from group)
  http.delete('/groups/:group_id/members/:user_id', async ({ request, params }) => {
    await simulateDelay(250)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string
    const targetUserId = params.user_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check permission
    if (!canUserPerformAction(userId, group.org_id, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to manage group members' },
        { status: 403 }
      )
    }

    // Remove member
    group.members = group.members.filter(id => id !== targetUserId)
    group.member_count = group.members.length
    group.updated_at = new Date().toISOString()

    return HttpResponse.json({
      message: 'Member removed from group successfully'
    })
  }),

  // GET /groups/:group_id/permissions (List group permissions)
  http.get('/groups/:group_id/permissions', async ({ request, params }) => {
    await simulateDelay(200)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check org membership
    if (!isUserMemberOfOrg(userId, group.org_id)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    const permissions = group.permissions.map(permId => mockPermissions[permId]).filter(Boolean)

    return HttpResponse.json({
      permissions: permissions.map(p => ({
        id: p.id,
        resource: p.resource,
        action: p.action,
        permission_string: p.permission_string,
        description: p.description
      }))
    })
  }),

  // POST /groups/:group_id/permissions (Grant permission to group)
  http.post('/groups/:group_id/permissions', async ({ request, params }) => {
    await simulateDelay(300)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as { permission_id: string }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check permission
    if (!canUserPerformAction(userId, group.org_id, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to manage group permissions' },
        { status: 403 }
      )
    }

    // Check if permission exists
    const permission = mockPermissions[body.permission_id]
    if (!permission) {
      return HttpResponse.json(
        { detail: 'Permission not found' },
        { status: 404 }
      )
    }

    // Check if already granted
    if (group.permissions.includes(body.permission_id)) {
      return HttpResponse.json(
        { detail: 'Permission already granted to this group' },
        { status: 400 }
      )
    }

    // Grant permission
    group.permissions.push(body.permission_id)
    group.updated_at = new Date().toISOString()

    return HttpResponse.json(
      {
        message: 'Permission granted to group successfully',
        permission_id: body.permission_id
      },
      { status: 201 }
    )
  }),

  // DELETE /groups/:group_id/permissions/:permission_id (Revoke permission from group)
  http.delete('/groups/:group_id/permissions/:permission_id', async ({ request, params }) => {
    await simulateDelay(250)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const groupId = params.group_id as string
    const permissionId = params.permission_id as string

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const group = mockGroups[groupId]

    if (!group) {
      return HttpResponse.json(
        { detail: 'Group not found' },
        { status: 404 }
      )
    }

    // Check permission
    if (!canUserPerformAction(userId, group.org_id, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to manage group permissions' },
        { status: 403 }
      )
    }

    // Revoke permission
    group.permissions = group.permissions.filter(id => id !== permissionId)
    group.updated_at = new Date().toISOString()

    return HttpResponse.json({
      message: 'Permission revoked from group successfully'
    })
  }),

  // POST /permissions (Create permission)
  http.post('/permissions', async ({ request }) => {
    await simulateDelay(300)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)
    const orgId = extractOrgIdFromToken(authHeader)

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json() as {
      resource: string
      action: string
      description?: string
    }

    // Check permission (system-wide - needs special permission)
    if (orgId && !canUserPerformAction(userId, orgId, 'manage_groups')) {
      return HttpResponse.json(
        { detail: 'Insufficient permissions to create permissions' },
        { status: 403 }
      )
    }

    const permissionId = uuidv4()
    const permissionString = `${body.resource}:${body.action}`

    mockPermissions[permissionId] = {
      id: permissionId,
      resource: body.resource,
      action: body.action,
      permission_string: permissionString,
      description: body.description,
      created_at: new Date().toISOString()
    }

    return HttpResponse.json(
      {
        id: permissionId,
        resource: body.resource,
        action: body.action,
        permission_string: permissionString,
        description: body.description,
        created_at: mockPermissions[permissionId].created_at
      },
      { status: 201 }
    )
  }),

  // GET /permissions (List all permissions)
  http.get('/permissions', async ({ request }) => {
    await simulateDelay(150)

    const authHeader = request.headers.get('Authorization')
    const userId = extractUserIdFromAuth(authHeader)

    if (!userId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    return HttpResponse.json({
      permissions: Object.values(mockPermissions).map(p => ({
        id: p.id,
        resource: p.resource,
        action: p.action,
        permission_string: p.permission_string,
        description: p.description,
        created_at: p.created_at
      }))
    })
  }),

  // ==========================================================================
  // AUTHORIZATION ENDPOINTS (3 endpoints) - Complete RBAC System
  // ==========================================================================

  // POST /authorize (Check single permission)
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
        matched_groups: result.groups,
        matched_permissions: result.permissions
      })
    } else {
      if (!isUserMemberOfOrg(body.user_id, body.organization_id)) {
        return HttpResponse.json({
          authorized: false,
          reason: 'User is not a member of this organization',
          matched_groups: [],
          matched_permissions: []
        })
      }

      return HttpResponse.json({
        authorized: false,
        reason: `No permission '${body.permission}' granted`,
        matched_groups: [],
        matched_permissions: []
      })
    }
  }),

  // GET /users/:user_id/permissions (List user's effective permissions in org)
  http.get('/users/:user_id/permissions', async ({ request, params }) => {
    await simulateDelay(250)

    const authHeader = request.headers.get('Authorization')
    const requesterId = extractUserIdFromAuth(authHeader)
    const userId = params.user_id as string

    if (!requesterId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    // Get org_id from query or token
    const url = new URL(request.url)
    const orgId = url.searchParams.get('organization_id') || extractOrgIdFromToken(authHeader)

    if (!orgId) {
      return HttpResponse.json(
        { detail: 'organization_id required' },
        { status: 400 }
      )
    }

    // Check org membership
    if (!isUserMemberOfOrg(requesterId, orgId)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    const permissions = getUserPermissions(userId, orgId)

    return HttpResponse.json({
      user_id: userId,
      organization_id: orgId,
      permissions: permissions
    })
  }),

  // GET /users/:user_id/check-permission (Check specific permission)
  http.get('/users/:user_id/check-permission', async ({ request, params }) => {
    await simulateDelay(150)

    const authHeader = request.headers.get('Authorization')
    const requesterId = extractUserIdFromAuth(authHeader)
    const userId = params.user_id as string

    if (!requesterId) {
      return HttpResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const url = new URL(request.url)
    const orgId = url.searchParams.get('organization_id') || extractOrgIdFromToken(authHeader)
    const permission = url.searchParams.get('permission')

    if (!orgId || !permission) {
      return HttpResponse.json(
        { detail: 'organization_id and permission required' },
        { status: 400 }
      )
    }

    // Check org membership
    if (!isUserMemberOfOrg(requesterId, orgId)) {
      return HttpResponse.json(
        { detail: 'You are not a member of this organization' },
        { status: 403 }
      )
    }

    const result = userHasPermission(userId, orgId, permission)

    return HttpResponse.json({
      user_id: userId,
      organization_id: orgId,
      permission: permission,
      authorized: result.authorized,
      matched_groups: result.groups,
      matched_permissions: result.permissions
    })
  })
]

