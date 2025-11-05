-- =============================================================================
-- Auth API - Database Schema and Stored Procedures
-- =============================================================================
-- This file contains:
-- 1. The users table schema
-- 2. All required stored procedures for the Auth API
--
-- IMPORTANT: Run this AFTER creating the 'activity' schema
-- =============================================================================

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS activity;

-- =============================================================================
-- 1. USERS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS activity.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Status flags
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    verified_at TIMESTAMP,
    last_login_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT email_lowercase CHECK (email = LOWER(email))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON activity.users(email);
CREATE INDEX IF NOT EXISTS idx_users_verified ON activity.users(is_verified) 
    WHERE is_verified = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_active ON activity.users(is_active) 
    WHERE is_active = TRUE;

-- =============================================================================
-- 2. STORED PROCEDURES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- sp_create_user: Create a new user account
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_create_user(
    p_email VARCHAR,
    p_hashed_password VARCHAR
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    INSERT INTO activity.users (email, hashed_password, is_verified, is_active)
    VALUES (LOWER(p_email), p_hashed_password, FALSE, TRUE)
    RETURNING 
        activity.users.id, 
        activity.users.email, 
        activity.users.is_verified, 
        activity.users.is_active, 
        activity.users.created_at;
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Email already exists: %', p_email
            USING ERRCODE = '23505';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_create_user IS 
'Create a new user with email and hashed password. 
Email is automatically lowercased. 
Throws exception if email already exists.';

-- -----------------------------------------------------------------------------
-- sp_get_user_by_email: Retrieve user by email
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
    last_login_at TIMESTAMP,
    two_factor_enabled BOOLEAN,
    two_factor_secret TEXT,
    two_factor_backup_codes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.email,
        u.hashed_password,
        u.is_verified,
        u.is_active,
        u.created_at,
        u.verified_at,
        u.last_login_at,
        u.two_factor_enabled,
        u.two_factor_secret,
        u.two_factor_backup_codes
    FROM activity.users u
    WHERE u.email = LOWER(p_email);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_get_user_by_email IS 
'Retrieve user by email address. Returns NULL if not found.';

-- -----------------------------------------------------------------------------
-- sp_get_user_by_id: Retrieve user by UUID
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
        u.id, 
        u.email, 
        u.hashed_password, 
        u.is_verified, 
        u.is_active,
        u.created_at, 
        u.verified_at, 
        u.last_login_at
    FROM activity.users u
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_get_user_by_id IS 
'Retrieve user by UUID. Returns NULL if not found.';

-- -----------------------------------------------------------------------------
-- sp_verify_user_email: Mark user email as verified
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_verify_user_email(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET 
        is_verified = TRUE,
        verified_at = NOW()
    WHERE id = p_user_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_verify_user_email IS 
'Mark user email as verified and set verification timestamp. 
Returns TRUE if user found, FALSE otherwise.';

-- -----------------------------------------------------------------------------
-- sp_update_last_login: Update last login timestamp
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_update_last_login(
    p_user_id UUID
) RETURNS VOID AS $$
BEGIN
    UPDATE activity.users
    SET last_login_at = NOW()
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_update_last_login IS 
'Update the last_login_at timestamp for a user.';

-- -----------------------------------------------------------------------------
-- sp_update_password: Update user password
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_update_password(
    p_user_id UUID,
    p_new_hashed_password VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET hashed_password = p_new_hashed_password
    WHERE id = p_user_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_update_password IS 
'Update user password (must be pre-hashed). 
Returns TRUE if user found, FALSE otherwise.';

-- -----------------------------------------------------------------------------
-- sp_deactivate_user: Soft delete user account
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_deactivate_user(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET is_active = FALSE
    WHERE id = p_user_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_deactivate_user IS 
'Soft delete user by setting is_active to FALSE. 
Returns TRUE if user found, FALSE otherwise.';

-- -----------------------------------------------------------------------------
-- sp_cleanup_unverified_users: Remove old unverified users (optional)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_cleanup_unverified_users(
    p_days_old INTEGER DEFAULT 7
) RETURNS INTEGER AS $$
DECLARE
    rows_deleted INTEGER;
BEGIN
    DELETE FROM activity.users
    WHERE is_verified = FALSE
      AND created_at < NOW() - INTERVAL '1 day' * p_days_old;
    
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN rows_deleted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION activity.sp_cleanup_unverified_users IS 
'Delete users who have not verified their email after specified days. 
Default is 7 days. Returns number of deleted users.
This should be run as a scheduled job (cron/pg_cron).';

-- =============================================================================
-- 3. VERIFICATION QUERIES
-- =============================================================================

-- Verify table exists and has correct structure
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'activity' 
        AND table_name = 'users'
    ) THEN
        RAISE EXCEPTION 'Table activity.users does not exist!';
    END IF;
    
    RAISE NOTICE 'Database schema created successfully!';
END $$;

-- List all stored procedures
SELECT 
    routine_name as function_name,
    routine_type as type
FROM information_schema.routines
WHERE routine_schema = 'activity'
    AND routine_name LIKE 'sp_%'
ORDER BY routine_name;
