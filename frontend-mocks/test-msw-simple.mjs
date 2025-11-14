#!/usr/bin/env node

/**
 * 🎯 100% MSW ENDPOINT VALIDATION
 * Simple, direct test of all 41 endpoints
 * Uses MSW in Node.js to validate mock handlers
 */

import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

// Import handlers - using dynamic import to handle TypeScript
const handlersModule = await import('./src/mocks/handlers.ts')
const handlers = handlersModule.handlers

// Setup MSW server
const server = setupServer(...handlers)
await server.listen({ onUnhandledRequest: 'bypass' })

console.log('🎯 MSW Server started - testing all 41 endpoints\n')

// Colors for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  purple: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m\x1b[1m'
}

let totalTests = 0
let passedTests = 0
let failedTests = 0
const failedEndpoints = []

// Test endpoint helper
async function testEndpoint(name, method, path, body, expectedStatus, validation) {
  totalTests++

  console.log(`${colors.blue}[${totalTests}] Testing: ${colors.white}${name}${colors.reset}`)
  console.log(`   ${colors.cyan}${method} ${path}${colors.reset}`)

  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' }
    }

    if (body) {
      options.body = JSON.stringify(body)
    }

    const response = await fetch(`http://localhost${path}`, options)

    // Check status code
    if (response.status !== expectedStatus) {
      throw new Error(`Expected status ${expectedStatus}, got ${response.status}`)
    }

    // Get response data
    let data = null
    if (response.status !== 204) {
      data = await response.json()
    }

    // Custom validation
    if (validation && data) {
      const validationResult = validation(data)
      if (!validationResult) {
        throw new Error('Validation failed')
      }
    }

    console.log(`   ${colors.green}✅ PASSED${colors.reset}\n`)
    passedTests++

  } catch (error) {
    console.log(`   ${colors.red}❌ FAILED - ${error.message}${colors.reset}\n`)
    failedTests++
    failedEndpoints.push(name)
  }
}

// ═══════════════════════════════════════════════════════════════
// 1. AUTHENTICATION ENDPOINTS (11 tests)
// ═══════════════════════════════════════════════════════════════

console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}`)
console.log(`${colors.white}1️⃣  AUTHENTICATION ENDPOINTS (11 endpoints)${colors.reset}`)
console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}\n`)

await testEndpoint(
  'POST /api/auth/register',
  'POST',
  '/api/auth/register',
  { email: 'newuser@test.com', password: 'Password123!' },
  201,
  data => data.email === 'newuser@test.com' && data.user_id
)

await testEndpoint(
  'POST /api/auth/verify-code',
  'POST',
  '/api/auth/verify-code',
  { email: 'newuser@test.com', code: '123456' },
  200,
  data => data.access_token && data.refresh_token
)

await testEndpoint(
  'POST /api/auth/login - Step 1 (password)',
  'POST',
  '/api/auth/login',
  { email: 'test@example.com', password: 'Password123!' },
  200,
  data => data.requires_code === true
)

await testEndpoint(
  'POST /api/auth/login - Step 2 (code)',
  'POST',
  '/api/auth/login',
  { email: 'test@example.com', password: 'Password123!', code: '123456' },
  200,
  data => Array.isArray(data.organizations) && data.organizations.length > 0
)

await testEndpoint(
  'POST /api/auth/login - Step 3 (org)',
  'POST',
  '/api/auth/login',
  {
    email: 'test@example.com',
    password: 'Password123!',
    code: '123456',
    org_id: '650e8400-e29b-41d4-a716-446655440001'
  },
  200,
  data => data.access_token && data.refresh_token
)

await testEndpoint(
  'POST /api/auth/refresh',
  'POST',
  '/api/auth/refresh',
  { refresh_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' },
  200,
  data => data.access_token && data.refresh_token
)

await testEndpoint(
  'POST /api/auth/logout',
  'POST',
  '/api/auth/logout',
  { refresh_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' },
  200,
  data => data.message || data.success
)

await testEndpoint(
  'POST /api/auth/request-password-reset',
  'POST',
  '/api/auth/request-password-reset',
  { email: 'test@example.com' },
  200,
  data => data.reset_token
)

await testEndpoint(
  'POST /api/auth/reset-password',
  'POST',
  '/api/auth/reset-password',
  {
    reset_token: 'reset_abc123',
    code: '123456',
    new_password: 'NewPassword123!'
  },
  200,
  data => data.message || data.success
)

await testEndpoint(
  'POST /api/auth/2fa/setup',
  'POST',
  '/api/auth/2fa/setup',
  {},
  200,
  data => data.qr_code && data.secret
)

await testEndpoint(
  'POST /api/auth/2fa/verify',
  'POST',
  '/api/auth/2fa/verify',
  { code: '123456' },
  200,
  data => Array.isArray(data.backup_codes)
)

// ═══════════════════════════════════════════════════════════════
// 2. OAUTH 2.0 ENDPOINTS (5 tests)
// ═══════════════════════════════════════════════════════════════

console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}`)
console.log(`${colors.white}2️⃣  OAUTH 2.0 ENDPOINTS (5 endpoints)${colors.reset}`)
console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}\n`)

await testEndpoint(
  'GET /.well-known/oauth-authorization-server',
  'GET',
  '/.well-known/oauth-authorization-server',
  null,
  200,
  data => data.issuer && data.authorization_endpoint
)

await testEndpoint(
  'GET /oauth/authorize',
  'GET',
  '/oauth/authorize?response_type=code&client_id=test&redirect_uri=http://localhost:3000/callback&code_challenge=abc&code_challenge_method=S256',
  null,
  200,
  data => data.consent_required || data.authorization_code
)

await testEndpoint(
  'POST /oauth/authorize',
  'POST',
  '/oauth/authorize',
  {
    client_id: 'test-client',
    redirect_uri: 'http://localhost:3000/callback',
    scope: 'read write',
    consent: true
  },
  200,
  data => data.authorization_code
)

await testEndpoint(
  'POST /oauth/token',
  'POST',
  '/oauth/token',
  {
    grant_type: 'authorization_code',
    code: 'auth_abc123',
    redirect_uri: 'http://localhost:3000/callback',
    client_id: 'test-client',
    client_secret: 'test-secret',
    code_verifier: 'xyz'
  },
  200,
  data => data.access_token
)

await testEndpoint(
  'POST /oauth/revoke',
  'POST',
  '/oauth/revoke',
  {
    token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    client_id: 'test-client',
    client_secret: 'test-secret'
  },
  200,
  data => data.success || data.message
)

// ═══════════════════════════════════════════════════════════════
// 3. ORGANIZATION ENDPOINTS (7 tests)
// ═══════════════════════════════════════════════════════════════

console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}`)
console.log(`${colors.white}3️⃣  ORGANIZATION ENDPOINTS (7 endpoints)${colors.reset}`)
console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}\n`)

await testEndpoint(
  'POST /api/auth/organizations',
  'POST',
  '/api/auth/organizations',
  { name: 'New Org', description: 'Test org' },
  201,
  data => data.org_id
)

await testEndpoint(
  'GET /api/auth/organizations',
  'GET',
  '/api/auth/organizations',
  null,
  200,
  data => Array.isArray(data.organizations)
)

await testEndpoint(
  'GET /api/auth/organizations/{org_id}',
  'GET',
  '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001',
  null,
  200,
  data => data.name
)

await testEndpoint(
  'GET /api/auth/organizations/{org_id}/members',
  'GET',
  '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members',
  null,
  200,
  data => Array.isArray(data.members)
)

await testEndpoint(
  'POST /api/auth/organizations/{org_id}/members',
  'POST',
  '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members',
  { email: 'newmember@test.com', role: 'member' },
  201,
  data => data.success || data.message
)

await testEndpoint(
  'DELETE /api/auth/organizations/{org_id}/members/{user_id}',
  'DELETE',
  '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440000',
  null,
  200,
  data => data.success || data.message
)

await testEndpoint(
  'PATCH /api/auth/organizations/{org_id}/members/{user_id}/role',
  'PATCH',
  '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440000/role',
  { role: 'admin' },
  200,
  data => data.success || data.message
)

// ═══════════════════════════════════════════════════════════════
// 4. GROUPS & RBAC ENDPOINTS (13 tests)
// ═══════════════════════════════════════════════════════════════

console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}`)
console.log(`${colors.white}4️⃣  GROUPS & RBAC ENDPOINTS (13 endpoints)${colors.reset}`)
console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}\n`)

await testEndpoint(
  'POST /api/auth/organizations/{org_id}/groups',
  'POST',
  '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups',
  { name: 'Developers', description: 'Dev team' },
  201,
  data => data.group_id
)

await testEndpoint(
  'GET /api/auth/organizations/{org_id}/groups',
  'GET',
  '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups',
  null,
  200,
  data => Array.isArray(data.groups)
)

await testEndpoint(
  'GET /api/auth/groups/{group_id}',
  'GET',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001',
  null,
  200,
  data => data.name
)

await testEndpoint(
  'PATCH /api/auth/groups/{group_id}',
  'PATCH',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001',
  { name: 'Senior Devs' },
  200,
  data => data.success || data.message
)

await testEndpoint(
  'DELETE /api/auth/groups/{group_id}',
  'DELETE',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001',
  null,
  200,
  data => data.success || data.message
)

await testEndpoint(
  'POST /api/auth/groups/{group_id}/members',
  'POST',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/members',
  { user_id: '550e8400-e29b-41d4-a716-446655440000' },
  201,
  data => data.success || data.message
)

await testEndpoint(
  'DELETE /api/auth/groups/{group_id}/members/{user_id}',
  'DELETE',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440000',
  null,
  200,
  data => data.success || data.message
)

await testEndpoint(
  'GET /api/auth/groups/{group_id}/members',
  'GET',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/members',
  null,
  200,
  data => Array.isArray(data.members)
)

await testEndpoint(
  'POST /api/auth/groups/{group_id}/permissions',
  'POST',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/permissions',
  { permission_id: '850e8400-e29b-41d4-a716-446655440001' },
  201,
  data => data.success || data.message
)

await testEndpoint(
  'DELETE /api/auth/groups/{group_id}/permissions/{permission_id}',
  'DELETE',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/permissions/850e8400-e29b-41d4-a716-446655440001',
  null,
  200,
  data => data.success || data.message
)

await testEndpoint(
  'GET /api/auth/groups/{group_id}/permissions',
  'GET',
  '/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/permissions',
  null,
  200,
  data => Array.isArray(data.permissions)
)

await testEndpoint(
  'POST /api/auth/permissions',
  'POST',
  '/api/auth/permissions',
  {
    permission_string: 'activity:create',
    description: 'Create activities'
  },
  201,
  data => data.permission_id
)

await testEndpoint(
  'GET /api/auth/permissions',
  'GET',
  '/api/auth/permissions',
  null,
  200,
  data => Array.isArray(data.permissions)
)

// ═══════════════════════════════════════════════════════════════
// 5. AUTHORIZATION ENDPOINTS (4 tests)
// ═══════════════════════════════════════════════════════════════

console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}`)
console.log(`${colors.white}5️⃣  AUTHORIZATION ENDPOINTS (4 endpoints)${colors.reset}`)
console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}\n`)

await testEndpoint(
  'POST /api/auth/authorize',
  'POST',
  '/api/auth/authorize',
  {
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    organization_id: '650e8400-e29b-41d4-a716-446655440001',
    permission: 'activity:create'
  },
  200,
  data => typeof data.authorized === 'boolean'
)

await testEndpoint(
  'POST /api/v1/authorization/check',
  'POST',
  '/api/v1/authorization/check',
  {
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    organization_id: '650e8400-e29b-41d4-a716-446655440001',
    permission: 'activity:create'
  },
  200,
  data => typeof data.authorized === 'boolean'
)

await testEndpoint(
  'GET /api/auth/users/{user_id}/permissions',
  'GET',
  '/api/auth/users/550e8400-e29b-41d4-a716-446655440000/permissions?organization_id=650e8400-e29b-41d4-a716-446655440001',
  null,
  200,
  data => Array.isArray(data.permissions)
)

await testEndpoint(
  'GET /api/auth/users/{user_id}/check-permission',
  'GET',
  '/api/auth/users/550e8400-e29b-41d4-a716-446655440000/check-permission?organization_id=650e8400-e29b-41d4-a716-446655440001&permission=activity:create',
  null,
  200,
  data => typeof data.has_permission === 'boolean'
)

// ═══════════════════════════════════════════════════════════════
// FINAL SUMMARY
// ═══════════════════════════════════════════════════════════════

console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}`)
console.log(`${colors.white}📊 FINAL TEST RESULTS${colors.reset}`)
console.log(`${colors.purple}${'═'.repeat(60)}${colors.reset}\n`)

console.log(`${colors.cyan}Total Tests:${colors.reset}    ${colors.white}${totalTests}${colors.reset}`)
console.log(`${colors.green}Passed:${colors.reset}         ${colors.white}${passedTests}${colors.reset}`)
console.log(`${colors.red}Failed:${colors.reset}         ${colors.white}${failedTests}${colors.reset}`)

if (totalTests > 0) {
  const percentage = Math.round((passedTests / totalTests) * 100)
  console.log(`${colors.cyan}Coverage:${colors.reset}       ${colors.white}${percentage}%${colors.reset}\n`)
}

// Show failed endpoints
if (failedTests > 0) {
  console.log(`${colors.red}❌ FAILED ENDPOINTS:${colors.reset}`)
  failedEndpoints.forEach(endpoint => {
    console.log(`   ${colors.red}• ${endpoint}${colors.reset}`)
  })
  console.log('')
}

// Final verdict
if (failedTests === 0) {
  console.log(`${colors.green}${'═'.repeat(60)}${colors.reset}`)
  console.log(`${colors.green}✅ 100% SUCCESS - ALL ENDPOINTS WORKING! 🎯🏆${colors.reset}`)
  console.log(`${colors.green}${'═'.repeat(60)}${colors.reset}`)
  console.log(`${colors.white}Frontend developer can proceed with confidence! 💪${colors.reset}`)
  console.log(`${colors.green}${'═'.repeat(60)}${colors.reset}`)
} else {
  console.log(`${colors.red}${'═'.repeat(60)}${colors.reset}`)
  console.log(`${colors.red}❌ FAILURES DETECTED - NEEDS INVESTIGATION${colors.reset}`)
  console.log(`${colors.red}${'═'.repeat(60)}${colors.reset}`)
  console.log(`${colors.yellow}Do NOT call frontend developer until all tests pass!${colors.reset}`)
  console.log(`${colors.red}${'═'.repeat(60)}${colors.reset}`)
}

// Cleanup
server.close()
process.exit(failedTests === 0 ? 0 : 1)
