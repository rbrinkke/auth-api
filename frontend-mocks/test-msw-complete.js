#!/usr/bin/env node
/**
 * 🎯 100% MSW Endpoint Test Suite
 *
 * Tests ALL 41 backend endpoints + OAuth flows
 * Run with: node test-msw-complete.js
 */

const BASE_URL = 'http://localhost:3000' // Adjust if needed

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
}

// Test results
let totalTests = 0
let passedTests = 0
let failedTests = 0
const failedDetails = []

// Helper function to make requests
async function testEndpoint(name, method, path, body, expectedStatus, validate) {
  totalTests++
  const url = `${BASE_URL}${path}`

  try {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    }

    if (body) {
      options.body = JSON.stringify(body)
    }

    const response = await fetch(url, options)
    const data = await response.text().then(text => {
      try {
        return JSON.parse(text)
      } catch {
        return text
      }
    })

    // Check status code
    if (response.status !== expectedStatus) {
      throw new Error(`Expected status ${expectedStatus}, got ${response.status}. Response: ${JSON.stringify(data)}`)
    }

    // Custom validation
    if (validate && !validate(data, response)) {
      throw new Error(`Validation failed. Response: ${JSON.stringify(data)}`)
    }

    passedTests++
    console.log(`${colors.green}✅ PASS${colors.reset} ${method} ${name}`)
    return { success: true, data }

  } catch (error) {
    failedTests++
    const errorMsg = `${method} ${name}: ${error.message}`
    failedDetails.push(errorMsg)
    console.log(`${colors.red}❌ FAIL${colors.reset} ${errorMsg}`)
    return { success: false, error: error.message }
  }
}

// Print section header
function section(title) {
  console.log(`\n${colors.bright}${colors.cyan}${'='.repeat(60)}${colors.reset}`)
  console.log(`${colors.bright}${colors.cyan}${title}${colors.reset}`)
  console.log(`${colors.cyan}${'='.repeat(60)}${colors.reset}\n`)
}

// Main test suite
async function runTests() {
  console.log(`\n${colors.bright}${colors.magenta}🎯 MSW 100% ENDPOINT TEST SUITE${colors.reset}\n`)
  console.log(`${colors.yellow}Testing against: ${BASE_URL}${colors.reset}\n`)

  // ==========================================================================
  // 1. AUTHENTICATION ENDPOINTS (11 tests)
  // ==========================================================================
  section('1. Authentication Endpoints (11)')

  // 1.1 Register
  await testEndpoint(
    'Register new user',
    'POST',
    '/api/auth/register',
    { email: 'newuser@test.com', password: 'Password123!' },
    201,
    data => data.email === 'newuser@test.com' && data.user_id
  )

  // 1.2 Verify code
  await testEndpoint(
    'Verify email code',
    'POST',
    '/api/auth/verify-code',
    { verification_token: 'VERIFY_TOKEN_ABC123456789', code: '123456' },
    200,
    data => data.message
  )

  // 1.3 Login - Step 1 (send code)
  const loginStep1 = await testEndpoint(
    'Login Step 1 - Send verification code',
    'POST',
    '/api/auth/login',
    { email: 'test@example.com', password: 'Password123!' },
    200,
    data => data.requires_code === true && data.user_id
  )

  // 1.4 Login - Step 2 (with code - multi-org user)
  const loginStep2 = await testEndpoint(
    'Login Step 2 - Verify code (multi-org)',
    'POST',
    '/api/auth/login',
    { email: 'test@example.com', password: 'Password123!', code: '123456' },
    200,
    data => Array.isArray(data.organizations) && data.organizations.length > 0
  )

  // 1.5 Login - Step 3 (with org_id)
  const loginStep3 = await testEndpoint(
    'Login Step 3 - Select organization',
    'POST',
    '/api/auth/login',
    {
      email: 'test@example.com',
      password: 'Password123!',
      code: '123456',
      org_id: '650e8400-e29b-41d4-a716-446655440001'
    },
    200,
    data => data.access_token && data.refresh_token && data.token_type === 'bearer'
  )

  // Store token for subsequent tests
  const accessToken = loginStep3.data?.access_token || 'mock-token'

  // 1.6 Login - Single org user (auto-select)
  await testEndpoint(
    'Login - Single org user (auto-select)',
    'POST',
    '/api/auth/login',
    {
      email: 'singleorg@example.com',
      password: 'Password123!',
      code: '123456'
    },
    200,
    data => data.access_token && data.refresh_token
  )

  // 1.7 Refresh token
  await testEndpoint(
    'Refresh access token',
    'POST',
    '/api/auth/refresh',
    { refresh_token: 'mock-refresh-token' },
    200,
    data => data.access_token && data.refresh_token
  )

  // 1.8 Logout
  await testEndpoint(
    'Logout',
    'POST',
    '/api/auth/logout',
    { refresh_token: 'mock-refresh-token' },
    200,
    data => data.message
  )

  // 1.9 Request password reset
  await testEndpoint(
    'Request password reset',
    'POST',
    '/api/auth/request-password-reset',
    { email: 'test@example.com' },
    200,
    data => data.message
  )

  // 1.10 Reset password
  await testEndpoint(
    'Reset password',
    'POST',
    '/api/auth/reset-password',
    {
      reset_token: 'RESET_TOKEN_XYZ',
      code: '123456',
      new_password: 'NewPassword123!'
    },
    200,
    data => data.message
  )

  // 1.11 2FA setup
  await testEndpoint(
    '2FA Setup',
    'POST',
    '/api/auth/2fa/setup',
    {},
    200,
    data => data.secret && data.qr_code_uri && Array.isArray(data.backup_codes)
  )

  // ==========================================================================
  // 2. OAUTH 2.0 ENDPOINTS (5 tests)
  // ==========================================================================
  section('2. OAuth 2.0 Endpoints (5)')

  // 2.1 OAuth Discovery
  await testEndpoint(
    'OAuth Discovery',
    'GET',
    '/.well-known/oauth-authorization-server',
    null,
    200,
    data => data.issuer && data.authorization_endpoint && data.token_endpoint
  )

  // 2.2 OAuth Token - Authorization Code Grant
  await testEndpoint(
    'OAuth Token - Authorization Code Grant',
    'POST',
    '/oauth/token',
    {
      grant_type: 'authorization_code',
      code: 'AUTH_CODE_VALID_ABC123',
      redirect_uri: 'https://app.example.com/callback',
      code_verifier: 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk',
      client_id: 'image-api-v1',
      client_secret: 'secret_image_api_12345'
    },
    200,
    data => data.access_token && data.token_type === 'Bearer'
  )

  // 2.3 OAuth Token - Refresh Token Grant
  await testEndpoint(
    'OAuth Token - Refresh Token Grant',
    'POST',
    '/oauth/token',
    {
      grant_type: 'refresh_token',
      refresh_token: accessToken, // Use token from login
      client_id: 'image-api-v1',
      client_secret: 'secret_image_api_12345'
    },
    200,
    data => data.access_token
  )

  // 2.4 OAuth Token - Client Credentials Grant
  await testEndpoint(
    'OAuth Token - Client Credentials Grant',
    'POST',
    '/oauth/token',
    {
      grant_type: 'client_credentials',
      scope: 'read:data write:data',
      client_id: 'service-account-bot',
      client_secret: 'secret_bot_service_67890'
    },
    200,
    data => data.access_token && data.token_type === 'Bearer' && !data.refresh_token
  )

  // 2.5 OAuth Revoke
  await testEndpoint(
    'OAuth Token Revocation',
    'POST',
    '/oauth/revoke',
    {
      token: accessToken,
      client_id: 'image-api-v1',
      client_secret: 'secret_image_api_12345'
    },
    200,
    () => true // Always returns 200 per RFC 7009
  )

  // ==========================================================================
  // 3. ORGANIZATION ENDPOINTS (7 tests)
  // ==========================================================================
  section('3. Organization Endpoints (7)')

  // 3.1 Create organization
  await testEndpoint(
    'Create organization',
    'POST',
    '/api/auth/organizations',
    { name: 'Test Org', slug: 'test-org', description: 'Test organization' },
    201,
    data => data.id && data.name === 'Test Org'
  )

  // 3.2 List organizations
  await testEndpoint(
    'List user organizations',
    'GET',
    '/api/auth/organizations',
    null,
    200,
    data => Array.isArray(data)
  )

  // 3.3 Get organization
  await testEndpoint(
    'Get organization by ID',
    'GET',
    '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001',
    null,
    200,
    data => data.id && data.name
  )

  // 3.4 List organization members
  await testEndpoint(
    'List organization members',
    'GET',
    '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members',
    null,
    200,
    data => Array.isArray(data)
  )

  // 3.5 Add organization member
  await testEndpoint(
    'Add organization member',
    'POST',
    '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members',
    { user_id: '550e8400-e29b-41d4-a716-446655440011', role: 'member' },
    201,
    data => data.user_id && data.role
  )

  // 3.6 Update member role
  await testEndpoint(
    'Update member role',
    'PATCH',
    '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440011/role',
    { role: 'admin' },
    200,
    data => data.message || data.member
  )

  // 3.7 Remove organization member
  await testEndpoint(
    'Remove organization member',
    'DELETE',
    '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440011',
    null,
    200,
    data => data.message
  )

  // ==========================================================================
  // 4. GROUPS & RBAC ENDPOINTS (13 tests)
  // ==========================================================================
  section('4. Groups & RBAC Endpoints (13)')

  // 4.1 Create group
  const newGroup = await testEndpoint(
    'Create group',
    'POST',
    '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups',
    { name: 'Test Group', description: 'Test group for testing' },
    201,
    data => data.id && data.name === 'Test Group'
  )

  const groupId = newGroup.data?.id || '750e8400-e29b-41d4-a716-446655440001'

  // 4.2 List groups
  await testEndpoint(
    'List organization groups',
    'GET',
    '/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups',
    null,
    200,
    data => Array.isArray(data)
  )

  // 4.3 Get group
  await testEndpoint(
    'Get group by ID',
    'GET',
    `/api/auth/groups/${groupId}`,
    null,
    200,
    data => data.id && data.name
  )

  // 4.4 Update group
  await testEndpoint(
    'Update group',
    'PATCH',
    `/api/auth/groups/${groupId}`,
    { name: 'Updated Group Name' },
    200,
    data => data.id
  )

  // 4.5 Add group member
  await testEndpoint(
    'Add group member',
    'POST',
    `/api/auth/groups/${groupId}/members`,
    { user_id: '550e8400-e29b-41d4-a716-446655440011' },
    201,
    data => data.user_id
  )

  // 4.6 List group members
  await testEndpoint(
    'List group members',
    'GET',
    `/api/auth/groups/${groupId}/members`,
    null,
    200,
    data => Array.isArray(data)
  )

  // 4.7 Remove group member
  await testEndpoint(
    'Remove group member',
    'DELETE',
    `/api/auth/groups/${groupId}/members/550e8400-e29b-41d4-a716-446655440011`,
    null,
    204,
    () => true
  )

  // 4.8 Create permission
  const newPermission = await testEndpoint(
    'Create permission',
    'POST',
    '/api/auth/permissions',
    { resource: 'test', action: 'create', description: 'Test permission' },
    201,
    data => data.id && data.permission_string === 'test:create'
  )

  const permissionId = newPermission.data?.id || '850e8400-e29b-41d4-a716-446655440001'

  // 4.9 List permissions
  await testEndpoint(
    'List all permissions',
    'GET',
    '/api/auth/permissions',
    null,
    200,
    data => Array.isArray(data) && data.length > 0
  )

  // 4.10 Grant permission to group
  await testEndpoint(
    'Grant permission to group',
    'POST',
    `/api/auth/groups/${groupId}/permissions`,
    { permission_id: permissionId },
    201,
    data => data.permission_id
  )

  // 4.11 List group permissions
  await testEndpoint(
    'List group permissions',
    'GET',
    `/api/auth/groups/${groupId}/permissions`,
    null,
    200,
    data => Array.isArray(data)
  )

  // 4.12 Revoke permission from group
  await testEndpoint(
    'Revoke permission from group',
    'DELETE',
    `/api/auth/groups/${groupId}/permissions/${permissionId}`,
    null,
    204,
    () => true
  )

  // 4.13 Delete group
  await testEndpoint(
    'Delete group',
    'DELETE',
    `/api/auth/groups/${groupId}`,
    null,
    204,
    () => true
  )

  // ==========================================================================
  // 5. AUTHORIZATION ENDPOINTS (4 tests)
  // ==========================================================================
  section('5. Authorization Endpoints (4)')

  // 5.1 Authorize - THE CORE
  await testEndpoint(
    'Authorize - THE CORE check',
    'POST',
    '/api/auth/authorize',
    {
      user_id: '550e8400-e29b-41d4-a716-446655440000',
      organization_id: '650e8400-e29b-41d4-a716-446655440001',
      permission: 'activity:create'
    },
    200,
    data => typeof data.authorized === 'boolean' && data.reason
  )

  // 5.2 Image-API compatible authorization check
  await testEndpoint(
    'Authorization check (Image-API compatible)',
    'POST',
    '/api/v1/authorization/check',
    {
      org_id: 'test-org-456',
      user_id: 'test-user-123',
      permission: 'image:upload'
    },
    200,
    data => data.allowed === true && Array.isArray(data.groups)
  )

  // 5.3 Get user permissions
  await testEndpoint(
    'Get user permissions',
    'GET',
    '/api/auth/users/550e8400-e29b-41d4-a716-446655440000/permissions?organization_id=650e8400-e29b-41d4-a716-446655440001',
    null,
    200,
    data => Array.isArray(data.permissions) || data.details
  )

  // 5.4 Check specific permission (GET)
  await testEndpoint(
    'Check permission (GET variant)',
    'GET',
    '/api/auth/users/550e8400-e29b-41d4-a716-446655440000/check-permission?organization_id=650e8400-e29b-41d4-a716-446655440001&permission=activity:create',
    null,
    200,
    data => typeof data.authorized === 'boolean'
  )

  // ==========================================================================
  // FINAL RESULTS
  // ==========================================================================
  console.log(`\n${colors.bright}${'='.repeat(60)}${colors.reset}`)
  console.log(`${colors.bright}${colors.magenta}📊 FINAL RESULTS${colors.reset}`)
  console.log(`${colors.bright}${'='.repeat(60)}${colors.reset}\n`)

  const coverage = totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(1) : 0

  console.log(`${colors.bright}Total Tests:${colors.reset}     ${totalTests}`)
  console.log(`${colors.green}${colors.bright}Passed:${colors.reset}          ${passedTests} ✅`)
  console.log(`${colors.red}${colors.bright}Failed:${colors.reset}          ${failedTests} ❌`)
  console.log(`${colors.cyan}${colors.bright}Coverage:${colors.reset}        ${coverage}% 🎯\n`)

  if (failedTests > 0) {
    console.log(`${colors.red}${colors.bright}❌ FAILED TESTS:${colors.reset}\n`)
    failedDetails.forEach((detail, i) => {
      console.log(`${i + 1}. ${detail}`)
    })
    console.log('')
  }

  if (passedTests === totalTests) {
    console.log(`${colors.green}${colors.bright}🏆 100% SUCCESS - ALL ENDPOINTS WORKING!${colors.reset}\n`)
    process.exit(0)
  } else {
    console.log(`${colors.red}${colors.bright}🚨 SOME TESTS FAILED - REVIEW ABOVE${colors.reset}\n`)
    process.exit(1)
  }
}

// Run tests
runTests().catch(error => {
  console.error(`${colors.red}❌ Fatal error:${colors.reset}`, error)
  process.exit(1)
})
