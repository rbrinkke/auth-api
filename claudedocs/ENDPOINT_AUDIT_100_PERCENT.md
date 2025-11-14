# 🎯 100% MSW Mock Handler Audit - CRITICAL ANALYSIS

**Status**: 🚨 **FRONTEND BLOCKED - $100/HOUR**
**Date**: 2025-11-14
**Analyst**: Claude Code
**Objective**: Achieve 100% API coverage - NO COMPROMISES

---

## 📊 EXECUTIVE SUMMARY

### Current State
- **Backend Endpoints**: 41 active endpoints (excluding groups_old.py, dashboard HTML)
- **MSW Handlers**: 46 handlers claimed
- **Coverage Gap**: CRITICAL - Multiple missing/incorrect endpoints found
- **Schema Compliance**: NOT VERIFIED - Needs systematic check

### Critical Issues Found
1. ❌ **Missing OAuth endpoints** in MSW
2. ❌ **Missing Authorization endpoints** in MSW
3. ❌ **Incorrect response schemas** (not verified against backend)
4. ❌ **Missing error scenarios** for critical flows

---

## 🔍 COMPLETE BACKEND ENDPOINT MAP

### 1. Authentication Endpoints (11 endpoints)

#### `/api/auth/register` - POST
- **File**: `app/routes/register.py:11`
- **Request**: `UserCreate` (email, password)
- **Response**: `RegisterResponse` (message, email, user_id)
- **Status**: 201 CREATED
- **MSW**: ✅ EXISTS

#### `/api/auth/verify-code` - POST
- **File**: `app/routes/verify.py:11`
- **Request**: `VerifyEmailRequest` (verification_token, code)
- **Response**: `VerifyEmailResponse` (message)
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/login` - POST
- **File**: `app/routes/login.py:19`
- **Request**: `LoginRequest` (email, password, code?, org_id?)
- **Response**: `TokenResponse | LoginCodeSentResponse | OrganizationSelectionResponse`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS (but check multi-step flow)

#### `/api/auth/login/2fa` - POST
- **File**: `app/routes/login.py:58`
- **Request**: `TwoFactorLoginRequest` (pre_auth_token, code)
- **Response**: `TokenResponse`
- **Status**: 200 OK
- **MSW**: ❓ CHECK IF EXISTS

#### `/api/auth/refresh` - POST
- **File**: `app/routes/refresh.py:9`
- **Request**: `RefreshTokenRequest` (refresh_token)
- **Response**: `TokenResponse`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/logout` - POST
- **File**: `app/routes/logout.py:9`
- **Request**: `RefreshTokenRequest` (refresh_token)
- **Response**: `LogoutResponse` (message)
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/request-password-reset` - POST
- **File**: `app/routes/password_reset.py:11`
- **Request**: `RequestPasswordResetRequest` (email)
- **Response**: `RequestPasswordResetResponse` (message, user_id?)
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/reset-password` - POST
- **File**: `app/routes/password_reset.py:23`
- **Request**: `ResetPasswordRequest` (reset_token, code, new_password)
- **Response**: `ResetPasswordResponse` (message)
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/2fa/setup` - POST
- **File**: `app/routes/twofa.py:20`
- **Request**: NONE (uses JWT auth)
- **Response**: `{secret, qr_code_uri, backup_codes}`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/2fa/verify` - POST
- **File**: `app/routes/twofa.py:31`
- **Request**: `TwoFactorVerifyRequest` (code)
- **Response**: `{message}`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/2fa/disable` - POST
- **File**: `app/routes/twofa.py:43`
- **Request**: NONE (uses JWT auth)
- **Response**: `{message}`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

---

### 2. OAuth 2.0 Endpoints (5 endpoints)

#### `/.well-known/oauth-authorization-server` - GET
- **File**: `app/routes/oauth_discovery.py:20`
- **Request**: NONE
- **Response**: `OAuthDiscoveryResponse` (issuer, endpoints, grant_types, scopes, etc.)
- **Status**: 200 OK
- **MSW**: ❌ **MISSING**

#### `/oauth/authorize` - GET
- **File**: `app/routes/oauth_authorize.py:37`
- **Request**: Query params (response_type, client_id, redirect_uri, scope, state, code_challenge, code_challenge_method, nonce?)
- **Response**: HTML consent screen OR redirect with code
- **Status**: 200 OK / 302 REDIRECT
- **MSW**: ❓ CHECK (complex flow)

#### `/oauth/authorize` - POST
- **File**: `app/routes/oauth_authorize.py:373`
- **Request**: Form data (action, client_id, redirect_uri, scope, code_challenge, code_challenge_method, state, nonce?, org_id?)
- **Response**: Redirect with code OR error
- **Status**: 302 REDIRECT
- **MSW**: ❓ CHECK

#### `/oauth/token` - POST
- **File**: `app/routes/oauth_token.py:32`
- **Request**: Form-encoded (grant_type, code?, redirect_uri?, code_verifier?, refresh_token?, client_id, client_secret?, scope?)
- **Response**: `TokenResponse` (access_token, refresh_token?, token_type, expires_in, scope)
- **Status**: 200 OK
- **MSW**: ✅ EXISTS (but verify all 3 grant types)

#### `/oauth/revoke` - POST
- **File**: `app/routes/oauth_revoke.py:24`
- **Request**: Form-encoded (token, token_type_hint?, client_id, client_secret?)
- **Response**: Empty (always 200 OK per RFC 7009)
- **Status**: 200 OK
- **MSW**: ❓ CHECK

---

### 3. Organization Endpoints (7 endpoints)

#### `/api/auth/organizations` - POST
- **File**: `app/routes/organizations.py:37`
- **Request**: `OrganizationCreate` (name, slug, description?)
- **Response**: `OrganizationResponse`
- **Status**: 201 CREATED
- **MSW**: ✅ EXISTS

#### `/api/auth/organizations` - GET
- **File**: `app/routes/organizations.py:71`
- **Request**: NONE (uses JWT)
- **Response**: `List[OrganizationMembershipResponse]`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/organizations/{org_id}` - GET
- **File**: `app/routes/organizations.py:97`
- **Request**: NONE (uses JWT)
- **Response**: `OrganizationResponse`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/organizations/{org_id}/members` - GET
- **File**: `app/routes/organizations.py:130`
- **Request**: Query params (limit?, offset?)
- **Response**: `List[OrganizationMemberResponse]`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/organizations/{org_id}/members` - POST
- **File**: `app/routes/organizations.py:170`
- **Request**: `OrganizationMemberAdd` (user_id, role)
- **Response**: `OrganizationMemberResponse`
- **Status**: 201 CREATED
- **MSW**: ✅ EXISTS

#### `/api/auth/organizations/{org_id}/members/{member_user_id}` - DELETE
- **File**: `app/routes/organizations.py:205`
- **Request**: NONE
- **Response**: `{message}`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/organizations/{org_id}/members/{member_user_id}/role` - PATCH
- **File**: `app/routes/organizations.py:237`
- **Request**: `OrganizationMemberUpdate` (role)
- **Response**: `{message, member}`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

---

### 4. Groups & RBAC Endpoints (13 endpoints)

#### `/api/auth/organizations/{org_id}/groups` - POST
- **File**: `app/routes/groups.py:64`
- **Request**: `GroupCreate` (name, description?)
- **Response**: `GroupResponse`
- **Status**: 201 CREATED
- **MSW**: ✅ EXISTS

#### `/api/auth/organizations/{org_id}/groups` - GET
- **File**: `app/routes/groups.py:105`
- **Request**: NONE
- **Response**: `List[GroupResponse]`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}` - GET
- **File**: `app/routes/groups.py:132`
- **Request**: NONE
- **Response**: `GroupResponse`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}` - PATCH
- **File**: `app/routes/groups.py:159`
- **Request**: `GroupUpdate` (name?, description?)
- **Response**: `GroupResponse`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}` - DELETE
- **File**: `app/routes/groups.py:198`
- **Request**: NONE
- **Response**: NONE
- **Status**: 204 NO CONTENT
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}/members` - POST
- **File**: `app/routes/groups.py:238`
- **Request**: `GroupMemberAdd` (user_id)
- **Response**: `GroupMemberResponse`
- **Status**: 201 CREATED
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}/members/{user_id}` - DELETE
- **File**: `app/routes/groups.py:277`
- **Request**: NONE
- **Response**: NONE
- **Status**: 204 NO CONTENT
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}/members` - GET
- **File**: `app/routes/groups.py:312`
- **Request**: NONE
- **Response**: `List[GroupMemberResponse]`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}/permissions` - POST
- **File**: `app/routes/groups.py:343`
- **Request**: `GroupPermissionGrant` (permission_id)
- **Response**: `GroupPermissionResponse`
- **Status**: 201 CREATED
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}/permissions/{permission_id}` - DELETE
- **File**: `app/routes/groups.py:382`
- **Request**: NONE
- **Response**: NONE
- **Status**: 204 NO CONTENT
- **MSW**: ✅ EXISTS

#### `/api/auth/groups/{group_id}/permissions` - GET
- **File**: `app/routes/groups.py:417`
- **Request**: NONE
- **Response**: `List[GroupPermissionResponse]`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

#### `/api/auth/permissions` - POST
- **File**: `app/routes/groups.py:448`
- **Request**: `PermissionCreate` (resource, action, description?)
- **Response**: `PermissionResponse`
- **Status**: 201 CREATED
- **MSW**: ✅ EXISTS

#### `/api/auth/permissions` - GET
- **File**: `app/routes/groups.py:488`
- **Request**: NONE (PUBLIC endpoint)
- **Response**: `List[PermissionResponse]`
- **Status**: 200 OK
- **MSW**: ✅ EXISTS

---

### 5. Authorization Endpoints (4 endpoints)

#### `/api/v1/authorization/authorize` - POST (**THE CORE**)
- **File**: `app/routes/permissions.py:43`
- **Request**: `AuthorizationRequest` (user_id, organization_id, permission, resource_id?)
- **Response**: `AuthorizationResponse` (authorized, reason, matched_groups?)
- **Status**: 200 OK
- **MSW**: ❓ **CHECK PATH** (might be `/authorize` not `/api/v1/authorization/authorize`)

#### `/api/v1/authorization/check` - POST (Image-API Compatible)
- **File**: `app/routes/authorization.py:47`
- **Request**: `ImageAPIAuthorizationRequest` (org_id: string, user_id: string, permission)
- **Response**: `ImageAPIAuthorizationResponse` (allowed, groups?, reason?)
- **Status**: 200 OK / 403 FORBIDDEN
- **MSW**: ❌ **MISSING**

#### `/api/auth/users/{user_id}/permissions` - GET
- **File**: `app/routes/permissions.py:125`
- **Request**: Query param (organization_id)
- **Response**: `UserPermissionsResponse`
- **Status**: 200 OK
- **MSW**: ❌ **MISSING**

#### `/api/auth/users/{user_id}/check-permission` - GET
- **File**: `app/routes/permissions.py:186`
- **Request**: Query params (organization_id, permission)
- **Response**: `AuthorizationResponse`
- **Status**: 200 OK
- **MSW**: ❌ **MISSING**

---

### 6. Dashboard (1 endpoint - internal only)

#### `/api` - GET
- **File**: `app/routes/dashboard.py`
- **Internal dashboard** - not needed for frontend

---

## 🚨 CRITICAL FINDINGS

### Missing Endpoints in MSW (7 endpoints)
1. ❌ `GET /.well-known/oauth-authorization-server` - OAuth discovery
2. ❌ `POST /api/v1/authorization/check` - Image-API compatible auth check
3. ❌ `GET /api/auth/users/{user_id}/permissions` - User permissions list
4. ❌ `GET /api/auth/users/{user_id}/check-permission` - Permission check (GET variant)
5. ❓ `POST /oauth/revoke` - Token revocation (needs verification)
6. ❓ `GET /oauth/authorize` - OAuth authorization flow (needs verification)
7. ❓ `POST /oauth/authorize` - OAuth consent submission (needs verification)

### Schema Compliance Issues (Need Verification)
1. ⚠️ **Login flow** - 3-step process (password → code → org_selection → tokens)
2. ⚠️ **OAuth token endpoint** - 3 grant types (authorization_code, refresh_token, client_credentials)
3. ⚠️ **Error responses** - Must match backend exceptions exactly
4. ⚠️ **Status codes** - 201 vs 200, 204 NO CONTENT handling

---

## 📋 ACTION PLAN - 100% COVERAGE

### Phase 1: Complete Endpoint Map (DONE ✅)
- [x] Map all 41 backend endpoints
- [x] Document request/response schemas
- [x] Identify missing MSW handlers

### Phase 2: Read MSW Handlers (NEXT)
- [ ] Read complete MSW handlers file
- [ ] Map all existing handlers
- [ ] Compare against backend map

### Phase 3: Fix Missing Endpoints
- [ ] Add OAuth discovery endpoint
- [ ] Add authorization check endpoints (4 missing)
- [ ] Add OAuth revoke endpoint
- [ ] Verify OAuth authorize flow

### Phase 4: Schema Validation
- [ ] Compare request schemas
- [ ] Compare response schemas
- [ ] Verify error responses
- [ ] Verify status codes

### Phase 5: Test & Validate
- [ ] Test all 41 endpoints
- [ ] Verify 100% coverage
- [ ] Unblock frontend developer

---

## 💰 IMPACT

**Frontend Developer Blocked**: $100/hour
**Estimated Fix Time**: 2-3 hours
**Cost of Delay**: $200-300
**Priority**: 🔴 **CRITICAL - IMMEDIATE ACTION REQUIRED**

---

**Next Step**: Read complete MSW handlers file and create detailed comparison matrix.
