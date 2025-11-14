/**
 * 🎯 100% MSW Handlers Test Suite - COMPLETE
 *
 * Tests ALL 41 backend endpoints systematically
 * Run with: npm run test:complete
 */

import { describe, it, expect, beforeAll } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Setup MSW server
const server = setupServer(...handlers)

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'bypass' })
  return () => server.close()
})

// Helper function
async function testEndpoint(
  method: string,
  path: string,
  body?: any,
  expectedStatus: number = 200
) {
  const options: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' }
  }

  if (body) {
    options.body = JSON.stringify(body)
  }

  const response = await fetch(`http://localhost${path}`, options)
  expect(response.status).toBe(expectedStatus)

  if (response.status === 204) {
    return null
  }

  const data = await response.json()
  return data
}

// =============================================================================
// 1. AUTHENTICATION ENDPOINTS (11 endpoints)
// =============================================================================
describe('1. Authentication Endpoints', () => {

  it('1.1 POST /api/auth/register - Create new user', async () => {
    const data = await testEndpoint('POST', '/api/auth/register', {
      email: 'newuser@test.com',
      password: 'Password123!'
    }, 201)

    expect(data.email).toBe('newuser@test.com')
    expect(data.user_id).toBeTruthy()
    expect(data.message).toContain('registered')
  })

  it('1.2 POST /api/auth/verify-code - Verify email', async () => {
    const data = await testEndpoint('POST', '/api/auth/verify-code', {
      verification_token: 'VERIFY_TOKEN_ABC123456789',
      code: '123456'
    })

    expect(data.message).toBeTruthy()
  })

  it('1.3 POST /api/auth/login (Step 1) - Send verification code', async () => {
    const data = await testEndpoint('POST', '/api/auth/login', {
      email: 'test@example.com',
      password: 'Password123!'
    })

    expect(data.requires_code).toBe(true)
    expect(data.user_id).toBeTruthy()
    expect(data.email).toBe('test@example.com')
    expect(data.expires_in).toBe(600)
  })

  it('1.4 POST /api/auth/login (Step 2) - Verify code → Org selection', async () => {
    const data = await testEndpoint('POST', '/api/auth/login', {
      email: 'test@example.com',
      password: 'Password123!',
      code: '123456'
    })

    expect(Array.isArray(data.organizations)).toBe(true)
    expect(data.organizations.length).toBeGreaterThan(0)
    expect(data.message).toContain('organization')
  })

  it('1.5 POST /api/auth/login (Step 3) - Select org → Tokens', async () => {
    const data = await testEndpoint('POST', '/api/auth/login', {
      email: 'test@example.com',
      password: 'Password123!',
      code: '123456',
      org_id: '650e8400-e29b-41d4-a716-446655440001'
    })

    expect(data.access_token).toBeTruthy()
    expect(data.refresh_token).toBeTruthy()
    expect(data.token_type).toBe('bearer')
    expect(data.org_id).toBe('650e8400-e29b-41d4-a716-446655440001')
  })

  it('1.6 POST /api/auth/login - Single org auto-select', async () => {
    const data = await testEndpoint('POST', '/api/auth/login', {
      email: 'singleorg@example.com',
      password: 'Password123!',
      code: '123456'
    })

    expect(data.access_token).toBeTruthy()
    expect(data.refresh_token).toBeTruthy()
  })

  it('1.7 POST /api/auth/refresh - Refresh token', async () => {
    const data = await testEndpoint('POST', '/api/auth/refresh', {
      refresh_token: 'mock-refresh-token'
    })

    expect(data.access_token).toBeTruthy()
    expect(data.refresh_token).toBeTruthy()
  })

  it('1.8 POST /api/auth/logout - Logout', async () => {
    const data = await testEndpoint('POST', '/api/auth/logout', {
      refresh_token: 'mock-refresh-token'
    })

    expect(data.message).toContain('logged out')
  })

  it('1.9 POST /api/auth/request-password-reset - Request reset', async () => {
    const data = await testEndpoint('POST', '/api/auth/request-password-reset', {
      email: 'test@example.com'
    })

    expect(data.message).toBeTruthy()
  })

  it('1.10 POST /api/auth/reset-password - Reset password', async () => {
    const data = await testEndpoint('POST', '/api/auth/reset-password', {
      reset_token: 'RESET_TOKEN_XYZ',
      code: '123456',
      new_password: 'NewPassword123!'
    })

    expect(data.message).toContain('reset')
  })

  it('1.11 POST /api/auth/2fa/setup - Setup 2FA', async () => {
    const data = await testEndpoint('POST', '/api/auth/2fa/setup', {})

    expect(data.secret).toBeTruthy()
    expect(data.qr_code_uri).toBeTruthy()
    expect(Array.isArray(data.backup_codes)).toBe(true)
  })
})

// =============================================================================
// 2. OAUTH 2.0 ENDPOINTS (5 endpoints)
// =============================================================================
describe('2. OAuth 2.0 Endpoints', () => {

  it('2.1 GET /.well-known/oauth-authorization-server - Discovery', async () => {
    const data = await testEndpoint('GET', '/.well-known/oauth-authorization-server')

    expect(data.issuer).toBeTruthy()
    expect(data.authorization_endpoint).toBeTruthy()
    expect(data.token_endpoint).toBeTruthy()
    expect(Array.isArray(data.grant_types_supported)).toBe(true)
  })

  it('2.2 POST /oauth/token - Authorization Code Grant', async () => {
    const data = await testEndpoint('POST', '/oauth/token', {
      grant_type: 'authorization_code',
      code: 'AUTH_CODE_VALID_ABC123',
      redirect_uri: 'https://app.example.com/callback',
      code_verifier: 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk',
      client_id: 'image-api-v1',
      client_secret: 'secret_image_api_12345'
    })

    expect(data.access_token).toBeTruthy()
    expect(data.token_type).toBe('Bearer')
  })

  it('2.3 POST /oauth/token - Refresh Token Grant', async () => {
    const data = await testEndpoint('POST', '/oauth/token', {
      grant_type: 'refresh_token',
      refresh_token: 'mock-refresh',
      client_id: 'image-api-v1',
      client_secret: 'secret_image_api_12345'
    })

    expect(data.access_token).toBeTruthy()
  })

  it('2.4 POST /oauth/token - Client Credentials Grant', async () => {
    const data = await testEndpoint('POST', '/oauth/token', {
      grant_type: 'client_credentials',
      scope: 'read:data write:data',
      client_id: 'service-account-bot',
      client_secret: 'secret_bot_service_67890'
    })

    expect(data.access_token).toBeTruthy()
    expect(data.token_type).toBe('Bearer')
    expect(data.refresh_token).toBeUndefined() // No refresh token for client_credentials
  })

  it('2.5 POST /oauth/revoke - Token revocation', async () => {
    await testEndpoint('POST', '/oauth/revoke', {
      token: 'some-token',
      client_id: 'image-api-v1',
      client_secret: 'secret_image_api_12345'
    })
    // Always returns 200 per RFC 7009
  })
})

// =============================================================================
// 3. ORGANIZATION ENDPOINTS (7 endpoints)
// =============================================================================
describe('3. Organization Endpoints', () => {

  it('3.1 POST /api/auth/organizations - Create org', async () => {
    const data = await testEndpoint('POST', '/api/auth/organizations', {
      name: 'Test Org',
      slug: 'test-org',
      description: 'Test organization'
    }, 201)

    expect(data.id).toBeTruthy()
    expect(data.name).toBe('Test Org')
    expect(data.slug).toBe('test-org')
  })

  it('3.2 GET /api/auth/organizations - List user orgs', async () => {
    const data = await testEndpoint('GET', '/api/auth/organizations')

    expect(Array.isArray(data)).toBe(true)
  })

  it('3.3 GET /api/auth/organizations/:org_id - Get org', async () => {
    const data = await testEndpoint('GET', '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001')

    expect(data.id).toBe('650e8400-e29b-41d4-a716-446655440001')
    expect(data.name).toBeTruthy()
  })

  it('3.4 GET /api/auth/organizations/:org_id/members - List members', async () => {
    const data = await testEndpoint('GET', '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members')

    expect(Array.isArray(data)).toBe(true)
  })

  it('3.5 POST /api/auth/organizations/:org_id/members - Add member', async () => {
    const data = await testEndpoint('POST', '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members', {
      user_id: '550e8400-e29b-41d4-a716-446655440011',
      role: 'member'
    }, 201)

    expect(data.user_id).toBe('550e8400-e29b-41d4-a716-446655440011')
  })

  it('3.6 PATCH /api/auth/organizations/:org_id/members/:user_id/role - Update role', async () => {
    const data = await testEndpoint('PATCH', '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440011/role', {
      role: 'admin'
    })

    expect(data.message || data.member).toBeTruthy()
  })

  it('3.7 DELETE /api/auth/organizations/:org_id/members/:user_id - Remove member', async () => {
    const data = await testEndpoint('DELETE', '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440011')

    expect(data.message).toBeTruthy()
  })
})

// =============================================================================
// 4. GROUPS & RBAC ENDPOINTS (13 endpoints)
// =============================================================================
describe('4. Groups & RBAC Endpoints', () => {

  let testGroupId = '750e8400-e29b-41d4-a716-446655440001'
  let testPermissionId = '850e8400-e29b-41d4-a716-446655440001'

  it('4.1 POST /api/auth/organizations/:org_id/groups - Create group', async () => {
    const data = await testEndpoint('POST', '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups', {
      name: 'Test Group',
      description: 'Test description'
    }, 201)

    expect(data.id).toBeTruthy()
    expect(data.name).toBe('Test Group')
    if (data.id) testGroupId = data.id
  })

  it('4.2 GET /api/auth/organizations/:org_id/groups - List groups', async () => {
    const data = await testEndpoint('GET', '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups')

    expect(Array.isArray(data)).toBe(true)
  })

  it('4.3 GET /api/auth/groups/:group_id - Get group', async () => {
    const data = await testEndpoint('GET', `/api/auth/groups/${testGroupId}`)

    expect(data.id).toBe(testGroupId)
  })

  it('4.4 PATCH /api/auth/groups/:group_id - Update group', async () => {
    const data = await testEndpoint('PATCH', `/api/auth/groups/${testGroupId}`, {
      name: 'Updated Group Name'
    })

    expect(data.id).toBeTruthy()
  })

  it('4.5 POST /api/auth/groups/:group_id/members - Add member', async () => {
    const data = await testEndpoint('POST', `/api/auth/groups/${testGroupId}/members`, {
      user_id: '550e8400-e29b-41d4-a716-446655440011'
    }, 201)

    expect(data.user_id).toBeTruthy()
  })

  it('4.6 GET /api/auth/groups/:group_id/members - List members', async () => {
    const data = await testEndpoint('GET', `/api/auth/groups/${testGroupId}/members`)

    expect(Array.isArray(data)).toBe(true)
  })

  it('4.7 DELETE /api/auth/groups/:group_id/members/:user_id - Remove member', async () => {
    await testEndpoint('DELETE', `/api/auth/groups/${testGroupId}/members/550e8400-e29b-41d4-a716-446655440011`, undefined, 204)
  })

  it('4.8 POST /api/auth/permissions - Create permission', async () => {
    const data = await testEndpoint('POST', '/api/auth/permissions', {
      resource: 'test',
      action: 'create',
      description: 'Test permission'
    }, 201)

    expect(data.id).toBeTruthy()
    expect(data.permission_string).toBe('test:create')
    if (data.id) testPermissionId = data.id
  })

  it('4.9 GET /api/auth/permissions - List all permissions', async () => {
    const data = await testEndpoint('GET', '/api/auth/permissions')

    expect(Array.isArray(data)).toBe(true)
    expect(data.length).toBeGreaterThan(0)
  })

  it('4.10 POST /api/auth/groups/:group_id/permissions - Grant permission', async () => {
    const data = await testEndpoint('POST', `/api/auth/groups/${testGroupId}/permissions`, {
      permission_id: testPermissionId
    }, 201)

    expect(data.permission_id).toBeTruthy()
  })

  it('4.11 GET /api/auth/groups/:group_id/permissions - List permissions', async () => {
    const data = await testEndpoint('GET', `/api/auth/groups/${testGroupId}/permissions`)

    expect(Array.isArray(data)).toBe(true)
  })

  it('4.12 DELETE /api/auth/groups/:group_id/permissions/:permission_id - Revoke permission', async () => {
    await testEndpoint('DELETE', `/api/auth/groups/${testGroupId}/permissions/${testPermissionId}`, undefined, 204)
  })

  it('4.13 DELETE /api/auth/groups/:group_id - Delete group', async () => {
    await testEndpoint('DELETE', `/api/auth/groups/${testGroupId}`, undefined, 204)
  })
})

// =============================================================================
// 5. AUTHORIZATION ENDPOINTS (4 endpoints)
// =============================================================================
describe('5. Authorization Endpoints', () => {

  it('5.1 POST /api/auth/authorize - THE CORE authorization', async () => {
    const data = await testEndpoint('POST', '/api/auth/authorize', {
      user_id: '550e8400-e29b-41d4-a716-446655440000',
      organization_id: '650e8400-e29b-41d4-a716-446655440001',
      permission: 'activity:create'
    })

    expect(typeof data.authorized).toBe('boolean')
    expect(data.reason).toBeTruthy()
  })

  it('5.2 POST /api/v1/authorization/check - Image-API compatible', async () => {
    const data = await testEndpoint('POST', '/api/v1/authorization/check', {
      org_id: 'test-org-456',
      user_id: 'test-user-123',
      permission: 'image:upload'
    })

    expect(data.allowed).toBe(true)
    expect(Array.isArray(data.groups)).toBe(true)
  })

  it('5.3 GET /api/auth/users/:user_id/permissions - Get user permissions', async () => {
    const data = await testEndpoint('GET', '/api/auth/users/550e8400-e29b-41d4-a716-446655440000/permissions?organization_id=650e8400-e29b-41d4-a716-446655440001')

    expect(data.permissions || data.details).toBeTruthy()
  })

  it('5.4 GET /api/auth/users/:user_id/check-permission - Check permission (GET)', async () => {
    const data = await testEndpoint('GET', '/api/auth/users/550e8400-e29b-41d4-a716-446655440000/check-permission?organization_id=650e8400-e29b-41d4-a716-446655440001&permission=activity:create')

    expect(typeof data.authorized).toBe('boolean')
  })
})

// =============================================================================
// 6. ERROR SCENARIOS
// =============================================================================
describe('6. Error Handling', () => {

  it('Should return 401 for invalid credentials', async () => {
    const response = await fetch('http://localhost/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'WrongPassword'
      })
    })

    expect(response.status).toBe(401)
  })

  it('Should return 403 for unverified email', async () => {
    const response = await fetch('http://localhost/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'unverified@example.com',
        password: 'Password123!'
      })
    })

    expect(response.status).toBe(403)
  })

  it('Should return 422 for validation errors', async () => {
    const response = await fetch('http://localhost/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: '', // Missing email
        password: 'Password123!'
      })
    })

    expect(response.status).toBe(422)
  })
})
