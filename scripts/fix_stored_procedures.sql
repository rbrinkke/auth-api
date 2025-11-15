-- =============================================================================
-- Auth API - Fixed Stored Procedures (Compatible with Restored Schema)
-- =============================================================================
-- This file fixes stored procedures to work with the restored database schema:
-- - Uses 'user_id' instead of 'id'
-- - Uses 'password_hash' instead of 'hashed_password'
-- - Adds 'username' requirement
-- - Works with existing 'status' column instead of 'is_active'
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Drop existing procedures if they exist
-- -----------------------------------------------------------------------------
DROP FUNCTION IF EXISTS activity.sp_create_user(VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS activity.sp_get_user_by_email(VARCHAR);
DROP FUNCTION IF EXISTS activity.sp_get_user_by_id(UUID);
DROP FUNCTION IF EXISTS activity.sp_verify_user_email(UUID);
DROP FUNCTION IF EXISTS activity.sp_update_last_login(UUID);
DROP FUNCTION IF EXISTS activity.sp_update_password(UUID, VARCHAR);
DROP FUNCTION IF EXISTS activity.sp_deactivate_user(UUID);

-- -----------------------------------------------------------------------------
-- Create refresh_tokens table (compatible with existing schema)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity.refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES activity.users(user_id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,
    jti VARCHAR(50) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    revoked BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON activity.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_jti ON activity.refresh_tokens(jti);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON activity.refresh_tokens(expires_at);

-- -----------------------------------------------------------------------------
-- sp_create_user: Create a new user account (FIXED)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_create_user(
    p_email VARCHAR,
    p_hashed_password VARCHAR
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    last_login_at TIMESTAMP
) AS $$
DECLARE
    v_username VARCHAR;
BEGIN
    -- Generate username from email (before @)
    v_username := split_part(p_email, '@', 1);

    -- Handle duplicate usernames by appending random suffix
    WHILE EXISTS (SELECT 1 FROM activity.users WHERE username = v_username) LOOP
        v_username := split_part(p_email, '@', 1) || floor(random() * 10000)::text;
    END LOOP;

    RETURN QUERY
    INSERT INTO activity.users (email, username, password_hash, is_verified, status)
    VALUES (
        LOWER(p_email),
        v_username,
        p_hashed_password,
        FALSE,
        'active'::activity.user_status
    )
    RETURNING
        activity.users.user_id AS id,
        activity.users.email,
        activity.users.password_hash AS hashed_password,
        activity.users.is_verified,
        (activity.users.status = 'active'::activity.user_status) AS is_active,
        activity.users.created_at,
        NULL::TIMESTAMP AS verified_at,
        activity.users.last_login_at;
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Email already exists: %', p_email
            USING ERRCODE = '23505';
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- sp_get_user_by_email: Retrieve user by email (FIXED)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_get_user_by_email(
    p_email VARCHAR
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    last_login_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id AS id,
        u.email,
        u.password_hash AS hashed_password,
        u.is_verified,
        (u.status = 'active'::activity.user_status) AS is_active,
        u.created_at::TIMESTAMP,
        NULL::TIMESTAMP AS verified_at,
        u.last_login_at::TIMESTAMP
    FROM activity.users u
    WHERE u.email = LOWER(p_email);
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- sp_get_user_by_id: Retrieve user by UUID (FIXED)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_get_user_by_id(
    p_user_id UUID
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    last_login_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id AS id,
        u.email,
        u.password_hash AS hashed_password,
        u.is_verified,
        (u.status = 'active'::activity.user_status) AS is_active,
        u.created_at::TIMESTAMP,
        NULL::TIMESTAMP AS verified_at,
        u.last_login_at::TIMESTAMP
    FROM activity.users u
    WHERE u.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- sp_verify_user_email: Mark user email as verified (FIXED)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_verify_user_email(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET is_verified = TRUE
    WHERE user_id = p_user_id;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- sp_update_last_login: Update last login timestamp (FIXED)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_update_last_login(
    p_user_id UUID
) RETURNS VOID AS $$
BEGIN
    UPDATE activity.users
    SET last_login_at = NOW()
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- sp_update_password: Update user password (FIXED)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_update_password(
    p_user_id UUID,
    p_new_hashed_password VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET password_hash = p_new_hashed_password
    WHERE user_id = p_user_id;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- sp_deactivate_user: Soft delete user account (FIXED)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_deactivate_user(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET status = 'deleted'::activity.user_status
    WHERE user_id = p_user_id;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- Verify stored procedures
-- -----------------------------------------------------------------------------
SELECT
    routine_name as function_name,
    routine_type as type
FROM information_schema.routines
WHERE routine_schema = 'activity'
    AND routine_name LIKE 'sp_%'
ORDER BY routine_name;
