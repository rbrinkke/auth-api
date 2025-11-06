-- Migration: Add Two-Factor Authentication support
-- Date: 2025-11-05
-- Description: Adds 2FA fields to users table and creates 2FA codes table

-- Add 2FA columns to users table
ALTER TABLE activity.users
ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255),  -- Encrypted TOTP secret
ADD COLUMN IF NOT EXISTS two_factor_backup_codes JSONB,  -- Hashed backup codes
ADD COLUMN IF NOT EXISTS backup_codes_used INT DEFAULT 0;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_users_two_factor_enabled ON activity.users(two_factor_enabled);

-- Create 2FA verification codes table
CREATE TABLE IF NOT EXISTS activity.two_factor_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES activity.users(id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,  -- 6-digit temporary code
    purpose VARCHAR(20) NOT NULL CHECK (purpose IN ('login', 'reset', 'verify')),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_2fa_codes_user_id ON activity.two_factor_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_2fa_codes_purpose ON activity.two_factor_codes(purpose);
CREATE INDEX IF NOT EXISTS idx_2fa_codes_expires_at ON activity.two_factor_codes(expires_at);

-- Create function to cleanup expired codes
CREATE OR REPLACE FUNCTION cleanup_expired_2fa_codes()
RETURNS void AS $$
BEGIN
    DELETE FROM activity.two_factor_codes
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create trigger to cleanup expired codes automatically
CREATE OR REPLACE FUNCTION auto_cleanup_2fa_codes()
RETURNS trigger AS $$
BEGIN
    -- This will be called periodically to clean up expired codes
    PERFORM cleanup_expired_2fa_codes();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Note: We'll schedule this cleanup via a cron job or background task

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON activity.users TO activity_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON activity.two_factor_codes TO activity_user;

-- Comments for documentation
COMMENT ON TABLE activity.two_factor_codes IS 'Temporary 2FA codes for verification';
COMMENT ON COLUMN activity.two_factor_codes.code IS '6-digit verification code';
COMMENT ON COLUMN activity.two_factor_codes.purpose IS 'Purpose: login, reset, or verify';
COMMENT ON COLUMN activity.two_factor_codes.expires_at IS 'Code expiration time (5 minutes)';
COMMENT ON COLUMN activity.two_factor_codes.used_at IS 'When code was used (NULL if unused)';

-- Rollback script (in case we need to revert)
-- DROP TABLE IF EXISTS activity.two_factor_codes;
-- ALTER TABLE activity.users DROP COLUMN IF EXISTS two_factor_enabled;
-- ALTER TABLE activity.users DROP COLUMN IF EXISTS two_factor_secret;
-- ALTER TABLE activity.users DROP COLUMN IF EXISTS two_factor_backup_codes;
-- ALTER TABLE activity.users DROP COLUMN IF EXISTS backup_codes_used;
