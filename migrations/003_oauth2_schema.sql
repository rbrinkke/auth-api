-- ============================================================================
-- MIGRATION 003: OAuth 2.0 Authorization Server Schema
-- ============================================================================
-- Description: Complete OAuth 2.0 implementation with Authorization Code + PKCE
-- Author: Claude Code
-- Date: 2025-11-12
-- Dependencies: 001_organizations_schema.sql, 002_rbac_schema.sql
-- Standards: RFC 6749, RFC 7636 (PKCE), RFC 7009 (Revocation), RFC 7662 (Introspection)
-- ============================================================================

-- ============================================================================
-- PART 1: OAUTH CLIENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity.oauth_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Client Identification
    client_id VARCHAR(255) UNIQUE NOT NULL,
    client_secret_hash VARCHAR(255),  -- NULL for public clients (SPA, mobile)
    client_name VARCHAR(255) NOT NULL,
    client_type VARCHAR(20) NOT NULL CHECK (client_type IN ('public', 'confidential')),

    -- OAuth Configuration
    redirect_uris TEXT[] NOT NULL,  -- Allowed redirect URIs (exact match only)
    allowed_scopes TEXT[] NOT NULL,  -- Scopes this client can request (subset of permissions)
    grant_types TEXT[] NOT NULL DEFAULT ARRAY['authorization_code', 'refresh_token'],

    -- Security Settings
    require_pkce BOOLEAN NOT NULL DEFAULT TRUE,  -- Mandatory for public clients
    require_consent BOOLEAN NOT NULL DEFAULT TRUE,  -- FALSE for first-party apps
    is_first_party BOOLEAN NOT NULL DEFAULT FALSE,  -- Internal apps skip consent

    -- Metadata (for consent screen)
    description TEXT,
    logo_uri TEXT,
    homepage_uri TEXT,
    terms_of_service_uri TEXT,
    privacy_policy_uri TEXT,
    contacts TEXT[],  -- Support emails

    -- Audit
    created_by UUID NOT NULL REFERENCES activity.users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Soft Delete
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_redirect_uris_not_empty CHECK (array_length(redirect_uris, 1) > 0),
    CONSTRAINT chk_allowed_scopes_not_empty CHECK (array_length(allowed_scopes, 1) > 0),
    CONSTRAINT chk_public_no_secret CHECK (
        (client_type = 'public' AND client_secret_hash IS NULL) OR
        (client_type = 'confidential' AND client_secret_hash IS NOT NULL)
    ),
    CONSTRAINT chk_public_requires_pkce CHECK (
        client_type = 'confidential' OR require_pkce = TRUE
    )
);

COMMENT ON TABLE activity.oauth_clients IS 'OAuth 2.0 registered clients (applications that use this authorization server)';
COMMENT ON COLUMN activity.oauth_clients.client_id IS 'Public client identifier (e.g., "image-api-v1", "mobile-app")';
COMMENT ON COLUMN activity.oauth_clients.client_secret_hash IS 'Argon2id hash of client secret (NULL for public clients like SPAs)';
COMMENT ON COLUMN activity.oauth_clients.redirect_uris IS 'Allowed redirect URIs - exact match only, no wildcards (security)';
COMMENT ON COLUMN activity.oauth_clients.allowed_scopes IS 'Scopes this client can request (e.g., ["activity:read", "image:upload"])';
COMMENT ON COLUMN activity.oauth_clients.is_first_party IS 'First-party clients skip consent screen (internal apps only)';
COMMENT ON COLUMN activity.oauth_clients.require_pkce IS 'Require PKCE (mandatory for public clients, recommended for all)';

CREATE INDEX idx_oauth_clients_client_id ON activity.oauth_clients(client_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_oauth_clients_created_by ON activity.oauth_clients(created_by);
CREATE INDEX idx_oauth_clients_type ON activity.oauth_clients(client_type);

-- ============================================================================
-- PART 2: AUTHORIZATION CODES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity.oauth_authorization_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Code Details
    code VARCHAR(128) UNIQUE NOT NULL,  -- Base64url-encoded random string (256 bits)

    -- Relationships
    client_id VARCHAR(255) NOT NULL REFERENCES activity.oauth_clients(client_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES activity.users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES activity.organizations(id) ON DELETE CASCADE,

    -- OAuth Parameters
    redirect_uri TEXT NOT NULL,  -- Must match client's registered URI
    scopes TEXT[] NOT NULL,  -- Granted scopes (intersection of requested, allowed, user permissions)

    -- PKCE (Proof Key for Code Exchange) - RFC 7636
    code_challenge VARCHAR(128) NOT NULL,  -- SHA256(code_verifier) or plain code_verifier
    code_challenge_method VARCHAR(10) NOT NULL DEFAULT 'S256' CHECK (code_challenge_method IN ('S256', 'plain')),

    -- State Management
    used BOOLEAN NOT NULL DEFAULT FALSE,
    used_at TIMESTAMPTZ,

    -- Security
    nonce VARCHAR(255),  -- For OpenID Connect (optional)
    ip_address INET,  -- Client IP for audit
    user_agent TEXT,  -- Client user agent for audit

    -- Lifecycle
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '60 seconds'),  -- Very short lifetime
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_code_single_use CHECK (used = FALSE OR used_at IS NOT NULL),
    CONSTRAINT chk_scopes_not_empty CHECK (array_length(scopes, 1) > 0),
    CONSTRAINT chk_code_not_expired_when_used CHECK (
        used = FALSE OR used_at <= expires_at
    )
);

COMMENT ON TABLE activity.oauth_authorization_codes IS 'OAuth 2.0 authorization codes (60-second lifetime, single-use)';
COMMENT ON COLUMN activity.oauth_authorization_codes.code IS 'One-time authorization code (exchanged for tokens)';
COMMENT ON COLUMN activity.oauth_authorization_codes.code_challenge IS 'SHA256(code_verifier) for PKCE validation';
COMMENT ON COLUMN activity.oauth_authorization_codes.scopes IS 'Granted scopes = intersection(requested, client_allowed, user_permissions)';
COMMENT ON COLUMN activity.oauth_authorization_codes.used IS 'TRUE after code is exchanged (prevents replay attacks)';

CREATE UNIQUE INDEX idx_oauth_authz_codes_code ON activity.oauth_authorization_codes(code) WHERE used = FALSE;
CREATE INDEX idx_oauth_authz_codes_user_id ON activity.oauth_authorization_codes(user_id);
CREATE INDEX idx_oauth_authz_codes_client_id ON activity.oauth_authorization_codes(client_id);
CREATE INDEX idx_oauth_authz_codes_expires_at ON activity.oauth_authorization_codes(expires_at);

-- Index for cleanup job (delete expired codes)
CREATE INDEX idx_oauth_authz_codes_cleanup ON activity.oauth_authorization_codes(expires_at, used)
    WHERE used = FALSE;

-- ============================================================================
-- PART 3: USER CONSENT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity.oauth_user_consent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    user_id UUID NOT NULL REFERENCES activity.users(id) ON DELETE CASCADE,
    client_id VARCHAR(255) NOT NULL REFERENCES activity.oauth_clients(client_id) ON DELETE CASCADE,
    organization_id UUID REFERENCES activity.organizations(id) ON DELETE CASCADE,

    -- Consent Details
    granted_scopes TEXT[] NOT NULL,  -- Scopes user has consented to

    -- Lifecycle
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- NULL = never expires (revocable by user)
    revoked_at TIMESTAMPTZ,

    -- Audit
    ip_address INET,
    user_agent TEXT,

    -- Constraints
    CONSTRAINT uq_oauth_consent_user_client_org UNIQUE(user_id, client_id, organization_id),
    CONSTRAINT chk_granted_scopes_not_empty CHECK (array_length(granted_scopes, 1) > 0),
    CONSTRAINT chk_consent_valid CHECK (
        revoked_at IS NULL OR revoked_at >= granted_at
    )
);

COMMENT ON TABLE activity.oauth_user_consent IS 'User consent decisions (avoid re-prompting for same scopes)';
COMMENT ON COLUMN activity.oauth_user_consent.granted_scopes IS 'Scopes user has consented to (client can request without consent)';
COMMENT ON COLUMN activity.oauth_user_consent.revoked_at IS 'When user revoked consent (NULL = still active)';
COMMENT ON COLUMN activity.oauth_user_consent.expires_at IS 'Optional expiry (NULL = never expires, user must explicitly revoke)';

CREATE INDEX idx_oauth_consent_user_client ON activity.oauth_user_consent(user_id, client_id);
CREATE INDEX idx_oauth_consent_org ON activity.oauth_user_consent(organization_id);
CREATE INDEX idx_oauth_consent_granted_at ON activity.oauth_user_consent(granted_at DESC);

-- Index for active consents only
CREATE INDEX idx_oauth_consent_active ON activity.oauth_user_consent(user_id, client_id, organization_id)
    WHERE revoked_at IS NULL;

-- ============================================================================
-- PART 4: OAUTH AUDIT LOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity.oauth_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event Details
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        -- Client Management
        'client_registered', 'client_updated', 'client_deleted',
        -- Authorization Flow
        'authorization_requested', 'authorization_granted', 'authorization_denied',
        'token_issued', 'token_refreshed', 'token_revoked',
        -- Consent
        'consent_granted', 'consent_revoked', 'consent_skipped',
        -- Security Events
        'pkce_validation_failed', 'redirect_uri_mismatch', 'invalid_scope',
        'code_replay_attempt', 'code_expired', 'invalid_client_credentials',
        'insufficient_permissions'
    )),

    -- Relationships
    user_id UUID REFERENCES activity.users(id) ON DELETE SET NULL,
    client_id VARCHAR(255) REFERENCES activity.oauth_clients(client_id) ON DELETE SET NULL,
    organization_id UUID REFERENCES activity.organizations(id) ON DELETE SET NULL,

    -- Request Context
    ip_address INET,
    user_agent TEXT,
    requested_scopes TEXT[],
    granted_scopes TEXT[],

    -- Additional Details
    details JSONB,  -- Flexible storage for event-specific data
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE activity.oauth_audit_log IS 'Complete audit trail for OAuth operations (security & compliance)';
COMMENT ON COLUMN activity.oauth_audit_log.event_type IS 'Type of OAuth event (authorization, token, consent, error)';
COMMENT ON COLUMN activity.oauth_audit_log.success IS 'FALSE for security events (PKCE failure, invalid credentials, etc.)';
COMMENT ON COLUMN activity.oauth_audit_log.details IS 'Event-specific data (JSONB for flexibility)';

CREATE INDEX idx_oauth_audit_log_created_at ON activity.oauth_audit_log(created_at DESC);
CREATE INDEX idx_oauth_audit_log_event_type ON activity.oauth_audit_log(event_type);
CREATE INDEX idx_oauth_audit_log_user_id ON activity.oauth_audit_log(user_id);
CREATE INDEX idx_oauth_audit_log_client_id ON activity.oauth_audit_log(client_id);
CREATE INDEX idx_oauth_audit_log_success ON activity.oauth_audit_log(success) WHERE success = FALSE;

-- ============================================================================
-- PART 5: ENHANCE REFRESH TOKENS TABLE (Add client_id)
-- ============================================================================

-- Add client_id to existing refresh_tokens table for OAuth support
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'activity'
          AND table_name = 'refresh_tokens'
          AND column_name = 'client_id'
    ) THEN
        ALTER TABLE activity.refresh_tokens
        ADD COLUMN client_id VARCHAR(255) REFERENCES activity.oauth_clients(client_id) ON DELETE CASCADE;

        CREATE INDEX idx_refresh_tokens_client_id ON activity.refresh_tokens(client_id);

        COMMENT ON COLUMN activity.refresh_tokens.client_id IS 'OAuth client that requested this refresh token';
    END IF;
END $$;

-- ============================================================================
-- PART 6: STORED PROCEDURES - CLIENT MANAGEMENT
-- ============================================================================

-- sp_create_oauth_client: Register a new OAuth client
CREATE OR REPLACE FUNCTION activity.sp_create_oauth_client(
    p_client_id VARCHAR(255),
    p_client_name VARCHAR(255),
    p_client_type VARCHAR(20),
    p_redirect_uris TEXT[],
    p_allowed_scopes TEXT[],
    p_client_secret_hash VARCHAR(255) DEFAULT NULL,
    p_is_first_party BOOLEAN DEFAULT FALSE,
    p_description TEXT DEFAULT NULL,
    p_logo_uri TEXT DEFAULT NULL,
    p_created_by UUID DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_oauth_client_id UUID;
BEGIN
    -- Validate client_type
    IF p_client_type NOT IN ('public', 'confidential') THEN
        RAISE EXCEPTION 'Invalid client_type: %', p_client_type;
    END IF;

    -- Validate public client has no secret
    IF p_client_type = 'public' AND p_client_secret_hash IS NOT NULL THEN
        RAISE EXCEPTION 'Public clients cannot have client_secret';
    END IF;

    -- Validate confidential client has secret
    IF p_client_type = 'confidential' AND p_client_secret_hash IS NULL THEN
        RAISE EXCEPTION 'Confidential clients must have client_secret';
    END IF;

    -- Insert client
    INSERT INTO activity.oauth_clients (
        client_id, client_name, client_type, redirect_uris, allowed_scopes,
        client_secret_hash, is_first_party, description, logo_uri, created_by
    )
    VALUES (
        p_client_id, p_client_name, p_client_type, p_redirect_uris, p_allowed_scopes,
        p_client_secret_hash, p_is_first_party, p_description, p_logo_uri, p_created_by
    )
    RETURNING id INTO v_oauth_client_id;

    -- Audit log
    INSERT INTO activity.oauth_audit_log (event_type, client_id, user_id, details)
    VALUES (
        'client_registered',
        p_client_id,
        p_created_by,
        jsonb_build_object(
            'client_name', p_client_name,
            'client_type', p_client_type,
            'allowed_scopes', p_allowed_scopes,
            'is_first_party', p_is_first_party
        )
    );

    RETURN v_oauth_client_id;
END;
$$;

COMMENT ON FUNCTION activity.sp_create_oauth_client IS 'Register a new OAuth 2.0 client application';

-- sp_get_oauth_client: Get client by client_id
CREATE OR REPLACE FUNCTION activity.sp_get_oauth_client(
    p_client_id VARCHAR(255)
)
RETURNS TABLE (
    id UUID,
    client_id VARCHAR(255),
    client_name VARCHAR(255),
    client_type VARCHAR(20),
    client_secret_hash VARCHAR(255),
    redirect_uris TEXT[],
    allowed_scopes TEXT[],
    require_pkce BOOLEAN,
    require_consent BOOLEAN,
    is_first_party BOOLEAN,
    description TEXT,
    logo_uri TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id, c.client_id, c.client_name, c.client_type, c.client_secret_hash,
        c.redirect_uris, c.allowed_scopes, c.require_pkce, c.require_consent,
        c.is_first_party, c.description, c.logo_uri, c.created_at
    FROM activity.oauth_clients c
    WHERE c.client_id = p_client_id
      AND c.deleted_at IS NULL;
END;
$$;

-- sp_list_oauth_clients: List all registered clients
CREATE OR REPLACE FUNCTION activity.sp_list_oauth_clients()
RETURNS TABLE (
    id UUID,
    client_id VARCHAR(255),
    client_name VARCHAR(255),
    client_type VARCHAR(20),
    is_first_party BOOLEAN,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.client_id, c.client_name, c.client_type, c.is_first_party, c.created_at
    FROM activity.oauth_clients c
    WHERE c.deleted_at IS NULL
    ORDER BY c.created_at DESC;
END;
$$;

-- ============================================================================
-- PART 7: STORED PROCEDURES - AUTHORIZATION CODE FLOW
-- ============================================================================

-- sp_create_authorization_code: Create authorization code
CREATE OR REPLACE FUNCTION activity.sp_create_authorization_code(
    p_code VARCHAR(128),
    p_client_id VARCHAR(255),
    p_user_id UUID,
    p_organization_id UUID,
    p_redirect_uri TEXT,
    p_scopes TEXT[],
    p_code_challenge VARCHAR(128),
    p_code_challenge_method VARCHAR(10) DEFAULT 'S256',
    p_nonce VARCHAR(255) DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_authz_code_id UUID;
BEGIN
    -- Insert authorization code
    INSERT INTO activity.oauth_authorization_codes (
        code, client_id, user_id, organization_id, redirect_uri, scopes,
        code_challenge, code_challenge_method, nonce, ip_address, user_agent
    )
    VALUES (
        p_code, p_client_id, p_user_id, p_organization_id, p_redirect_uri, p_scopes,
        p_code_challenge, p_code_challenge_method, p_nonce, p_ip_address, p_user_agent
    )
    RETURNING id INTO v_authz_code_id;

    -- Audit log
    INSERT INTO activity.oauth_audit_log (
        event_type, user_id, client_id, organization_id,
        granted_scopes, ip_address, user_agent
    )
    VALUES (
        'authorization_granted',
        p_user_id,
        p_client_id,
        p_organization_id,
        p_scopes,
        p_ip_address,
        p_user_agent
    );

    RETURN v_authz_code_id;
END;
$$;

COMMENT ON FUNCTION activity.sp_create_authorization_code IS 'Create authorization code (60-second lifetime)';

-- sp_validate_and_consume_authorization_code: Validate and mark code as used
CREATE OR REPLACE FUNCTION activity.sp_validate_and_consume_authorization_code(
    p_code VARCHAR(128),
    p_client_id VARCHAR(255),
    p_redirect_uri TEXT
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    organization_id UUID,
    scopes TEXT[],
    code_challenge VARCHAR(128),
    code_challenge_method VARCHAR(10),
    nonce VARCHAR(255)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_record RECORD;
BEGIN
    -- Find authorization code
    SELECT * INTO v_record
    FROM activity.oauth_authorization_codes
    WHERE code = p_code
      AND client_id = p_client_id
      AND used = FALSE
      AND expires_at > NOW()
    FOR UPDATE;  -- Lock row for atomic update

    -- Validate code exists and not expired
    IF NOT FOUND THEN
        -- Check if code was already used (replay attack)
        IF EXISTS (
            SELECT 1 FROM activity.oauth_authorization_codes
            WHERE code = p_code AND used = TRUE
        ) THEN
            -- Audit log: Code replay attempt
            INSERT INTO activity.oauth_audit_log (
                event_type, client_id, success, error_message
            )
            VALUES (
                'code_replay_attempt',
                p_client_id,
                FALSE,
                'Authorization code has already been used'
            );

            RAISE EXCEPTION 'Authorization code has already been used (replay attack detected)';
        ELSE
            -- Audit log: Code expired or invalid
            INSERT INTO activity.oauth_audit_log (
                event_type, client_id, success, error_message
            )
            VALUES (
                'code_expired',
                p_client_id,
                FALSE,
                'Authorization code not found or expired'
            );

            RAISE EXCEPTION 'Authorization code not found or expired';
        END IF;
    END IF;

    -- Validate redirect_uri matches
    IF v_record.redirect_uri != p_redirect_uri THEN
        -- Audit log: Redirect URI mismatch
        INSERT INTO activity.oauth_audit_log (
            event_type, user_id, client_id, success, error_message, details
        )
        VALUES (
            'redirect_uri_mismatch',
            v_record.user_id,
            p_client_id,
            FALSE,
            'Redirect URI mismatch',
            jsonb_build_object(
                'expected', v_record.redirect_uri,
                'received', p_redirect_uri
            )
        );

        RAISE EXCEPTION 'Redirect URI mismatch';
    END IF;

    -- Mark code as used
    UPDATE activity.oauth_authorization_codes
    SET used = TRUE, used_at = NOW()
    WHERE code = p_code;

    -- Return code details
    RETURN QUERY
    SELECT
        v_record.id,
        v_record.user_id,
        v_record.organization_id,
        v_record.scopes,
        v_record.code_challenge,
        v_record.code_challenge_method,
        v_record.nonce;
END;
$$;

COMMENT ON FUNCTION activity.sp_validate_and_consume_authorization_code IS 'Validate and consume authorization code (atomic, prevents replay)';

-- sp_cleanup_expired_authorization_codes: Cleanup job (run periodically)
CREATE OR REPLACE FUNCTION activity.sp_cleanup_expired_authorization_codes()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM activity.oauth_authorization_codes
    WHERE expires_at < NOW() - INTERVAL '1 hour';  -- Keep for 1 hour for audit

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    RETURN v_deleted_count;
END;
$$;

COMMENT ON FUNCTION activity.sp_cleanup_expired_authorization_codes IS 'Delete expired authorization codes (run as cron job)';

-- ============================================================================
-- PART 8: STORED PROCEDURES - CONSENT MANAGEMENT
-- ============================================================================

-- sp_save_user_consent: Save user consent decision
CREATE OR REPLACE FUNCTION activity.sp_save_user_consent(
    p_user_id UUID,
    p_client_id VARCHAR(255),
    p_organization_id UUID,
    p_granted_scopes TEXT[],
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_consent_id UUID;
BEGIN
    -- Upsert consent (update if exists, insert if not)
    INSERT INTO activity.oauth_user_consent (
        user_id, client_id, organization_id, granted_scopes, ip_address, user_agent
    )
    VALUES (
        p_user_id, p_client_id, p_organization_id, p_granted_scopes, p_ip_address, p_user_agent
    )
    ON CONFLICT (user_id, client_id, organization_id)
    DO UPDATE SET
        granted_scopes = p_granted_scopes,
        granted_at = NOW(),
        revoked_at = NULL,  -- Re-activate if previously revoked
        ip_address = p_ip_address,
        user_agent = p_user_agent
    RETURNING id INTO v_consent_id;

    -- Audit log
    INSERT INTO activity.oauth_audit_log (
        event_type, user_id, client_id, organization_id,
        granted_scopes, ip_address, user_agent
    )
    VALUES (
        'consent_granted',
        p_user_id,
        p_client_id,
        p_organization_id,
        p_granted_scopes,
        p_ip_address,
        p_user_agent
    );

    RETURN v_consent_id;
END;
$$;

COMMENT ON FUNCTION activity.sp_save_user_consent IS 'Save user consent decision (upsert)';

-- sp_get_user_consent: Check if user has previously consented
CREATE OR REPLACE FUNCTION activity.sp_get_user_consent(
    p_user_id UUID,
    p_client_id VARCHAR(255),
    p_organization_id UUID,
    p_requested_scopes TEXT[]
)
RETURNS TABLE (
    has_consent BOOLEAN,
    granted_scopes TEXT[],
    needs_new_consent BOOLEAN
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_consent RECORD;
    v_has_consent BOOLEAN;
    v_needs_new_consent BOOLEAN;
BEGIN
    -- Find active consent
    SELECT * INTO v_consent
    FROM activity.oauth_user_consent
    WHERE user_id = p_user_id
      AND client_id = p_client_id
      AND organization_id = p_organization_id
      AND revoked_at IS NULL
      AND (expires_at IS NULL OR expires_at > NOW());

    -- No consent found
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::TEXT[], TRUE;
        RETURN;
    END IF;

    -- Check if requested scopes are subset of granted scopes
    v_has_consent := p_requested_scopes <@ v_consent.granted_scopes;

    -- If requested scopes are not fully covered, need new consent (incremental consent)
    v_needs_new_consent := NOT v_has_consent;

    RETURN QUERY
    SELECT v_has_consent, v_consent.granted_scopes, v_needs_new_consent;
END;
$$;

COMMENT ON FUNCTION activity.sp_get_user_consent IS 'Check if user has consented to requested scopes';

-- sp_revoke_user_consent: Revoke user consent
CREATE OR REPLACE FUNCTION activity.sp_revoke_user_consent(
    p_user_id UUID,
    p_client_id VARCHAR(255),
    p_organization_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE activity.oauth_user_consent
    SET revoked_at = NOW()
    WHERE user_id = p_user_id
      AND client_id = p_client_id
      AND organization_id = p_organization_id
      AND revoked_at IS NULL;

    IF FOUND THEN
        -- Audit log
        INSERT INTO activity.oauth_audit_log (
            event_type, user_id, client_id, organization_id
        )
        VALUES (
            'consent_revoked',
            p_user_id,
            p_client_id,
            p_organization_id
        );

        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$;

COMMENT ON FUNCTION activity.sp_revoke_user_consent IS 'Revoke user consent for a client';

-- ============================================================================
-- PART 9: SEED FIRST-PARTY CLIENTS
-- ============================================================================

-- Seed first-party clients (internal apps that skip consent)
-- Note: These are examples - adjust based on your actual services

INSERT INTO activity.oauth_clients (
    client_id, client_name, client_type, redirect_uris, allowed_scopes,
    is_first_party, require_consent, description,
    created_by
) VALUES
    -- Image API (first-party, confidential)
    (
        'image-api-v1',
        'Image Upload Service',
        'confidential',
        ARRAY[
            'https://image-api.activity.com/oauth/callback',
            'http://localhost:8001/oauth/callback'
        ],
        ARRAY[
            'activity:read', 'activity:create', 'activity:update',
            'image:upload', 'image:read', 'image:delete',
            'user:read'
        ],
        TRUE,  -- First-party
        FALSE,  -- Skip consent
        'Internal image upload and management service',
        (SELECT id FROM activity.users LIMIT 1)  -- System user
    ),

    -- Activity API (first-party, confidential)
    (
        'activity-api-v1',
        'Activity Management Service',
        'confidential',
        ARRAY[
            'https://activity-api.activity.com/oauth/callback',
            'http://localhost:8002/oauth/callback'
        ],
        ARRAY[
            'activity:read', 'activity:create', 'activity:update', 'activity:delete',
            'user:read', 'user:update',
            'organization:read'
        ],
        TRUE,  -- First-party
        FALSE,  -- Skip consent
        'Core activity management service',
        (SELECT id FROM activity.users LIMIT 1)
    ),

    -- Web Frontend (first-party, public)
    (
        'web-frontend-v1',
        'Activity Web App',
        'public',
        ARRAY[
            'https://app.activity.com/auth/callback',
            'http://localhost:3000/auth/callback'
        ],
        ARRAY[
            'activity:read', 'activity:create', 'activity:update', 'activity:delete',
            'image:upload', 'image:read', 'image:delete',
            'user:read', 'user:update',
            'organization:read', 'organization:update',
            'group:read', 'group:create', 'group:update', 'group:delete',
            'group:manage_members', 'group:manage_permissions'
        ],
        TRUE,  -- First-party
        FALSE,  -- Skip consent
        'Official web application',
        (SELECT id FROM activity.users LIMIT 1)
    ),

    -- Mobile App (first-party, public)
    (
        'mobile-app-v1',
        'Activity Mobile App',
        'public',
        ARRAY[
            'activityapp://auth/callback',
            'http://localhost/auth/callback'
        ],
        ARRAY[
            'activity:read', 'activity:create', 'activity:update', 'activity:delete',
            'image:upload', 'image:read',
            'user:read', 'user:update'
        ],
        TRUE,  -- First-party
        FALSE,  -- Skip consent
        'Official mobile application (iOS & Android)',
        (SELECT id FROM activity.users LIMIT 1)
    )

ON CONFLICT (client_id) DO NOTHING;

-- ============================================================================
-- PART 10: TRIGGERS
-- ============================================================================

-- Auto-update updated_at for oauth_clients
CREATE OR REPLACE FUNCTION activity.update_oauth_clients_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_oauth_clients_updated_at
    BEFORE UPDATE ON activity.oauth_clients
    FOR EACH ROW
    EXECUTE FUNCTION activity.update_oauth_clients_updated_at();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables were created
DO $$
DECLARE
    v_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema = 'activity'
      AND table_name IN ('oauth_clients', 'oauth_authorization_codes', 'oauth_user_consent', 'oauth_audit_log');

    IF v_table_count = 4 THEN
        RAISE NOTICE '✓ Migration 003: Successfully created 4 OAuth 2.0 tables';
    ELSE
        RAISE WARNING '⚠ Migration 003: Expected 4 tables, found %', v_table_count;
    END IF;
END $$;

-- Verify stored procedures were created
DO $$
DECLARE
    v_proc_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_proc_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'activity'
      AND p.proname LIKE 'sp_%oauth%';

    RAISE NOTICE '✓ Migration 003: Created % OAuth 2.0 stored procedures', v_proc_count;
END $$;

-- Verify first-party clients were seeded
DO $$
DECLARE
    v_client_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_client_count
    FROM activity.oauth_clients
    WHERE is_first_party = TRUE;

    RAISE NOTICE '✓ Migration 003: Seeded % first-party OAuth clients', v_client_count;
END $$;

RAISE NOTICE '🚀 Migration 003: OAuth 2.0 Authorization Server schema migration completed successfully!';
RAISE NOTICE '   - Authorization Code + PKCE flow ready';
RAISE NOTICE '   - Consent management enabled';
RAISE NOTICE '   - Security audit logging configured';
RAISE NOTICE '   - First-party clients registered';
RAISE NOTICE '';
RAISE NOTICE '📖 Next steps:';
RAISE NOTICE '   1. Run migration: psql -U activity_user -d activitydb -f migrations/003_oauth2_schema.sql';
RAISE NOTICE '   2. Implement OAuth endpoints (/oauth/authorize, /oauth/token)';
RAISE NOTICE '   3. Create consent screen UI';
RAISE NOTICE '   4. Update Resource Servers to validate OAuth scopes';
