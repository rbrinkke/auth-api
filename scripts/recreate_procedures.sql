-- Clean slate: Drop all auth procedures
DROP FUNCTION IF EXISTS activity.sp_create_user CASCADE;
DROP FUNCTION IF EXISTS activity.sp_get_user_by_email CASCADE;
DROP FUNCTION IF EXISTS activity.sp_get_user_by_id CASCADE;
DROP FUNCTION IF EXISTS activity.sp_verify_user_email CASCADE;
DROP FUNCTION IF EXISTS activity.sp_update_last_login CASCADE;
DROP FUNCTION IF EXISTS activity.sp_update_password CASCADE;
DROP FUNCTION IF EXISTS activity.sp_deactivate_user CASCADE;

-- sp_create_user
CREATE FUNCTION activity.sp_create_user(
    p_email VARCHAR,
    p_hashed_password VARCHAR
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ
) AS $$
DECLARE
    v_username VARCHAR;
BEGIN
    v_username := split_part(p_email, '@', 1);
    WHILE EXISTS (SELECT 1 FROM activity.users WHERE username = v_username) LOOP
        v_username := split_part(p_email, '@', 1) || floor(random() * 10000)::text;
    END LOOP;

    RETURN QUERY
    INSERT INTO activity.users (email, username, password_hash, is_verified, status)
    VALUES (LOWER(p_email), v_username, p_hashed_password, FALSE, 'active')
    RETURNING user_id, users.email, password_hash, is_verified,
              (status = 'active'), created_at, NULL::TIMESTAMPTZ, last_login_at;
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Email already exists: %', p_email USING ERRCODE = '23505';
END;
$$ LANGUAGE plpgsql;

-- sp_get_user_by_email
CREATE FUNCTION activity.sp_get_user_by_email(
    p_email VARCHAR
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT user_id, u.email, password_hash, is_verified,
           (status = 'active'), u.created_at, NULL::TIMESTAMPTZ, last_login_at
    FROM activity.users u
    WHERE u.email = LOWER(p_email);
END;
$$ LANGUAGE plpgsql;

-- sp_get_user_by_id
CREATE FUNCTION activity.sp_get_user_by_id(
    p_user_id UUID
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT user_id, u.email, password_hash, is_verified,
           (status = 'active'), u.created_at, NULL::TIMESTAMPTZ, last_login_at
    FROM activity.users u
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- sp_verify_user_email
CREATE FUNCTION activity.sp_verify_user_email(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users SET is_verified = TRUE WHERE user_id = p_user_id;
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

-- sp_update_last_login
CREATE FUNCTION activity.sp_update_last_login(
    p_user_id UUID
) RETURNS VOID AS $$
BEGIN
    UPDATE activity.users SET last_login_at = NOW() WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- sp_update_password
CREATE FUNCTION activity.sp_update_password(
    p_user_id UUID,
    p_new_hashed_password VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users SET password_hash = p_new_hashed_password WHERE user_id = p_user_id;
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

-- sp_deactivate_user
CREATE FUNCTION activity.sp_deactivate_user(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users SET status = 'deleted' WHERE user_id = p_user_id;
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

-- Verify
SELECT routine_name FROM information_schema.routines
WHERE routine_schema = 'activity' AND routine_name LIKE 'sp_%'
ORDER BY routine_name;
