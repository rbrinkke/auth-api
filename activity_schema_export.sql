--
-- PostgreSQL database dump
--

\restrict nobbgSzeAg1RfFrkJ3bvM7wA2HcL8mycUEbd4ZBzmgf23F6dDK1jR2mT9fomim5

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: activity; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA activity;


ALTER SCHEMA activity OWNER TO postgres;

--
-- Name: activity_privacy_level; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.activity_privacy_level AS ENUM (
    'public',
    'friends_only',
    'invite_only'
);


ALTER TYPE activity.activity_privacy_level OWNER TO postgres;

--
-- Name: activity_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.activity_status AS ENUM (
    'draft',
    'published',
    'cancelled',
    'completed'
);


ALTER TYPE activity.activity_status OWNER TO postgres;

--
-- Name: activity_type; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.activity_type AS ENUM (
    'standard',
    'xxl',
    'womens_only',
    'mens_only'
);


ALTER TYPE activity.activity_type OWNER TO postgres;

--
-- Name: attendance_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.attendance_status AS ENUM (
    'registered',
    'attended',
    'no_show'
);


ALTER TYPE activity.attendance_status OWNER TO postgres;

--
-- Name: badge_category; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.badge_category AS ENUM (
    'participation',
    'achievement',
    'milestone',
    'special',
    'verification'
);


ALTER TYPE activity.badge_category OWNER TO postgres;

--
-- Name: community_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.community_status AS ENUM (
    'active',
    'archived',
    'suspended'
);


ALTER TYPE activity.community_status OWNER TO postgres;

--
-- Name: community_type; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.community_type AS ENUM (
    'open',
    'closed',
    'secret'
);


ALTER TYPE activity.community_type OWNER TO postgres;

--
-- Name: content_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.content_status AS ENUM (
    'draft',
    'published',
    'archived',
    'flagged',
    'removed'
);


ALTER TYPE activity.content_status OWNER TO postgres;

--
-- Name: content_type; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.content_type AS ENUM (
    'post',
    'photo',
    'video',
    'poll',
    'event_announcement'
);


ALTER TYPE activity.content_type OWNER TO postgres;

--
-- Name: invitation_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.invitation_status AS ENUM (
    'pending',
    'accepted',
    'declined',
    'expired'
);


ALTER TYPE activity.invitation_status OWNER TO postgres;

--
-- Name: membership_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.membership_status AS ENUM (
    'pending',
    'active',
    'banned',
    'left'
);


ALTER TYPE activity.membership_status OWNER TO postgres;

--
-- Name: notification_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.notification_status AS ENUM (
    'unread',
    'read',
    'archived'
);


ALTER TYPE activity.notification_status OWNER TO postgres;

--
-- Name: notification_type; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.notification_type AS ENUM (
    'activity_invite',
    'activity_reminder',
    'activity_update',
    'community_invite',
    'new_member',
    'new_post',
    'comment',
    'reaction',
    'mention',
    'profile_view',
    'new_favorite',
    'system'
);


ALTER TYPE activity.notification_type OWNER TO postgres;

--
-- Name: organization_role; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.organization_role AS ENUM (
    'owner',
    'admin',
    'moderator',
    'member'
);


ALTER TYPE activity.organization_role OWNER TO postgres;

--
-- Name: organization_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.organization_status AS ENUM (
    'active',
    'suspended',
    'archived'
);


ALTER TYPE activity.organization_status OWNER TO postgres;

--
-- Name: participant_role; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.participant_role AS ENUM (
    'organizer',
    'co_organizer',
    'member'
);


ALTER TYPE activity.participant_role OWNER TO postgres;

--
-- Name: participation_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.participation_status AS ENUM (
    'registered',
    'waitlisted',
    'declined',
    'cancelled'
);


ALTER TYPE activity.participation_status OWNER TO postgres;

--
-- Name: photo_moderation_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.photo_moderation_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


ALTER TYPE activity.photo_moderation_status OWNER TO postgres;

--
-- Name: reaction_type; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.reaction_type AS ENUM (
    'like',
    'love',
    'celebrate',
    'support',
    'insightful'
);


ALTER TYPE activity.reaction_type OWNER TO postgres;

--
-- Name: report_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.report_status AS ENUM (
    'pending',
    'reviewing',
    'resolved',
    'dismissed'
);


ALTER TYPE activity.report_status OWNER TO postgres;

--
-- Name: report_type; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.report_type AS ENUM (
    'spam',
    'harassment',
    'inappropriate',
    'fake',
    'no_show',
    'other'
);


ALTER TYPE activity.report_type OWNER TO postgres;

--
-- Name: subscription_level; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.subscription_level AS ENUM (
    'free',
    'club',
    'premium'
);


ALTER TYPE activity.subscription_level OWNER TO postgres;

--
-- Name: user_status; Type: TYPE; Schema: activity; Owner: postgres
--

CREATE TYPE activity.user_status AS ENUM (
    'active',
    'temporary_ban',
    'banned'
);


ALTER TYPE activity.user_status OWNER TO postgres;

--
-- Name: sp_accept_invitation(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_accept_invitation(p_invitation_id uuid, p_user_id uuid) RETURNS TABLE(success boolean, activity_id uuid, participation_status activity.participation_status, waitlist_position integer, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_invitation RECORD;
    v_activity RECORD;
    v_current_count INT;
    v_next_position INT;
BEGIN
    RAISE NOTICE 'sp_accept_invitation called: invitation_id=%, user_id=%', p_invitation_id, p_user_id;

    -- Get invitation details
    SELECT * INTO v_invitation
    FROM activity.activity_invitations
    WHERE invitation_id = p_invitation_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Invitation not found: %', p_invitation_id;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::activity.participation_status, NULL::INT,
            'INVITATION_NOT_FOUND'::VARCHAR(50), 'Invitation does not exist'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'Invitation found: activity_id=%, user_id=%, status=%',
        v_invitation.activity_id, v_invitation.user_id, v_invitation.status;

    -- Check invitation is for this user
    IF v_invitation.user_id != p_user_id THEN
        RAISE NOTICE 'Invitation is for different user: expected=%, actual=%',
            v_invitation.user_id, p_user_id;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::activity.participation_status, NULL::INT,
            'NOT_YOUR_INVITATION'::VARCHAR(50), 'This invitation is not for you'::TEXT;
        RETURN;
    END IF;

    -- Check invitation status
    IF v_invitation.status != 'pending' THEN
        RAISE NOTICE 'Invitation already responded: status=%', v_invitation.status;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::activity.participation_status, NULL::INT,
            'ALREADY_RESPONDED'::VARCHAR(50), 'Invitation already responded to'::TEXT;
        RETURN;
    END IF;

    -- Check invitation not expired
    IF v_invitation.expires_at IS NOT NULL AND v_invitation.expires_at <= NOW() THEN
        RAISE NOTICE 'Invitation expired: expires_at=%', v_invitation.expires_at;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::activity.participation_status, NULL::INT,
            'INVITATION_EXPIRED'::VARCHAR(50), 'Invitation has expired'::TEXT;
        RETURN;
    END IF;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = v_invitation.activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', v_invitation.activity_id;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::activity.participation_status, NULL::INT,
            'INVITATION_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check activity not in past
    IF v_activity.scheduled_at <= NOW() THEN
        RAISE NOTICE 'Activity is in the past: scheduled_at=%', v_activity.scheduled_at;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::activity.participation_status, NULL::INT,
            'ACTIVITY_IN_PAST'::VARCHAR(50), 'Activity has already occurred'::TEXT;
        RETURN;
    END IF;

    -- Accept invitation
    RAISE NOTICE 'Accepting invitation';
    UPDATE activity.activity_invitations
    SET status = 'accepted', responded_at = NOW()
    WHERE invitation_id = p_invitation_id;

    -- Join activity (check capacity)
    v_current_count := v_activity.current_participants_count;
    RAISE NOTICE 'Capacity check: current=%, max=%', v_current_count, v_activity.max_participants;

    IF v_current_count >= v_activity.max_participants THEN
        -- Add to waitlist
        RAISE NOTICE 'Activity full - adding to waitlist';

        SELECT COALESCE(MAX(position), 0) + 1 INTO v_next_position
        FROM activity.waitlist_entries
        WHERE activity_id = v_invitation.activity_id;

        INSERT INTO activity.waitlist_entries (activity_id, user_id, position)
        VALUES (v_invitation.activity_id, p_user_id, v_next_position);

        UPDATE activity.activities
        SET waitlist_count = waitlist_count + 1
        WHERE activity_id = v_invitation.activity_id;

        RAISE NOTICE 'Invitation accepted and added to waitlist: position=%', v_next_position;

        RETURN QUERY SELECT TRUE, v_invitation.activity_id,
            'waitlisted'::activity.participation_status, v_next_position,
            NULL::VARCHAR(50), NULL::TEXT;
        RETURN;
    ELSE
        -- Add as participant
        RAISE NOTICE 'Spots available - adding as participant';

        INSERT INTO activity.participants (activity_id, user_id, role, participation_status)
        VALUES (v_invitation.activity_id, p_user_id, 'member', 'registered');

        UPDATE activity.activities
        SET current_participants_count = current_participants_count + 1
        WHERE activity_id = v_invitation.activity_id;

        RAISE NOTICE 'Invitation accepted and joined activity';

        RETURN QUERY SELECT TRUE, v_invitation.activity_id,
            'registered'::activity.participation_status, NULL::INT,
            NULL::VARCHAR(50), NULL::TEXT;
        RETURN;
    END IF;
END;
$$;


ALTER FUNCTION activity.sp_accept_invitation(p_invitation_id uuid, p_user_id uuid) OWNER TO postgres;

--
-- Name: FUNCTION sp_accept_invitation(p_invitation_id uuid, p_user_id uuid); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_accept_invitation(p_invitation_id uuid, p_user_id uuid) IS 'Accept invitation and join activity or waitlist';


--
-- Name: sp_activity_cancel(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_cancel(p_activity_id uuid, p_user_id uuid, p_cancellation_reason text) RETURNS TABLE(activity_id uuid, status activity.activity_status, cancelled_at timestamp with time zone, participants_notified_count integer)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity RECORD;
    v_participants_count INT;
BEGIN
    -- 1. VALIDATION
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activities.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- Check if activity is published
    IF v_activity.status != 'published' THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_ACTIVITY_NOT_PUBLISHED' USING ERRCODE = '42501';
    END IF;

    -- Check if user is organizer
    IF NOT EXISTS (
        SELECT 1 FROM activity.participants
        WHERE activity_id = p_activity_id
          AND user_id = p_user_id
          AND role = 'organizer'
    ) THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NOT_ORGANIZER' USING ERRCODE = '42501';
    END IF;

    -- Check if activity is in the past
    IF v_activity.scheduled_at < NOW() THEN
        RAISE EXCEPTION 'ERR_CANNOT_CANCEL_PAST_ACTIVITY' USING ERRCODE = '22000';
    END IF;

    -- 2. CANCEL ACTIVITY
    UPDATE activity.activities
    SET
        status = 'cancelled',
        cancelled_at = NOW()
    WHERE activities.activity_id = p_activity_id;

    -- Update all participants
    UPDATE activity.participants
    SET participation_status = 'cancelled'
    WHERE participants.activity_id = p_activity_id;

    -- Count participants for notification
    SELECT COUNT(*) INTO v_participants_count
    FROM activity.participants
    WHERE participants.activity_id = p_activity_id
      AND user_id != p_user_id;  -- Exclude organizer

    -- 3. RETURN
    RETURN QUERY
    SELECT
        p_activity_id,
        'cancelled'::activity.activity_status,
        NOW(),
        v_participants_count;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_cancel(p_activity_id uuid, p_user_id uuid, p_cancellation_reason text) OWNER TO postgres;

--
-- Name: sp_activity_category_create(character varying, character varying, text, character varying, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_category_create(p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer) RETURNS TABLE(category_id uuid, name character varying, slug character varying, description text, icon_url character varying, display_order integer, is_active boolean, created_at timestamp with time zone)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $_$
DECLARE
    v_category_id UUID;
BEGIN
    -- 1. VALIDATION
    -- Validate slug format (must be lowercase with hyphens/numbers only)
    IF p_slug !~ '^[a-z0-9-]+$' THEN
        RAISE EXCEPTION 'ERR_VALIDATION_INVALID_SLUG_FORMAT'
            USING ERRCODE = '22000';
    END IF;

    -- Check name uniqueness
    IF EXISTS (
        SELECT 1 FROM activity.categories
        WHERE name = p_name
    ) THEN
        RAISE EXCEPTION 'ERR_CONFLICT_CATEGORY_NAME_EXISTS'
            USING ERRCODE = '23505';
    END IF;

    -- Check slug uniqueness
    IF EXISTS (
        SELECT 1 FROM activity.categories
        WHERE slug = p_slug
    ) THEN
        RAISE EXCEPTION 'ERR_CONFLICT_CATEGORY_SLUG_EXISTS'
            USING ERRCODE = '23505';
    END IF;

    -- 2. BUSINESS LOGIC
    -- Insert new category
    INSERT INTO activity.categories (
        name,
        slug,
        description,
        icon_url,
        display_order,
        is_active
    ) VALUES (
        p_name,
        p_slug,
        p_description,
        p_icon_url,
        COALESCE(p_display_order, 0),
        TRUE
    ) RETURNING categories.category_id INTO v_category_id;

    -- 3. RETURN
    RETURN QUERY
    SELECT
        c.category_id,
        c.name,
        c.slug,
        c.description,
        c.icon_url,
        c.display_order,
        c.is_active,
        c.created_at
    FROM activity.categories c
    WHERE c.category_id = v_category_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$_$;


ALTER FUNCTION activity.sp_activity_category_create(p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_activity_category_create(p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_activity_category_create(p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer) IS 'Create a new activity category (admin only)';


--
-- Name: sp_activity_category_list(); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_category_list() RETURNS TABLE(category_id uuid, name character varying, slug character varying, description text, icon_url character varying, display_order integer, is_active boolean, created_at timestamp with time zone)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    -- Query active categories, sorted by display_order and name
    RETURN QUERY
    SELECT
        c.category_id,
        c.name,
        c.slug,
        c.description,
        c.icon_url,
        c.display_order,
        c.is_active,
        c.created_at
    FROM activity.categories c
    WHERE c.is_active = TRUE
    ORDER BY c.display_order ASC, c.name ASC;

END;
$$;


ALTER FUNCTION activity.sp_activity_category_list() OWNER TO postgres;

--
-- Name: FUNCTION sp_activity_category_list(); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_activity_category_list() IS 'List all active categories sorted by display order';


--
-- Name: sp_activity_category_update(uuid, character varying, character varying, text, character varying, integer, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_category_update(p_category_id uuid, p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer, p_is_active boolean) RETURNS TABLE(category_id uuid, name character varying, slug character varying, description text, icon_url character varying, display_order integer, is_active boolean, created_at timestamp with time zone, updated_at timestamp with time zone)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $_$
DECLARE
    v_existing_category RECORD;
BEGIN
    -- 1. VALIDATION
    -- Check if category exists
    SELECT * INTO v_existing_category
    FROM activity.categories
    WHERE categories.category_id = p_category_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_CATEGORY'
            USING ERRCODE = '42704';
    END IF;

    -- Validate slug format if provided
    IF p_slug IS NOT NULL AND p_slug !~ '^[a-z0-9-]+$' THEN
        RAISE EXCEPTION 'ERR_VALIDATION_INVALID_SLUG_FORMAT'
            USING ERRCODE = '22000';
    END IF;

    -- Check name uniqueness if changed
    IF p_name IS NOT NULL AND p_name != v_existing_category.name THEN
        IF EXISTS (
            SELECT 1 FROM activity.categories
            WHERE name = p_name AND categories.category_id != p_category_id
        ) THEN
            RAISE EXCEPTION 'ERR_CONFLICT_CATEGORY_NAME_EXISTS'
                USING ERRCODE = '23505';
        END IF;
    END IF;

    -- Check slug uniqueness if changed
    IF p_slug IS NOT NULL AND p_slug != v_existing_category.slug THEN
        IF EXISTS (
            SELECT 1 FROM activity.categories
            WHERE slug = p_slug AND categories.category_id != p_category_id
        ) THEN
            RAISE EXCEPTION 'ERR_CONFLICT_CATEGORY_SLUG_EXISTS'
                USING ERRCODE = '23505';
        END IF;
    END IF;

    -- 2. BUSINESS LOGIC
    -- Update category (only update fields that are provided)
    UPDATE activity.categories
    SET
        name = COALESCE(p_name, name),
        slug = COALESCE(p_slug, slug),
        description = COALESCE(p_description, description),
        icon_url = COALESCE(p_icon_url, icon_url),
        display_order = COALESCE(p_display_order, display_order),
        is_active = COALESCE(p_is_active, is_active),
        updated_at = NOW()
    WHERE categories.category_id = p_category_id;

    -- 3. RETURN
    RETURN QUERY
    SELECT
        c.category_id,
        c.name,
        c.slug,
        c.description,
        c.icon_url,
        c.display_order,
        c.is_active,
        c.created_at,
        c.updated_at
    FROM activity.categories c
    WHERE c.category_id = p_category_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$_$;


ALTER FUNCTION activity.sp_activity_category_update(p_category_id uuid, p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer, p_is_active boolean) OWNER TO postgres;

--
-- Name: FUNCTION sp_activity_category_update(p_category_id uuid, p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer, p_is_active boolean); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_activity_category_update(p_category_id uuid, p_name character varying, p_slug character varying, p_description text, p_icon_url character varying, p_display_order integer, p_is_active boolean) IS 'Update an existing category (admin only)';


--
-- Name: sp_activity_create(uuid, uuid, character varying, text, activity.activity_type, activity.activity_privacy_level, timestamp with time zone, integer, timestamp with time zone, integer, character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying, numeric, numeric, character varying, jsonb); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_create(p_organizer_user_id uuid, p_category_id uuid, p_title character varying, p_description text, p_activity_type activity.activity_type, p_activity_privacy_level activity.activity_privacy_level, p_scheduled_at timestamp with time zone, p_duration_minutes integer, p_joinable_at_free timestamp with time zone, p_max_participants integer, p_language character varying, p_external_chat_id character varying, p_venue_name character varying, p_address_line1 character varying, p_address_line2 character varying, p_city character varying, p_state_province character varying, p_postal_code character varying, p_country character varying, p_latitude numeric, p_longitude numeric, p_place_id character varying, p_tags jsonb) RETURNS TABLE(activity_id uuid, organizer_user_id uuid, category_id uuid, title character varying, description text, activity_type activity.activity_type, activity_privacy_level activity.activity_privacy_level, status activity.activity_status, scheduled_at timestamp with time zone, duration_minutes integer, joinable_at_free timestamp with time zone, max_participants integer, current_participants_count integer, waitlist_count integer, location_name character varying, city character varying, language character varying, external_chat_id character varying, created_at timestamp with time zone, location jsonb, tags text[])
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity_id UUID;
    v_location_id UUID;
    v_tags_array TEXT[];
BEGIN
    -- 1. VALIDATION
    -- Check user exists and is active
    IF NOT EXISTS (
        SELECT 1 FROM activity.users
        WHERE users.user_id = p_organizer_user_id AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'ERR_USER_NOT_FOUND' USING ERRCODE = '42704';
    END IF;

    -- Check category if provided
    IF p_category_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM activity.categories
        WHERE categories.category_id = p_category_id AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'ERR_CATEGORY_NOT_FOUND' USING ERRCODE = '42704';
    END IF;

    -- Validate scheduled_at is in the future
    IF p_scheduled_at <= NOW() THEN
        RAISE EXCEPTION 'ERR_SCHEDULED_AT_PAST' USING ERRCODE = '22000';
    END IF;

    -- Validate joinable_at_free is not in the past
    IF p_joinable_at_free IS NOT NULL AND p_joinable_at_free < NOW() THEN
        RAISE EXCEPTION 'ERR_JOINABLE_AT_FREE_PAST' USING ERRCODE = '22000';
    END IF;

    -- Validate max_participants range
    IF p_max_participants < 2 OR p_max_participants > 1000 THEN
        RAISE EXCEPTION 'ERR_INVALID_MAX_PARTICIPANTS' USING ERRCODE = '22000';
    END IF;

    -- Validate tags count
    IF p_tags IS NOT NULL AND jsonb_array_length(p_tags) > 20 THEN
        RAISE EXCEPTION 'ERR_MAX_TAGS_EXCEEDED' USING ERRCODE = '22000';
    END IF;

    -- 2. BUSINESS LOGIC
    -- Insert activity
    INSERT INTO activity.activities (
        organizer_user_id,
        category_id,
        title,
        description,
        activity_type,
        activity_privacy_level,
        scheduled_at,
        duration_minutes,
        joinable_at_free,
        max_participants,
        language,
        external_chat_id,
        status,
        current_participants_count,
        location_name,
        city
    ) VALUES (
        p_organizer_user_id,
        p_category_id,
        p_title,
        p_description,
        p_activity_type,
        p_activity_privacy_level,
        p_scheduled_at,
        p_duration_minutes,
        p_joinable_at_free,
        p_max_participants,
        COALESCE(p_language, 'en'),
        p_external_chat_id,
        'published',
        1,  -- Organizer is first participant
        p_venue_name,
        p_city
    ) RETURNING activities.activity_id INTO v_activity_id;

    -- Insert location if provided
    IF p_venue_name IS NOT NULL OR p_latitude IS NOT NULL THEN
        INSERT INTO activity.activity_locations (
            activity_id,
            venue_name,
            address_line1,
            address_line2,
            city,
            state_province,
            postal_code,
            country,
            latitude,
            longitude,
            place_id
        ) VALUES (
            v_activity_id,
            p_venue_name,
            p_address_line1,
            p_address_line2,
            p_city,
            p_state_province,
            p_postal_code,
            p_country,
            p_latitude,
            p_longitude,
            p_place_id
        ) RETURNING location_id INTO v_location_id;
    END IF;

    -- Insert tags
    IF p_tags IS NOT NULL AND jsonb_array_length(p_tags) > 0 THEN
        INSERT INTO activity.activity_tags (activity_id, tag)
        SELECT v_activity_id, jsonb_array_elements_text(p_tags);
    END IF;

    -- Insert organizer as participant
    INSERT INTO activity.participants (
        activity_id,
        user_id,
        role,
        participation_status
    ) VALUES (
        v_activity_id,
        p_organizer_user_id,
        'organizer',
        'registered'
    );

    -- Increment activities_created_count
    UPDATE activity.users
    SET activities_created_count = activities_created_count + 1
    WHERE users.user_id = p_organizer_user_id;

    -- 3. RETURN
    -- Build tags array
    SELECT ARRAY_AGG(tag) INTO v_tags_array
    FROM activity.activity_tags
    WHERE activity_tags.activity_id = v_activity_id;

    RETURN QUERY
    SELECT
        a.activity_id,
        a.organizer_user_id,
        a.category_id,
        a.title,
        a.description,
        a.activity_type,
        a.activity_privacy_level,
        a.status,
        a.scheduled_at,
        a.duration_minutes,
        a.joinable_at_free,
        a.max_participants,
        a.current_participants_count,
        a.waitlist_count,
        a.location_name,
        a.city,
        a.language,
        a.external_chat_id,
        a.created_at,
        -- Location as JSONB
        (
            SELECT row_to_json(l.*)::JSONB
            FROM activity.activity_locations l
            WHERE l.activity_id = a.activity_id
        ) as location,
        -- Tags as array
        COALESCE(v_tags_array, ARRAY[]::TEXT[]) as tags
    FROM activity.activities a
    WHERE a.activity_id = v_activity_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_create(p_organizer_user_id uuid, p_category_id uuid, p_title character varying, p_description text, p_activity_type activity.activity_type, p_activity_privacy_level activity.activity_privacy_level, p_scheduled_at timestamp with time zone, p_duration_minutes integer, p_joinable_at_free timestamp with time zone, p_max_participants integer, p_language character varying, p_external_chat_id character varying, p_venue_name character varying, p_address_line1 character varying, p_address_line2 character varying, p_city character varying, p_state_province character varying, p_postal_code character varying, p_country character varying, p_latitude numeric, p_longitude numeric, p_place_id character varying, p_tags jsonb) OWNER TO postgres;

--
-- Name: sp_activity_delete(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_delete(p_activity_id uuid, p_user_id uuid) RETURNS TABLE(deleted boolean, message text)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity RECORD;
BEGIN
    -- 1. VALIDATION
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activities.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- Check if user is organizer
    IF v_activity.organizer_user_id != p_user_id THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NOT_ORGANIZER' USING ERRCODE = '42501';
    END IF;

    -- Check if only organizer is participant
    IF v_activity.current_participants_count > 1 THEN
        RAISE EXCEPTION 'ERR_CANNOT_DELETE_WITH_PARTICIPANTS' USING ERRCODE = '42501';
    END IF;

    -- 2. DELETE ACTIVITY (CASCADE will handle related records)
    DELETE FROM activity.activities WHERE activities.activity_id = p_activity_id;

    -- Decrement activities_created_count
    UPDATE activity.users
    SET activities_created_count = activities_created_count - 1
    WHERE users.user_id = p_user_id;

    -- 3. RETURN
    RETURN QUERY
    SELECT TRUE, 'Activity deleted successfully'::TEXT;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_delete(p_activity_id uuid, p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_activity_get_by_id(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_get_by_id(p_activity_id uuid, p_requesting_user_id uuid) RETURNS TABLE(activity_id uuid, organizer_user_id uuid, organizer_username character varying, organizer_first_name character varying, organizer_main_photo_url character varying, organizer_is_verified boolean, category_id uuid, category_name character varying, title character varying, description text, activity_type activity.activity_type, activity_privacy_level activity.activity_privacy_level, status activity.activity_status, scheduled_at timestamp with time zone, duration_minutes integer, joinable_at_free timestamp with time zone, max_participants integer, current_participants_count integer, waitlist_count integer, location jsonb, tags text[], language character varying, external_chat_id character varying, created_at timestamp with time zone, updated_at timestamp with time zone, completed_at timestamp with time zone, cancelled_at timestamp with time zone, user_participation_status character varying, user_can_join boolean, user_can_edit boolean, is_blocked boolean)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity RECORD;
    v_is_blocked BOOLEAN := FALSE;
    v_user_participation_status VARCHAR(50) := 'not_participating';
    v_user_can_join BOOLEAN := FALSE;
    v_user_can_edit BOOLEAN := FALSE;
    v_tags_array TEXT[];
BEGIN
    -- 1. VALIDATION
    -- Check if activity exists
    SELECT a.* INTO v_activity
    FROM activity.activities a
    WHERE a.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- 2. BLOCKING CHECK (both directions, except XXL)
    IF v_activity.activity_type != 'xxl' THEN
        IF EXISTS (
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = v_activity.organizer_user_id AND blocked_user_id = p_requesting_user_id)
               OR (blocker_user_id = p_requesting_user_id AND blocked_user_id = v_activity.organizer_user_id)
        ) THEN
            v_is_blocked := TRUE;
        END IF;
    END IF;

    -- 3. PRIVACY LEVEL CHECK
    IF v_activity.activity_privacy_level = 'friends_only' AND NOT v_is_blocked THEN
        -- Check if requesting user is friend of organizer
        IF NOT EXISTS (
            SELECT 1 FROM activity.friendships
            WHERE ((user_id_1 = v_activity.organizer_user_id AND user_id_2 = p_requesting_user_id)
                OR (user_id_1 = p_requesting_user_id AND user_id_2 = v_activity.organizer_user_id))
              AND status = 'accepted'
        ) THEN
            -- Not a friend - check if user is already a participant
            IF NOT EXISTS (
                SELECT 1 FROM activity.participants
                WHERE activity_id = p_activity_id AND user_id = p_requesting_user_id
            ) THEN
                RAISE EXCEPTION 'ERR_FORBIDDEN_FRIENDS_ONLY' USING ERRCODE = '42501';
            END IF;
        END IF;
    END IF;

    IF v_activity.activity_privacy_level = 'invite_only' AND NOT v_is_blocked THEN
        -- Check if user has invitation
        IF NOT EXISTS (
            SELECT 1 FROM activity.activity_invitations
            WHERE activity_id = p_activity_id
              AND user_id = p_requesting_user_id
              AND status = 'accepted'
        ) THEN
            -- No invitation - check if user is already a participant
            IF NOT EXISTS (
                SELECT 1 FROM activity.participants
                WHERE activity_id = p_activity_id AND user_id = p_requesting_user_id
            ) THEN
                RAISE EXCEPTION 'ERR_FORBIDDEN_INVITE_ONLY' USING ERRCODE = '42501';
            END IF;
        END IF;
    END IF;

    -- 4. CHECK USER PARTICIPATION
    SELECT p.participation_status INTO v_user_participation_status
    FROM activity.participants p
    WHERE p.activity_id = p_activity_id AND p.user_id = p_requesting_user_id;

    IF NOT FOUND THEN
        v_user_participation_status := 'not_participating';
    END IF;

    -- 5. CHECK IF USER CAN EDIT
    IF EXISTS (
        SELECT 1 FROM activity.participants
        WHERE activity_id = p_activity_id
          AND user_id = p_requesting_user_id
          AND role IN ('organizer', 'co_organizer')
    ) THEN
        v_user_can_edit := TRUE;
    END IF;

    -- 6. CHECK IF USER CAN JOIN
    IF v_activity.status = 'published'
       AND v_activity.scheduled_at > NOW()
       AND v_user_participation_status = 'not_participating'
       AND v_activity.current_participants_count < v_activity.max_participants
       AND NOT v_is_blocked
    THEN
        v_user_can_join := TRUE;
    END IF;

    -- Build tags array
    SELECT ARRAY_AGG(tag) INTO v_tags_array
    FROM activity.activity_tags
    WHERE activity_tags.activity_id = p_activity_id;

    -- 7. RETURN
    RETURN QUERY
    SELECT
        v_activity.activity_id,
        v_activity.organizer_user_id,
        u.username,
        u.first_name,
        u.main_photo_url,
        u.is_verified,
        v_activity.category_id,
        c.name as category_name,
        v_activity.title,
        v_activity.description,
        v_activity.activity_type,
        v_activity.activity_privacy_level,
        v_activity.status,
        v_activity.scheduled_at,
        v_activity.duration_minutes,
        v_activity.joinable_at_free,
        v_activity.max_participants,
        v_activity.current_participants_count,
        v_activity.waitlist_count,
        -- Location as JSONB
        (
            SELECT row_to_json(l.*)::JSONB
            FROM activity.activity_locations l
            WHERE l.activity_id = v_activity.activity_id
        ) as location,
        -- Tags
        COALESCE(v_tags_array, ARRAY[]::TEXT[]) as tags,
        v_activity.language,
        v_activity.external_chat_id,
        v_activity.created_at,
        v_activity.updated_at,
        v_activity.completed_at,
        v_activity.cancelled_at,
        v_user_participation_status,
        v_user_can_join,
        v_user_can_edit,
        v_is_blocked
    FROM activity.users u
    LEFT JOIN activity.categories c ON c.category_id = v_activity.category_id
    WHERE u.user_id = v_activity.organizer_user_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_get_by_id(p_activity_id uuid, p_requesting_user_id uuid) OWNER TO postgres;

--
-- Name: sp_activity_get_feed(uuid, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_get_feed(p_user_id uuid, p_limit integer) RETURNS TABLE(activity_id uuid, title character varying, description text, activity_type activity.activity_type, scheduled_at timestamp with time zone, duration_minutes integer, max_participants integer, current_participants_count integer, city character varying, language character varying, tags text[], organizer_username character varying, organizer_is_verified boolean, category_name character varying)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_blocked_users UUID[];
    v_user_interests TEXT[];
BEGIN
    -- 1. GET USER CONTEXT
    -- Get blocked users
    v_blocked_users := ARRAY(
        SELECT blocked_user_id FROM activity.user_blocks WHERE blocker_user_id = p_user_id
        UNION
        SELECT blocker_user_id FROM activity.user_blocks WHERE blocked_user_id = p_user_id
    );

    -- Get user interests
    SELECT ARRAY_AGG(interest_tag) INTO v_user_interests
    FROM activity.user_interests
    WHERE user_id = p_user_id;

    -- 2. RETURN PERSONALIZED ACTIVITIES
    -- Algorithm: Match based on user interests, friends' activities, and past participation
    RETURN QUERY
    SELECT DISTINCT
        a.activity_id,
        a.title,
        a.description,
        a.activity_type,
        a.scheduled_at,
        a.duration_minutes,
        a.max_participants,
        a.current_participants_count,
        a.city,
        a.language,
        ARRAY(
            SELECT tag FROM activity.activity_tags
            WHERE activity_tags.activity_id = a.activity_id
        ) as tags,
        u.username,
        u.is_verified,
        c.name as category_name
    FROM activity.activities a
    JOIN activity.users u ON u.user_id = a.organizer_user_id
    LEFT JOIN activity.categories c ON c.category_id = a.category_id
    WHERE a.status = 'published'
      AND a.scheduled_at > NOW()
      AND a.current_participants_count < a.max_participants
      AND (a.activity_type = 'xxl' OR a.organizer_user_id NOT IN (SELECT unnest(v_blocked_users)))
      AND (
          -- Match user interests
          EXISTS (
              SELECT 1 FROM activity.activity_tags at
              WHERE at.activity_id = a.activity_id
                AND at.tag = ANY(v_user_interests)
          )
          -- OR activities by friends
          OR EXISTS (
              SELECT 1 FROM activity.friendships f
              WHERE ((f.user_id_1 = p_user_id AND f.user_id_2 = a.organizer_user_id)
                 OR (f.user_id_2 = p_user_id AND f.user_id_1 = a.organizer_user_id))
                AND f.status = 'accepted'
          )
          -- OR similar to past activities
          OR a.category_id IN (
              SELECT DISTINCT a2.category_id
              FROM activity.participants p2
              JOIN activity.activities a2 ON a2.activity_id = p2.activity_id
              WHERE p2.user_id = p_user_id
                AND p2.attendance_status = 'attended'
          )
      )
    ORDER BY a.scheduled_at ASC
    LIMIT p_limit;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_get_feed(p_user_id uuid, p_limit integer) OWNER TO postgres;

--
-- Name: sp_activity_get_nearby(uuid, numeric, numeric, numeric, uuid, timestamp with time zone, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_get_nearby(p_user_id uuid, p_latitude numeric, p_longitude numeric, p_radius_km numeric, p_category_id uuid, p_date_from timestamp with time zone, p_limit integer, p_offset integer) RETURNS TABLE(total_count bigint, activity_id uuid, title character varying, description text, activity_type activity.activity_type, scheduled_at timestamp with time zone, duration_minutes integer, max_participants integer, current_participants_count integer, city character varying, language character varying, tags text[], organizer_username character varying, organizer_is_verified boolean, category_name character varying, distance_km numeric)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_blocked_users UUID[];
    v_total_count BIGINT;
BEGIN
    -- 1. GET BLOCKED USERS
    v_blocked_users := ARRAY(
        SELECT blocked_user_id FROM activity.user_blocks WHERE blocker_user_id = p_user_id
        UNION
        SELECT blocker_user_id FROM activity.user_blocks WHERE blocked_user_id = p_user_id
    );

    -- 2. CALCULATE DISTANCES AND COUNT
    -- Note: This uses simplified distance calculation (Haversine formula approximation)
    -- For production, consider using PostGIS ST_Distance
    WITH nearby AS (
        SELECT
            a.activity_id,
            a.organizer_user_id,
            a.title,
            a.description,
            a.activity_type,
            a.scheduled_at,
            a.duration_minutes,
            a.max_participants,
            a.current_participants_count,
            a.city,
            a.language,
            a.category_id,
            al.latitude,
            al.longitude,
            -- Simplified distance calculation (km)
            (6371 * acos(
                cos(radians(p_latitude)) *
                cos(radians(al.latitude)) *
                cos(radians(al.longitude) - radians(p_longitude)) +
                sin(radians(p_latitude)) *
                sin(radians(al.latitude))
            ))::DECIMAL(10, 2) as distance_km
        FROM activity.activities a
        JOIN activity.activity_locations al ON al.activity_id = a.activity_id
        WHERE a.status = 'published'
          AND a.scheduled_at > NOW()
          AND al.latitude IS NOT NULL
          AND al.longitude IS NOT NULL
          AND (a.activity_type = 'xxl' OR a.organizer_user_id NOT IN (SELECT unnest(v_blocked_users)))
          AND (p_category_id IS NULL OR a.category_id = p_category_id)
          AND (p_date_from IS NULL OR a.scheduled_at >= p_date_from)
    )
    SELECT COUNT(*) INTO v_total_count
    FROM nearby
    WHERE distance_km <= p_radius_km;

    -- 3. RETURN RESULTS
    RETURN QUERY
    WITH nearby AS (
        SELECT
            a.activity_id,
            a.organizer_user_id,
            a.title,
            a.description,
            a.activity_type,
            a.scheduled_at,
            a.duration_minutes,
            a.max_participants,
            a.current_participants_count,
            a.city,
            a.language,
            a.category_id,
            (6371 * acos(
                cos(radians(p_latitude)) *
                cos(radians(al.latitude)) *
                cos(radians(al.longitude) - radians(p_longitude)) +
                sin(radians(p_latitude)) *
                sin(radians(al.latitude))
            ))::DECIMAL(10, 2) as distance_km
        FROM activity.activities a
        JOIN activity.activity_locations al ON al.activity_id = a.activity_id
        WHERE a.status = 'published'
          AND a.scheduled_at > NOW()
          AND al.latitude IS NOT NULL
          AND al.longitude IS NOT NULL
          AND (a.activity_type = 'xxl' OR a.organizer_user_id NOT IN (SELECT unnest(v_blocked_users)))
          AND (p_category_id IS NULL OR a.category_id = p_category_id)
          AND (p_date_from IS NULL OR a.scheduled_at >= p_date_from)
    )
    SELECT
        v_total_count,
        n.activity_id,
        n.title,
        n.description,
        n.activity_type,
        n.scheduled_at,
        n.duration_minutes,
        n.max_participants,
        n.current_participants_count,
        n.city,
        n.language,
        ARRAY(
            SELECT tag FROM activity.activity_tags
            WHERE activity_tags.activity_id = n.activity_id
        ) as tags,
        u.username,
        u.is_verified,
        c.name as category_name,
        n.distance_km
    FROM nearby n
    JOIN activity.users u ON u.user_id = n.organizer_user_id
    LEFT JOIN activity.categories c ON c.category_id = n.category_id
    WHERE n.distance_km <= p_radius_km
    ORDER BY n.distance_km ASC, n.scheduled_at ASC
    LIMIT p_limit
    OFFSET p_offset;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_get_nearby(p_user_id uuid, p_latitude numeric, p_longitude numeric, p_radius_km numeric, p_category_id uuid, p_date_from timestamp with time zone, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_activity_get_participants(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_get_participants(p_activity_id uuid, p_requesting_user_id uuid) RETURNS TABLE(activity_id uuid, total_participants integer, max_participants integer, user_id uuid, username character varying, first_name character varying, main_photo_url character varying, is_verified boolean, role activity.participant_role, participation_status activity.participation_status, attendance_status activity.attendance_status, joined_at timestamp with time zone)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity RECORD;
    v_is_blocked BOOLEAN := FALSE;
BEGIN
    -- 1. VALIDATION
    -- Check if activity exists
    SELECT * INTO v_activity
    FROM activity.activities a
    WHERE a.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- 2. BLOCKING CHECK (except XXL)
    IF v_activity.activity_type != 'xxl' THEN
        IF EXISTS (
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = v_activity.organizer_user_id AND blocked_user_id = p_requesting_user_id)
               OR (blocker_user_id = p_requesting_user_id AND blocked_user_id = v_activity.organizer_user_id)
        ) THEN
            v_is_blocked := TRUE;
        END IF;

        IF v_is_blocked THEN
            RAISE EXCEPTION 'ERR_FORBIDDEN_BLOCKED' USING ERRCODE = '42501';
        END IF;
    END IF;

    -- 3. PRIVACY CHECK
    IF v_activity.activity_privacy_level = 'friends_only' THEN
        IF NOT EXISTS (
            SELECT 1 FROM activity.friendships
            WHERE ((user_id_1 = v_activity.organizer_user_id AND user_id_2 = p_requesting_user_id)
                OR (user_id_1 = p_requesting_user_id AND user_id_2 = v_activity.organizer_user_id))
              AND status = 'accepted'
        ) THEN
            -- Not a friend - check if user is participant
            IF NOT EXISTS (
                SELECT 1 FROM activity.participants
                WHERE activity_id = p_activity_id AND user_id = p_requesting_user_id
            ) THEN
                RAISE EXCEPTION 'ERR_FORBIDDEN_FRIENDS_ONLY' USING ERRCODE = '42501';
            END IF;
        END IF;
    END IF;

    IF v_activity.activity_privacy_level = 'invite_only' THEN
        IF NOT EXISTS (
            SELECT 1 FROM activity.activity_invitations
            WHERE activity_id = p_activity_id
              AND user_id = p_requesting_user_id
              AND status = 'accepted'
        ) THEN
            -- No invitation - check if user is participant
            IF NOT EXISTS (
                SELECT 1 FROM activity.participants
                WHERE activity_id = p_activity_id AND user_id = p_requesting_user_id
            ) THEN
                RAISE EXCEPTION 'ERR_FORBIDDEN_INVITE_ONLY' USING ERRCODE = '42501';
            END IF;
        END IF;
    END IF;

    -- 4. RETURN PARTICIPANTS
    RETURN QUERY
    SELECT
        p_activity_id,
        v_activity.current_participants_count,
        v_activity.max_participants,
        u.user_id,
        u.username,
        u.first_name,
        u.main_photo_url,
        u.is_verified,
        p.role,
        p.participation_status,
        p.attendance_status,
        p.joined_at
    FROM activity.participants p
    JOIN activity.users u ON u.user_id = p.user_id
    WHERE p.activity_id = p_activity_id
      AND p.participation_status = 'registered'
    ORDER BY
        CASE p.role
            WHEN 'organizer' THEN 1
            WHEN 'co_organizer' THEN 2
            ELSE 3
        END,
        p.joined_at ASC;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_get_participants(p_activity_id uuid, p_requesting_user_id uuid) OWNER TO postgres;

--
-- Name: sp_activity_get_recommendations(uuid, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_get_recommendations(p_user_id uuid, p_limit integer) RETURNS TABLE(activity_id uuid, title character varying, description text, activity_type activity.activity_type, scheduled_at timestamp with time zone, duration_minutes integer, max_participants integer, current_participants_count integer, city character varying, language character varying, tags text[], organizer_username character varying, organizer_is_verified boolean, category_name character varying)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_blocked_users UUID[];
BEGIN
    -- 1. GET BLOCKED USERS
    v_blocked_users := ARRAY(
        SELECT blocked_user_id FROM activity.user_blocks WHERE blocker_user_id = p_user_id
        UNION
        SELECT blocker_user_id FROM activity.user_blocks WHERE blocked_user_id = p_user_id
    );

    -- 2. COLLABORATIVE FILTERING
    -- Algorithm: Find users with similar activity participation and recommend their activities
    RETURN QUERY
    SELECT DISTINCT
        a.activity_id,
        a.title,
        a.description,
        a.activity_type,
        a.scheduled_at,
        a.duration_minutes,
        a.max_participants,
        a.current_participants_count,
        a.city,
        a.language,
        ARRAY(
            SELECT tag FROM activity.activity_tags
            WHERE activity_tags.activity_id = a.activity_id
        ) as tags,
        u.username,
        u.is_verified,
        c.name as category_name
    FROM activity.activities a
    JOIN activity.users u ON u.user_id = a.organizer_user_id
    LEFT JOIN activity.categories c ON c.category_id = a.category_id
    WHERE a.status = 'published'
      AND a.scheduled_at > NOW()
      AND a.current_participants_count < a.max_participants
      AND (a.activity_type = 'xxl' OR a.organizer_user_id NOT IN (SELECT unnest(v_blocked_users)))
      -- Find activities joined by similar users
      AND EXISTS (
          SELECT 1 FROM activity.participants p1
          WHERE p1.activity_id = a.activity_id
            AND p1.user_id IN (
                -- Find similar users (participated in same activities)
                SELECT DISTINCT p2.user_id
                FROM activity.participants p2
                WHERE p2.activity_id IN (
                    SELECT activity_id FROM activity.participants
                    WHERE user_id = p_user_id
                      AND attendance_status = 'attended'
                )
                AND p2.user_id != p_user_id
                AND p2.attendance_status = 'attended'
            )
      )
      -- Exclude activities user already joined
      AND NOT EXISTS (
          SELECT 1 FROM activity.participants p3
          WHERE p3.activity_id = a.activity_id
            AND p3.user_id = p_user_id
      )
    ORDER BY a.scheduled_at ASC
    LIMIT p_limit;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_get_recommendations(p_user_id uuid, p_limit integer) OWNER TO postgres;

--
-- Name: sp_activity_get_waitlist(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_get_waitlist(p_activity_id uuid, p_requesting_user_id uuid) RETURNS TABLE(activity_id uuid, total_waitlist integer, user_id uuid, username character varying, first_name character varying, main_photo_url character varying, is_verified boolean, waitlist_position integer, created_at timestamp with time zone, notified_at timestamp with time zone)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity RECORD;
    v_is_organizer BOOLEAN := FALSE;
BEGIN
    -- 1. VALIDATION
    -- Check if activity exists
    SELECT * INTO v_activity
    FROM activity.activities a
    WHERE a.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- 2. AUTHORIZATION CHECK
    -- Only organizer and co-organizers can view waitlist
    SELECT EXISTS (
        SELECT 1 FROM activity.participants
        WHERE activity_id = p_activity_id
          AND user_id = p_requesting_user_id
          AND role IN ('organizer', 'co_organizer')
    ) INTO v_is_organizer;

    IF NOT v_is_organizer THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NOT_ORGANIZER' USING ERRCODE = '42501';
    END IF;

    -- 3. RETURN WAITLIST
    RETURN QUERY
    SELECT
        p_activity_id,
        v_activity.waitlist_count,
        u.user_id,
        u.username,
        u.first_name,
        u.main_photo_url,
        u.is_verified,
        w.position,
        w.created_at,
        w.notified_at
    FROM activity.waitlist_entries w
    JOIN activity.users u ON u.user_id = w.user_id
    WHERE w.activity_id = p_activity_id
    ORDER BY w.position ASC;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_get_waitlist(p_activity_id uuid, p_requesting_user_id uuid) OWNER TO postgres;

--
-- Name: sp_activity_review_create(uuid, uuid, integer, text, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_review_create(p_activity_id uuid, p_reviewer_user_id uuid, p_rating integer, p_review_text text, p_is_anonymous boolean) RETURNS TABLE(review_id uuid, activity_id uuid, reviewer_user_id uuid, reviewer_username character varying, reviewer_first_name character varying, reviewer_main_photo_url character varying, reviewer_is_verified boolean, rating integer, review_text text, is_anonymous boolean, created_at timestamp with time zone, updated_at timestamp with time zone, is_own_review boolean)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity RECORD;
    v_review_id UUID;
    v_participation RECORD;
BEGIN
    -- 1. VALIDATION
    -- Check if activity exists
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activities.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- Check if activity is completed
    IF v_activity.status != 'completed' THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_ACTIVITY_NOT_COMPLETED' USING ERRCODE = '42501';
    END IF;

    -- Check if user participated
    SELECT * INTO v_participation
    FROM activity.participants
    WHERE activity_id = p_activity_id
      AND user_id = p_reviewer_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NOT_PARTICIPANT' USING ERRCODE = '42501';
    END IF;

    -- Check if user attended (not no-show)
    IF v_participation.attendance_status = 'no_show' THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NO_SHOW' USING ERRCODE = '42501';
    END IF;

    -- Check if review already exists
    IF EXISTS (
        SELECT 1 FROM activity.activity_reviews
        WHERE activity_id = p_activity_id
          AND reviewer_user_id = p_reviewer_user_id
    ) THEN
        RAISE EXCEPTION 'ERR_CONFLICT_REVIEW_EXISTS' USING ERRCODE = '23505';
    END IF;

    -- Validate rating range
    IF p_rating < 1 OR p_rating > 5 THEN
        RAISE EXCEPTION 'ERR_VALIDATION_INVALID_RATING' USING ERRCODE = '22000';
    END IF;

    -- 2. CREATE REVIEW
    INSERT INTO activity.activity_reviews (
        activity_id,
        reviewer_user_id,
        rating,
        review_text,
        is_anonymous
    ) VALUES (
        p_activity_id,
        p_reviewer_user_id,
        p_rating,
        p_review_text,
        COALESCE(p_is_anonymous, FALSE)
    ) RETURNING activity_reviews.review_id INTO v_review_id;

    -- 3. RETURN
    RETURN QUERY
    SELECT
        v_review_id,
        p_activity_id,
        CASE WHEN p_is_anonymous THEN NULL ELSE u.user_id END,
        CASE WHEN p_is_anonymous THEN NULL ELSE u.username END,
        CASE WHEN p_is_anonymous THEN NULL ELSE u.first_name END,
        CASE WHEN p_is_anonymous THEN NULL ELSE u.main_photo_url END,
        CASE WHEN p_is_anonymous THEN NULL ELSE u.is_verified END,
        p_rating,
        p_review_text,
        COALESCE(p_is_anonymous, FALSE),
        NOW(),
        NULL::TIMESTAMP WITH TIME ZONE,
        TRUE  -- is_own_review
    FROM activity.users u
    WHERE u.user_id = p_reviewer_user_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_review_create(p_activity_id uuid, p_reviewer_user_id uuid, p_rating integer, p_review_text text, p_is_anonymous boolean) OWNER TO postgres;

--
-- Name: sp_activity_review_delete(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_review_delete(p_review_id uuid, p_user_id uuid) RETURNS TABLE(deleted boolean, message text)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_review RECORD;
BEGIN
    -- 1. VALIDATION
    -- Check if review exists
    SELECT * INTO v_review
    FROM activity.activity_reviews
    WHERE review_id = p_review_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_REVIEW' USING ERRCODE = '42704';
    END IF;

    -- Check if user is the reviewer
    IF v_review.reviewer_user_id != p_user_id THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NOT_REVIEWER' USING ERRCODE = '42501';
    END IF;

    -- 2. DELETE REVIEW
    DELETE FROM activity.activity_reviews WHERE review_id = p_review_id;

    -- 3. RETURN
    RETURN QUERY
    SELECT TRUE, 'Review deleted successfully'::TEXT;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_review_delete(p_review_id uuid, p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_activity_review_get_list(uuid, uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_review_get_list(p_activity_id uuid, p_requesting_user_id uuid, p_limit integer, p_offset integer) RETURNS TABLE(activity_id uuid, total_reviews bigint, average_rating numeric, review_id uuid, reviewer_user_id uuid, reviewer_username character varying, reviewer_first_name character varying, reviewer_main_photo_url character varying, reviewer_is_verified boolean, rating integer, review_text text, is_anonymous boolean, created_at timestamp with time zone, updated_at timestamp with time zone, is_own_review boolean)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_total_reviews BIGINT;
    v_average_rating NUMERIC;
BEGIN
    -- 1. VALIDATION
    -- Check if activity exists
    IF NOT EXISTS (
        SELECT 1 FROM activity.activities WHERE activities.activity_id = p_activity_id
    ) THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- 2. GET STATISTICS
    SELECT
        COUNT(*)::BIGINT,
        AVG(r.rating)::NUMERIC(3,2)
    INTO v_total_reviews, v_average_rating
    FROM activity.activity_reviews r
    WHERE r.activity_id = p_activity_id;

    -- 3. RETURN REVIEWS
    RETURN QUERY
    SELECT
        p_activity_id,
        v_total_reviews,
        v_average_rating,
        r.review_id,
        CASE WHEN r.is_anonymous THEN NULL ELSE u.user_id END,
        CASE WHEN r.is_anonymous THEN NULL ELSE u.username END,
        CASE WHEN r.is_anonymous THEN NULL ELSE u.first_name END,
        CASE WHEN r.is_anonymous THEN NULL ELSE u.main_photo_url END,
        CASE WHEN r.is_anonymous THEN NULL ELSE u.is_verified END,
        r.rating,
        r.review_text,
        r.is_anonymous,
        r.created_at,
        r.updated_at,
        CASE WHEN p_requesting_user_id IS NOT NULL AND r.reviewer_user_id = p_requesting_user_id
            THEN TRUE ELSE FALSE END as is_own_review
    FROM activity.activity_reviews r
    JOIN activity.users u ON u.user_id = r.reviewer_user_id
    WHERE r.activity_id = p_activity_id
    ORDER BY r.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_review_get_list(p_activity_id uuid, p_requesting_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_activity_review_update(uuid, uuid, integer, text, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_review_update(p_review_id uuid, p_user_id uuid, p_rating integer, p_review_text text, p_is_anonymous boolean) RETURNS TABLE(review_id uuid, activity_id uuid, reviewer_user_id uuid, reviewer_username character varying, reviewer_first_name character varying, reviewer_main_photo_url character varying, reviewer_is_verified boolean, rating integer, review_text text, is_anonymous boolean, created_at timestamp with time zone, updated_at timestamp with time zone, is_own_review boolean)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_review RECORD;
    v_is_anonymous BOOLEAN;
BEGIN
    -- 1. VALIDATION
    -- Check if review exists
    SELECT * INTO v_review
    FROM activity.activity_reviews
    WHERE activity_reviews.review_id = p_review_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_REVIEW' USING ERRCODE = '42704';
    END IF;

    -- Check if user is the reviewer
    IF v_review.reviewer_user_id != p_user_id THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NOT_REVIEWER' USING ERRCODE = '42501';
    END IF;

    -- Validate rating if provided
    IF p_rating IS NOT NULL AND (p_rating < 1 OR p_rating > 5) THEN
        RAISE EXCEPTION 'ERR_VALIDATION_INVALID_RATING' USING ERRCODE = '22000';
    END IF;

    -- 2. UPDATE REVIEW
    UPDATE activity.activity_reviews
    SET
        rating = COALESCE(p_rating, rating),
        review_text = COALESCE(p_review_text, review_text),
        is_anonymous = COALESCE(p_is_anonymous, is_anonymous),
        updated_at = NOW()
    WHERE activity_reviews.review_id = p_review_id
    RETURNING is_anonymous INTO v_is_anonymous;

    -- 3. RETURN
    RETURN QUERY
    SELECT
        r.review_id,
        r.activity_id,
        CASE WHEN v_is_anonymous THEN NULL ELSE u.user_id END,
        CASE WHEN v_is_anonymous THEN NULL ELSE u.username END,
        CASE WHEN v_is_anonymous THEN NULL ELSE u.first_name END,
        CASE WHEN v_is_anonymous THEN NULL ELSE u.main_photo_url END,
        CASE WHEN v_is_anonymous THEN NULL ELSE u.is_verified END,
        r.rating,
        r.review_text,
        r.is_anonymous,
        r.created_at,
        r.updated_at,
        TRUE  -- is_own_review
    FROM activity.activity_reviews r
    JOIN activity.users u ON u.user_id = r.reviewer_user_id
    WHERE r.review_id = p_review_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_review_update(p_review_id uuid, p_user_id uuid, p_rating integer, p_review_text text, p_is_anonymous boolean) OWNER TO postgres;

--
-- Name: sp_activity_search(uuid, character varying, uuid, activity.activity_type, character varying, character varying, jsonb, timestamp with time zone, timestamp with time zone, boolean, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_search(p_user_id uuid, p_query character varying, p_category_id uuid, p_activity_type activity.activity_type, p_city character varying, p_language character varying, p_tags jsonb, p_date_from timestamp with time zone, p_date_to timestamp with time zone, p_has_spots_available boolean, p_limit integer, p_offset integer) RETURNS TABLE(total_count bigint, activity_id uuid, title character varying, description text, activity_type activity.activity_type, scheduled_at timestamp with time zone, duration_minutes integer, max_participants integer, current_participants_count integer, city character varying, language character varying, tags text[], organizer_username character varying, organizer_is_verified boolean, category_name character varying)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_blocked_users UUID[];
    v_user_subscription VARCHAR(50);
    v_total_count BIGINT;
BEGIN
    -- 1. GET USER CONTEXT
    -- Get user subscription level
    SELECT subscription_level INTO v_user_subscription
    FROM activity.users
    WHERE user_id = p_user_id;

    -- Validate language filter (Premium only)
    IF p_language IS NOT NULL AND v_user_subscription NOT IN ('premium', 'club') THEN
        RAISE EXCEPTION 'ERR_PREMIUM_REQUIRED_LANGUAGE_FILTER' USING ERRCODE = '42501';
    END IF;

    -- Get blocked users (both directions)
    v_blocked_users := ARRAY(
        SELECT blocked_user_id FROM activity.user_blocks WHERE blocker_user_id = p_user_id
        UNION
        SELECT blocker_user_id FROM activity.user_blocks WHERE blocked_user_id = p_user_id
    );

    -- 2. SEARCH QUERY
    -- First get total count
    SELECT COUNT(*) INTO v_total_count
    FROM activity.activities a
    WHERE a.status = 'published'
      AND a.scheduled_at > NOW()
      -- Blocking filter (except XXL)
      AND (a.activity_type = 'xxl' OR a.organizer_user_id NOT IN (SELECT unnest(v_blocked_users)))
      -- Text search filter
      AND (p_query IS NULL OR (a.title ILIKE '%' || p_query || '%' OR a.description ILIKE '%' || p_query || '%'))
      -- Category filter
      AND (p_category_id IS NULL OR a.category_id = p_category_id)
      -- Activity type filter
      AND (p_activity_type IS NULL OR a.activity_type = p_activity_type)
      -- City filter
      AND (p_city IS NULL OR a.city ILIKE p_city)
      -- Language filter (Premium only)
      AND (p_language IS NULL OR a.language = p_language)
      -- Date range filters
      AND (p_date_from IS NULL OR a.scheduled_at >= p_date_from)
      AND (p_date_to IS NULL OR a.scheduled_at <= p_date_to)
      -- Spots available filter
      AND (p_has_spots_available IS NULL OR p_has_spots_available = FALSE
           OR a.current_participants_count < a.max_participants)
      -- Tag filter (match any tag)
      AND (p_tags IS NULL OR EXISTS (
          SELECT 1 FROM activity.activity_tags at
          WHERE at.activity_id = a.activity_id
            AND at.tag = ANY(ARRAY(SELECT jsonb_array_elements_text(p_tags)))
      ));

    -- 3. RETURN RESULTS
    RETURN QUERY
    SELECT
        v_total_count,
        a.activity_id,
        a.title,
        a.description,
        a.activity_type,
        a.scheduled_at,
        a.duration_minutes,
        a.max_participants,
        a.current_participants_count,
        a.city,
        a.language,
        ARRAY(
            SELECT tag FROM activity.activity_tags
            WHERE activity_tags.activity_id = a.activity_id
        ) as tags,
        u.username,
        u.is_verified,
        c.name as category_name
    FROM activity.activities a
    JOIN activity.users u ON u.user_id = a.organizer_user_id
    LEFT JOIN activity.categories c ON c.category_id = a.category_id
    WHERE a.status = 'published'
      AND a.scheduled_at > NOW()
      AND (a.activity_type = 'xxl' OR a.organizer_user_id NOT IN (SELECT unnest(v_blocked_users)))
      AND (p_query IS NULL OR (a.title ILIKE '%' || p_query || '%' OR a.description ILIKE '%' || p_query || '%'))
      AND (p_category_id IS NULL OR a.category_id = p_category_id)
      AND (p_activity_type IS NULL OR a.activity_type = p_activity_type)
      AND (p_city IS NULL OR a.city ILIKE p_city)
      AND (p_language IS NULL OR a.language = p_language)
      AND (p_date_from IS NULL OR a.scheduled_at >= p_date_from)
      AND (p_date_to IS NULL OR a.scheduled_at <= p_date_to)
      AND (p_has_spots_available IS NULL OR p_has_spots_available = FALSE
           OR a.current_participants_count < a.max_participants)
      AND (p_tags IS NULL OR EXISTS (
          SELECT 1 FROM activity.activity_tags at
          WHERE at.activity_id = a.activity_id
            AND at.tag = ANY(ARRAY(SELECT jsonb_array_elements_text(p_tags)))
      ))
    ORDER BY a.scheduled_at ASC
    LIMIT p_limit
    OFFSET p_offset;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_search(p_user_id uuid, p_query character varying, p_category_id uuid, p_activity_type activity.activity_type, p_city character varying, p_language character varying, p_tags jsonb, p_date_from timestamp with time zone, p_date_to timestamp with time zone, p_has_spots_available boolean, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_activity_tag_get_popular(integer, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_tag_get_popular(p_limit integer, p_prefix character varying) RETURNS TABLE(tag character varying, usage_count bigint)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    -- Query activity_tags and aggregate by tag
    RETURN QUERY
    SELECT
        at.tag,
        COUNT(*)::BIGINT as usage_count
    FROM activity.activity_tags at
    -- Filter by prefix if provided
    WHERE p_prefix IS NULL OR at.tag ILIKE (p_prefix || '%')
    GROUP BY at.tag
    ORDER BY usage_count DESC, at.tag ASC
    LIMIT p_limit;

END;
$$;


ALTER FUNCTION activity.sp_activity_tag_get_popular(p_limit integer, p_prefix character varying) OWNER TO postgres;

--
-- Name: sp_activity_update(uuid, uuid, uuid, character varying, text, activity.activity_type, activity.activity_privacy_level, timestamp with time zone, integer, timestamp with time zone, integer, character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying, numeric, numeric, character varying, jsonb); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_activity_update(p_activity_id uuid, p_user_id uuid, p_category_id uuid, p_title character varying, p_description text, p_activity_type activity.activity_type, p_activity_privacy_level activity.activity_privacy_level, p_scheduled_at timestamp with time zone, p_duration_minutes integer, p_joinable_at_free timestamp with time zone, p_max_participants integer, p_language character varying, p_external_chat_id character varying, p_venue_name character varying, p_address_line1 character varying, p_address_line2 character varying, p_city character varying, p_state_province character varying, p_postal_code character varying, p_country character varying, p_latitude numeric, p_longitude numeric, p_place_id character varying, p_tags jsonb) RETURNS TABLE(activity_id uuid, title character varying, description text, scheduled_at timestamp with time zone, updated_at timestamp with time zone)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_activity RECORD;
    v_location_exists BOOLEAN;
BEGIN
    -- 1. VALIDATION
    -- Check if activity exists
    SELECT * INTO v_activity
    FROM activity.activities a
    WHERE a.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERR_NOT_FOUND_ACTIVITY' USING ERRCODE = '42704';
    END IF;

    -- Check if activity is not cancelled or completed
    IF v_activity.status IN ('cancelled', 'completed') THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_ACTIVITY_CLOSED' USING ERRCODE = '42501';
    END IF;

    -- Check if user is organizer or co-organizer
    IF NOT EXISTS (
        SELECT 1 FROM activity.participants
        WHERE activity_id = p_activity_id
          AND user_id = p_user_id
          AND role IN ('organizer', 'co_organizer')
    ) THEN
        RAISE EXCEPTION 'ERR_FORBIDDEN_NOT_ORGANIZER' USING ERRCODE = '42501';
    END IF;

    -- Validate scheduled_at if provided
    IF p_scheduled_at IS NOT NULL AND p_scheduled_at <= NOW() THEN
        RAISE EXCEPTION 'ERR_SCHEDULED_AT_PAST' USING ERRCODE = '22000';
    END IF;

    -- Validate max_participants if provided
    IF p_max_participants IS NOT NULL THEN
        IF p_max_participants < v_activity.current_participants_count THEN
            RAISE EXCEPTION 'ERR_CANNOT_REDUCE_PARTICIPANTS' USING ERRCODE = '22000';
        END IF;
        IF p_max_participants < 2 OR p_max_participants > 1000 THEN
            RAISE EXCEPTION 'ERR_INVALID_MAX_PARTICIPANTS' USING ERRCODE = '22000';
        END IF;
    END IF;

    -- Validate category if provided
    IF p_category_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM activity.categories
        WHERE category_id = p_category_id AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'ERR_CATEGORY_NOT_FOUND' USING ERRCODE = '42704';
    END IF;

    -- 2. UPDATE ACTIVITY
    UPDATE activity.activities
    SET
        category_id = COALESCE(p_category_id, category_id),
        title = COALESCE(p_title, title),
        description = COALESCE(p_description, description),
        activity_type = COALESCE(p_activity_type, activity_type),
        activity_privacy_level = COALESCE(p_activity_privacy_level, activity_privacy_level),
        scheduled_at = COALESCE(p_scheduled_at, scheduled_at),
        duration_minutes = COALESCE(p_duration_minutes, duration_minutes),
        joinable_at_free = COALESCE(p_joinable_at_free, joinable_at_free),
        max_participants = COALESCE(p_max_participants, max_participants),
        language = COALESCE(p_language, language),
        external_chat_id = COALESCE(p_external_chat_id, external_chat_id),
        location_name = COALESCE(p_venue_name, location_name),
        city = COALESCE(p_city, city),
        updated_at = NOW()
    WHERE activities.activity_id = p_activity_id;

    -- 3. UPDATE/INSERT LOCATION
    IF p_venue_name IS NOT NULL OR p_latitude IS NOT NULL THEN
        -- Check if location exists
        SELECT EXISTS (
            SELECT 1 FROM activity.activity_locations
            WHERE activity_locations.activity_id = p_activity_id
        ) INTO v_location_exists;

        IF v_location_exists THEN
            -- Update existing location
            UPDATE activity.activity_locations
            SET
                venue_name = COALESCE(p_venue_name, venue_name),
                address_line1 = COALESCE(p_address_line1, address_line1),
                address_line2 = COALESCE(p_address_line2, address_line2),
                city = COALESCE(p_city, city),
                state_province = COALESCE(p_state_province, state_province),
                postal_code = COALESCE(p_postal_code, postal_code),
                country = COALESCE(p_country, country),
                latitude = COALESCE(p_latitude, latitude),
                longitude = COALESCE(p_longitude, longitude),
                place_id = COALESCE(p_place_id, place_id),
                updated_at = NOW()
            WHERE activity_locations.activity_id = p_activity_id;
        ELSE
            -- Insert new location
            INSERT INTO activity.activity_locations (
                activity_id, venue_name, address_line1, address_line2,
                city, state_province, postal_code, country,
                latitude, longitude, place_id
            ) VALUES (
                p_activity_id, p_venue_name, p_address_line1, p_address_line2,
                p_city, p_state_province, p_postal_code, p_country,
                p_latitude, p_longitude, p_place_id
            );
        END IF;
    END IF;

    -- 4. UPDATE TAGS if provided
    IF p_tags IS NOT NULL THEN
        -- Delete existing tags
        DELETE FROM activity.activity_tags WHERE activity_tags.activity_id = p_activity_id;

        -- Insert new tags
        IF jsonb_array_length(p_tags) > 0 THEN
            INSERT INTO activity.activity_tags (activity_id, tag)
            SELECT p_activity_id, jsonb_array_elements_text(p_tags);
        END IF;
    END IF;

    -- 5. RETURN
    RETURN QUERY
    SELECT
        a.activity_id,
        a.title,
        a.description,
        a.scheduled_at,
        a.updated_at
    FROM activity.activities a
    WHERE a.activity_id = p_activity_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_activity_update(p_activity_id uuid, p_user_id uuid, p_category_id uuid, p_title character varying, p_description text, p_activity_type activity.activity_type, p_activity_privacy_level activity.activity_privacy_level, p_scheduled_at timestamp with time zone, p_duration_minutes integer, p_joinable_at_free timestamp with time zone, p_max_participants integer, p_language character varying, p_external_chat_id character varying, p_venue_name character varying, p_address_line1 character varying, p_address_line2 character varying, p_city character varying, p_state_province character varying, p_postal_code character varying, p_country character varying, p_latitude numeric, p_longitude numeric, p_place_id character varying, p_tags jsonb) OWNER TO postgres;

--
-- Name: sp_add_organization_member(uuid, uuid, text, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_add_organization_member(p_user_id uuid, p_org_id uuid, p_role text, p_invited_by uuid) RETURNS TABLE(id uuid, user_email text, role text, joined_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Insert membership (ON CONFLICT DO NOTHING for idempotency)
    INSERT INTO activity.organization_members (user_id, organization_id, role, invited_by)
    VALUES (p_user_id, p_org_id, p_role, p_invited_by)
    ON CONFLICT (user_id, organization_id) DO NOTHING;

    -- Return membership info
    RETURN QUERY
    SELECT
        om.id,
        u.email,
        om.role,
        om.joined_at
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.id
    WHERE om.user_id = p_user_id
      AND om.organization_id = p_org_id;
END;
$$;


ALTER FUNCTION activity.sp_add_organization_member(p_user_id uuid, p_org_id uuid, p_role text, p_invited_by uuid) OWNER TO postgres;

--
-- Name: sp_add_organization_member_v2(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_add_organization_member_v2(p_user_id uuid, p_org_id uuid, p_role text) RETURNS TABLE(ret_user_id uuid, ret_organization_id uuid, ret_user_email character varying, ret_role character varying, ret_joined_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Insert membership (ON CONFLICT DO NOTHING for idempotency)
    -- Cast p_role to activity.organization_role enum type
    INSERT INTO activity.organization_members (user_id, organization_id, role)
    VALUES (p_user_id, p_org_id, p_role::activity.organization_role)
    ON CONFLICT (organization_id, user_id) DO NOTHING;

    -- Return membership info
    RETURN QUERY
    SELECT 
        om.user_id,
        om.organization_id,
        u.email::varchar,
        om.role::varchar,
        om.joined_at
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.user_id
    WHERE om.user_id = p_user_id
      AND om.organization_id = p_org_id;
END;
$$;


ALTER FUNCTION activity.sp_add_organization_member_v2(p_user_id uuid, p_org_id uuid, p_role text) OWNER TO postgres;

--
-- Name: sp_add_profile_photo(uuid, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_add_profile_photo(p_user_id uuid, p_photo_url character varying) RETURNS TABLE(success boolean, message text, photo_count integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_current_photos JSONB;
    v_photo_count INT;
BEGIN
    -- Get current photos
    SELECT profile_photos_extra INTO v_current_photos
    FROM activity.users
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'User not found'::TEXT, 0;
        RETURN;
    END IF;

    -- Check photo count
    v_photo_count := jsonb_array_length(v_current_photos);

    IF v_photo_count >= 8 THEN
        RETURN QUERY SELECT FALSE, 'Maximum 8 photos allowed'::TEXT, v_photo_count;
        RETURN;
    END IF;

    -- Check if photo already exists
    IF v_current_photos @> to_jsonb(ARRAY[p_photo_url]) THEN
        RETURN QUERY SELECT FALSE, 'Photo already added'::TEXT, v_photo_count;
        RETURN;
    END IF;

    -- Add photo to array
    UPDATE activity.users
    SET
        profile_photos_extra = profile_photos_extra || to_jsonb(ARRAY[p_photo_url]),
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE, 'Photo added successfully'::TEXT, v_photo_count + 1;
END;
$$;


ALTER FUNCTION activity.sp_add_profile_photo(p_user_id uuid, p_photo_url character varying) OWNER TO postgres;

--
-- Name: sp_add_user_interest(uuid, character varying, numeric); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_add_user_interest(p_user_id uuid, p_interest_tag character varying, p_weight numeric DEFAULT 1.0) RETURNS TABLE(success boolean, message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_interest_count INT;
BEGIN
    -- Validate weight
    IF p_weight < 0 OR p_weight > 1 THEN
        RAISE EXCEPTION 'Interest weight must be between 0.0 and 1.0';
    END IF;

    -- Count existing interests
    SELECT COUNT(*) INTO v_interest_count
    FROM activity.user_interests
    WHERE user_id = p_user_id;

    IF v_interest_count >= 20 THEN
        RETURN QUERY SELECT FALSE, 'Maximum 20 interests allowed'::TEXT;
        RETURN;
    END IF;

    -- Insert or update interest
    INSERT INTO activity.user_interests (user_id, interest_tag, weight)
    VALUES (p_user_id, p_interest_tag, p_weight)
    ON CONFLICT (user_id, interest_tag)
    DO UPDATE SET weight = p_weight, updated_at = NOW();

    RETURN QUERY SELECT TRUE, 'Interest added successfully'::TEXT;
END;
$$;


ALTER FUNCTION activity.sp_add_user_interest(p_user_id uuid, p_interest_tag character varying, p_weight numeric) OWNER TO postgres;

--
-- Name: sp_ban_user(uuid, text, timestamp with time zone); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_ban_user(p_user_id uuid, p_ban_reason text, p_ban_expires_at timestamp with time zone DEFAULT NULL::timestamp with time zone) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Validate expiry date (must be in future if provided)
    IF p_ban_expires_at IS NOT NULL AND p_ban_expires_at <= NOW() THEN
        RAISE EXCEPTION 'Ban expiry date must be in the future';
    END IF;

    -- Update user status
    IF p_ban_expires_at IS NULL THEN
        -- Permanent ban
        UPDATE activity.users
        SET
            status = 'banned',
            ban_reason = p_ban_reason,
            ban_expires_at = NULL,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    ELSE
        -- Temporary ban
        UPDATE activity.users
        SET
            status = 'temporary_ban',
            ban_reason = p_ban_reason,
            ban_expires_at = p_ban_expires_at,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    END IF;

    RETURN QUERY SELECT FOUND;
END;
$$;


ALTER FUNCTION activity.sp_ban_user(p_user_id uuid, p_ban_reason text, p_ban_expires_at timestamp with time zone) OWNER TO postgres;

--
-- Name: sp_cancel_invitation(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_cancel_invitation(p_invitation_id uuid, p_cancelling_user_id uuid) RETURNS TABLE(success boolean, activity_id uuid, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_invitation RECORD;
    v_activity RECORD;
    v_participant RECORD;
    v_is_authorized BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE 'sp_cancel_invitation called: invitation_id=%, cancelling_user_id=%',
        p_invitation_id, p_cancelling_user_id;

    -- Get invitation details
    SELECT * INTO v_invitation
    FROM activity.activity_invitations
    WHERE invitation_id = p_invitation_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Invitation not found: %', p_invitation_id;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'INVITATION_NOT_FOUND'::VARCHAR(50), 'Invitation does not exist'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'Invitation found: activity_id=%, invited_by_user_id=%, status=%',
        v_invitation.activity_id, v_invitation.invited_by_user_id, v_invitation.status;

    -- Check invitation status
    IF v_invitation.status != 'pending' THEN
        RAISE NOTICE 'Invitation already responded: status=%', v_invitation.status;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'ALREADY_RESPONDED'::VARCHAR(50), 'Cannot cancel responded invitation'::TEXT;
        RETURN;
    END IF;

    -- Check authorization
    -- Can cancel if: organizer, co-organizer, or the person who sent the invitation
    IF v_invitation.invited_by_user_id = p_cancelling_user_id THEN
        v_is_authorized := TRUE;
        RAISE NOTICE 'User sent this invitation - authorized';
    ELSE
        -- Check if organizer or co-organizer
        SELECT * INTO v_participant
        FROM activity.participants
        WHERE activity_id = v_invitation.activity_id
          AND user_id = p_cancelling_user_id;

        IF FOUND AND (v_participant.role = 'organizer' OR v_participant.role = 'co_organizer') THEN
            v_is_authorized := TRUE;
            RAISE NOTICE 'User is organizer/co-organizer - authorized';
        END IF;
    END IF;

    IF NOT v_is_authorized THEN
        RAISE NOTICE 'User not authorized to cancel invitation';
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'NOT_AUTHORIZED'::VARCHAR(50), 'Not authorized to cancel this invitation'::TEXT;
        RETURN;
    END IF;

    -- Cancel invitation (delete it)
    RAISE NOTICE 'Cancelling invitation';
    DELETE FROM activity.activity_invitations
    WHERE invitation_id = p_invitation_id;

    RAISE NOTICE 'Invitation cancelled successfully';

    RETURN QUERY SELECT TRUE, v_invitation.activity_id,
        NULL::VARCHAR(50), NULL::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_cancel_invitation(p_invitation_id uuid, p_cancelling_user_id uuid) OWNER TO postgres;

--
-- Name: FUNCTION sp_cancel_invitation(p_invitation_id uuid, p_cancelling_user_id uuid); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_cancel_invitation(p_invitation_id uuid, p_cancelling_user_id uuid) IS 'Cancel invitation (organizer/co-organizer/sender only)';


--
-- Name: sp_cancel_participation(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_cancel_participation(p_activity_id uuid, p_user_id uuid, p_reason text DEFAULT NULL::text) RETURNS TABLE(success boolean, promoted_user_id uuid, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_participant RECORD;
    v_next_waitlist RECORD;
BEGIN
    RAISE NOTICE 'sp_cancel_participation called: activity_id=%, user_id=%, reason=%',
        p_activity_id, p_user_id, p_reason;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check activity is not in the past
    IF v_activity.scheduled_at <= NOW() THEN
        RAISE NOTICE 'Activity is in the past: scheduled_at=%', v_activity.scheduled_at;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'ACTIVITY_IN_PAST'::VARCHAR(50), 'Cannot cancel past activities'::TEXT;
        RETURN;
    END IF;

    -- Check if user is participant
    SELECT * INTO v_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_user_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'User is not a participant';
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'NOT_PARTICIPANT'::VARCHAR(50), 'Not a participant of this activity'::TEXT;
        RETURN;
    END IF;

    IF v_participant.participation_status = 'cancelled' THEN
        RAISE NOTICE 'Participation already cancelled';
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'ALREADY_CANCELLED'::VARCHAR(50), 'Participation already cancelled'::TEXT;
        RETURN;
    END IF;

    IF v_participant.participation_status != 'registered' THEN
        RAISE NOTICE 'Participation status is not registered: status=%', v_participant.participation_status;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'NOT_PARTICIPANT'::VARCHAR(50), 'Not a registered participant'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'Cancelling participation';

    -- Update participation status
    UPDATE activity.participants
    SET participation_status = 'cancelled',
        left_at = NOW(),
        payload = CASE
            WHEN p_reason IS NOT NULL THEN jsonb_set(COALESCE(payload, '{}'::jsonb), '{cancel_reason}', to_jsonb(p_reason))
            ELSE payload
        END
    WHERE activity_id = p_activity_id AND user_id = p_user_id;

    UPDATE activity.activities
    SET current_participants_count = current_participants_count - 1
    WHERE activity_id = p_activity_id;

    RAISE NOTICE 'Participation cancelled, checking waitlist for promotion';

    -- Promote next from waitlist
    SELECT * INTO v_next_waitlist
    FROM activity.waitlist_entries
    WHERE activity_id = p_activity_id
    ORDER BY position ASC
    LIMIT 1;

    IF FOUND THEN
        RAISE NOTICE 'Promoting from waitlist: user_id=%, position=%',
            v_next_waitlist.user_id, v_next_waitlist.position;

        -- Add promoted user as participant
        INSERT INTO activity.participants (activity_id, user_id, role, participation_status)
        VALUES (p_activity_id, v_next_waitlist.user_id, 'member', 'registered');

        -- Remove from waitlist
        DELETE FROM activity.waitlist_entries
        WHERE waitlist_id = v_next_waitlist.waitlist_id;

        -- Update counts
        UPDATE activity.activities
        SET waitlist_count = waitlist_count - 1,
            current_participants_count = current_participants_count + 1
        WHERE activity_id = p_activity_id;

        -- Update waitlist positions
        UPDATE activity.waitlist_entries
        SET position = position - 1
        WHERE activity_id = p_activity_id;

        RAISE NOTICE 'Waitlist promotion complete';

        RETURN QUERY SELECT TRUE, v_next_waitlist.user_id,
            NULL::VARCHAR(50), NULL::TEXT;
        RETURN;
    ELSE
        RAISE NOTICE 'No waitlist to promote';
        RETURN QUERY SELECT TRUE, NULL::UUID,
            NULL::VARCHAR(50), NULL::TEXT;
        RETURN;
    END IF;
END;
$$;


ALTER FUNCTION activity.sp_cancel_participation(p_activity_id uuid, p_user_id uuid, p_reason text) OWNER TO postgres;

--
-- Name: FUNCTION sp_cancel_participation(p_activity_id uuid, p_user_id uuid, p_reason text); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_cancel_participation(p_activity_id uuid, p_user_id uuid, p_reason text) IS 'Cancel participation with reason tracking and waitlist promotion';


--
-- Name: sp_check_org_permission(uuid, uuid, text[]); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_check_org_permission(p_user_id uuid, p_org_id uuid, p_required_roles text[]) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_role TEXT;
    v_has_permission BOOLEAN;
BEGIN
    -- Get user's role
    SELECT role INTO v_user_role
    FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    -- Check if role is in required roles
    v_has_permission := v_user_role = ANY(p_required_roles);

    RETURN COALESCE(v_has_permission, FALSE);
END;
$$;


ALTER FUNCTION activity.sp_check_org_permission(p_user_id uuid, p_org_id uuid, p_required_roles text[]) OWNER TO postgres;

--
-- Name: sp_cleanup_unverified_users(integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_cleanup_unverified_users(p_days_old integer DEFAULT 7) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    rows_deleted INTEGER;
BEGIN
    DELETE FROM activity.users
    WHERE is_verified = FALSE
      AND created_at < NOW() - INTERVAL '1 day' * p_days_old;
    
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN rows_deleted;
END;
$$;


ALTER FUNCTION activity.sp_cleanup_unverified_users(p_days_old integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_cleanup_unverified_users(p_days_old integer); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_cleanup_unverified_users(p_days_old integer) IS 'Delete users who have not verified their email after specified days.
Default is 7 days. Returns number of deleted users.
This should be run as a scheduled job (cron/pg_cron).';


--
-- Name: sp_community_comment_create(uuid, uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_comment_create(p_post_id uuid, p_author_user_id uuid, p_parent_comment_id uuid, p_content text) RETURNS TABLE(comment_id uuid, post_id uuid, parent_comment_id uuid, author_user_id uuid, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_comment_id UUID;
    v_created_at TIMESTAMP WITH TIME ZONE;
    v_community_id UUID;
    v_post_status activity.content_status;
BEGIN
    -- 1. Validate post exists and get details
    SELECT p.community_id, p.status
    INTO v_community_id, v_post_status
    FROM activity.posts p
    WHERE p.post_id = p_post_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'POST_NOT_FOUND';
    END IF;

    IF v_post_status != 'published' THEN
        RAISE EXCEPTION 'POST_NOT_PUBLISHED';
    END IF;

    -- 2. Check user is active member
    IF NOT EXISTS (
        SELECT 1 FROM activity.community_members cm
        WHERE cm.community_id = v_community_id
        AND cm.user_id = p_author_user_id
        AND cm.status = 'active'
    ) THEN
        RAISE EXCEPTION 'NOT_MEMBER';
    END IF;

    -- 3. If parent comment provided, validate it
    IF p_parent_comment_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM activity.comments c
            WHERE c.comment_id = p_parent_comment_id
            AND c.post_id = p_post_id
            AND c.is_deleted = FALSE
        ) THEN
            RAISE EXCEPTION 'PARENT_COMMENT_NOT_FOUND';
        END IF;
    END IF;

    -- 4. Insert comment
    v_created_at := NOW();
    INSERT INTO activity.comments (
        post_id,
        parent_comment_id,
        author_user_id,
        content,
        is_deleted,
        reaction_count,
        created_at
    ) VALUES (
        p_post_id,
        p_parent_comment_id,
        p_author_user_id,
        p_content,
        FALSE,
        0,
        v_created_at
    ) RETURNING comments.comment_id INTO v_comment_id;

    -- 5. Update post comment count
    UPDATE activity.posts
    SET comment_count = comment_count + 1
    WHERE posts.post_id = p_post_id;

    -- 6. Return comment details
    RETURN QUERY
    SELECT v_comment_id, p_post_id, p_parent_comment_id, p_author_user_id, v_created_at;
END;
$$;


ALTER FUNCTION activity.sp_community_comment_create(p_post_id uuid, p_author_user_id uuid, p_parent_comment_id uuid, p_content text) OWNER TO postgres;

--
-- Name: sp_community_comment_delete(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_comment_delete(p_comment_id uuid, p_deleting_user_id uuid) RETURNS TABLE(comment_id uuid, deleted_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_author_user_id UUID;
    v_post_id UUID;
    v_community_id UUID;
    v_deleted_at TIMESTAMP WITH TIME ZONE;
    v_is_organizer BOOLEAN;
BEGIN
    -- 1. Get comment details
    SELECT c.author_user_id, c.post_id
    INTO v_author_user_id, v_post_id
    FROM activity.comments c
    WHERE c.comment_id = p_comment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'COMMENT_NOT_FOUND';
    END IF;

    -- Get community_id from post
    SELECT p.community_id INTO v_community_id
    FROM activity.posts p
    WHERE p.post_id = v_post_id;

    -- 2. Check if user is author or community organizer
    v_is_organizer := EXISTS (
        SELECT 1 FROM activity.community_members cm
        WHERE cm.community_id = v_community_id
        AND cm.user_id = p_deleting_user_id
        AND cm.role = 'organizer'
        AND cm.status = 'active'
    );

    IF v_author_user_id != p_deleting_user_id AND NOT v_is_organizer THEN
        RAISE EXCEPTION 'INSUFFICIENT_PERMISSIONS';
    END IF;

    -- 3. Soft delete comment
    v_deleted_at := NOW();
    UPDATE activity.comments
    SET is_deleted = TRUE, updated_at = v_deleted_at
    WHERE comments.comment_id = p_comment_id;

    -- 4. Update post comment count
    UPDATE activity.posts
    SET comment_count = comment_count - 1
    WHERE posts.post_id = v_post_id;

    -- 5. Return confirmation
    RETURN QUERY
    SELECT p_comment_id, v_deleted_at;
END;
$$;


ALTER FUNCTION activity.sp_community_comment_delete(p_comment_id uuid, p_deleting_user_id uuid) OWNER TO postgres;

--
-- Name: sp_community_comment_update(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_comment_update(p_comment_id uuid, p_updating_user_id uuid, p_content text) RETURNS TABLE(comment_id uuid, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_author_user_id UUID;
    v_is_deleted BOOLEAN;
    v_updated_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 1. Get comment details
    SELECT c.author_user_id, c.is_deleted
    INTO v_author_user_id, v_is_deleted
    FROM activity.comments c
    WHERE c.comment_id = p_comment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'COMMENT_NOT_FOUND';
    END IF;

    IF v_is_deleted THEN
        RAISE EXCEPTION 'COMMENT_DELETED';
    END IF;

    -- 2. Check user is author
    IF v_author_user_id != p_updating_user_id THEN
        RAISE EXCEPTION 'INSUFFICIENT_PERMISSIONS';
    END IF;

    -- 3. Update comment
    v_updated_at := NOW();
    UPDATE activity.comments
    SET content = p_content, updated_at = v_updated_at
    WHERE comments.comment_id = p_comment_id;

    -- 4. Return updated details
    RETURN QUERY
    SELECT p_comment_id, v_updated_at;
END;
$$;


ALTER FUNCTION activity.sp_community_comment_update(p_comment_id uuid, p_updating_user_id uuid, p_content text) OWNER TO postgres;

--
-- Name: sp_community_create(uuid, uuid, character varying, character varying, text, activity.community_type, character varying, character varying, integer, text[]); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_create(p_creator_user_id uuid, p_organization_id uuid, p_name character varying, p_slug character varying, p_description text, p_community_type activity.community_type, p_cover_image_url character varying, p_icon_url character varying, p_max_members integer, p_tags text[]) RETURNS TABLE(community_id uuid, slug character varying, created_at timestamp with time zone, member_count integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_community_id UUID;
    v_created_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 1. Validate user exists
    IF NOT EXISTS (SELECT 1 FROM activity.users WHERE user_id = p_creator_user_id) THEN
        RAISE EXCEPTION 'USER_NOT_FOUND';
    END IF;

    -- 2. If org provided, validate membership
    IF p_organization_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM activity.organizations WHERE organization_id = p_organization_id) THEN
            RAISE EXCEPTION 'ORGANIZATION_NOT_FOUND';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM activity.organization_members
            WHERE organization_id = p_organization_id
            AND user_id = p_creator_user_id
        ) THEN
            RAISE EXCEPTION 'NOT_ORGANIZATION_MEMBER';
        END IF;
    END IF;

    -- 3. Validate slug uniqueness
    IF EXISTS (
        SELECT 1 FROM activity.communities
        WHERE communities.slug = p_slug
        AND (
            (communities.organization_id = p_organization_id) OR
            (communities.organization_id IS NULL AND p_organization_id IS NULL)
        )
    ) THEN
        RAISE EXCEPTION 'SLUG_EXISTS';
    END IF;

    -- 4. Validate community type (Phase 1: only 'open')
    IF p_community_type != 'open' THEN
        RAISE EXCEPTION 'INVALID_COMMUNITY_TYPE';
    END IF;

    -- 5. Insert community
    INSERT INTO activity.communities (
        organization_id,
        creator_user_id,
        name,
        slug,
        description,
        community_type,
        status,
        member_count,
        max_members,
        cover_image_url,
        icon_url
    ) VALUES (
        p_organization_id,
        p_creator_user_id,
        p_name,
        p_slug,
        p_description,
        p_community_type,
        'active',
        1,
        p_max_members,
        p_cover_image_url,
        p_icon_url
    ) RETURNING communities.community_id, communities.created_at
    INTO v_community_id, v_created_at;

    -- 6. Insert creator as organizer
    INSERT INTO activity.community_members (
        community_id,
        user_id,
        role,
        status
    ) VALUES (
        v_community_id,
        p_creator_user_id,
        'organizer',
        'active'
    );

    -- 7. Insert tags if provided
    IF p_tags IS NOT NULL AND array_length(p_tags, 1) > 0 THEN
        INSERT INTO activity.community_tags (community_id, tag)
        SELECT v_community_id, unnest(p_tags);
    END IF;

    -- 8. Return community details
    RETURN QUERY
    SELECT v_community_id, p_slug, v_created_at, 1;
END;
$$;


ALTER FUNCTION activity.sp_community_create(p_creator_user_id uuid, p_organization_id uuid, p_name character varying, p_slug character varying, p_description text, p_community_type activity.community_type, p_cover_image_url character varying, p_icon_url character varying, p_max_members integer, p_tags text[]) OWNER TO postgres;

--
-- Name: sp_community_get_by_id(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_get_by_id(p_community_id uuid, p_requesting_user_id uuid) RETURNS TABLE(community_id uuid, organization_id uuid, creator_user_id uuid, name character varying, slug character varying, description text, community_type activity.community_type, status activity.community_status, member_count integer, max_members integer, is_featured boolean, cover_image_url character varying, icon_url character varying, created_at timestamp with time zone, updated_at timestamp with time zone, is_member boolean, user_role activity.participant_role, user_status activity.membership_status, tags text[])
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.community_id,
        c.organization_id,
        c.creator_user_id,
        c.name,
        c.slug,
        c.description,
        c.community_type,
        c.status,
        c.member_count,
        c.max_members,
        c.is_featured,
        c.cover_image_url,
        c.icon_url,
        c.created_at,
        c.updated_at,
        CASE WHEN cm.user_id IS NOT NULL THEN TRUE ELSE FALSE END as is_member,
        cm.role as user_role,
        cm.status as user_status,
        COALESCE(ARRAY_AGG(ct.tag) FILTER (WHERE ct.tag IS NOT NULL), ARRAY[]::TEXT[]) as tags
    FROM activity.communities c
    LEFT JOIN activity.community_members cm
        ON c.community_id = cm.community_id
        AND cm.user_id = p_requesting_user_id
        AND cm.status = 'active'
    LEFT JOIN activity.community_tags ct
        ON c.community_id = ct.community_id
    WHERE c.community_id = p_community_id
    GROUP BY
        c.community_id, c.organization_id, c.creator_user_id, c.name, c.slug,
        c.description, c.community_type, c.status, c.member_count, c.max_members,
        c.is_featured, c.cover_image_url, c.icon_url, c.created_at, c.updated_at,
        cm.user_id, cm.role, cm.status;
END;
$$;


ALTER FUNCTION activity.sp_community_get_by_id(p_community_id uuid, p_requesting_user_id uuid) OWNER TO postgres;

--
-- Name: sp_community_get_members(uuid, uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_get_members(p_community_id uuid, p_requesting_user_id uuid, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0) RETURNS TABLE(user_id uuid, username character varying, first_name character varying, last_name character varying, main_photo_url character varying, role activity.participant_role, status activity.membership_status, joined_at timestamp with time zone, is_verified boolean, total_count bigint)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_community_type activity.community_type;
    v_is_member BOOLEAN;
BEGIN
    -- 1. Validate community exists
    SELECT c.community_type INTO v_community_type
    FROM activity.communities c
    WHERE c.community_id = p_community_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_FOUND';
    END IF;

    -- 2. Check permission (is member OR community is open)
    SELECT EXISTS (
        SELECT 1 FROM activity.community_members cm
        WHERE cm.community_id = p_community_id
        AND cm.user_id = p_requesting_user_id
        AND cm.status = 'active'
    ) INTO v_is_member;

    IF NOT v_is_member AND v_community_type != 'open' THEN
        RAISE EXCEPTION 'INSUFFICIENT_PERMISSIONS';
    END IF;

    -- 3. Return members
    RETURN QUERY
    SELECT
        u.user_id,
        u.username,
        u.first_name,
        u.last_name,
        u.main_photo_url,
        cm.role,
        cm.status,
        cm.joined_at,
        u.is_verified,
        COUNT(*) OVER() as total_count
    FROM activity.community_members cm
    JOIN activity.users u ON cm.user_id = u.user_id
    WHERE cm.community_id = p_community_id
    AND cm.status = 'active'
    ORDER BY
        CASE cm.role
            WHEN 'organizer' THEN 1
            WHEN 'co_organizer' THEN 2
            ELSE 3
        END,
        cm.joined_at ASC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_community_get_members(p_community_id uuid, p_requesting_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_community_join(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_join(p_community_id uuid, p_user_id uuid) RETURNS TABLE(community_id uuid, user_id uuid, role activity.participant_role, status activity.membership_status, joined_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_community_type activity.community_type;
    v_member_count INT;
    v_max_members INT;
    v_status activity.community_status;
    v_joined_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 1. Validate community exists and get details
    SELECT c.community_type, c.member_count, c.max_members, c.status
    INTO v_community_type, v_member_count, v_max_members, v_status
    FROM activity.communities c
    WHERE c.community_id = p_community_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_FOUND';
    END IF;

    -- Check community is active
    IF v_status != 'active' THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_ACTIVE';
    END IF;

    -- Check community is open type
    IF v_community_type != 'open' THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_OPEN';
    END IF;

    -- 2. Check if max_members reached
    IF v_max_members IS NOT NULL AND v_member_count >= v_max_members THEN
        RAISE EXCEPTION 'COMMUNITY_FULL';
    END IF;

    -- 3. Check user not already member
    IF EXISTS (
        SELECT 1 FROM activity.community_members
        WHERE community_members.community_id = p_community_id
        AND community_members.user_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'ALREADY_MEMBER';
    END IF;

    -- 4. Insert membership
    v_joined_at := NOW();
    INSERT INTO activity.community_members (
        community_id,
        user_id,
        role,
        status,
        joined_at
    ) VALUES (
        p_community_id,
        p_user_id,
        'member',
        'active',
        v_joined_at
    );

    -- 5. Update member count
    UPDATE activity.communities
    SET member_count = member_count + 1
    WHERE communities.community_id = p_community_id;

    -- 6. Return membership details
    RETURN QUERY
    SELECT p_community_id, p_user_id, 'member'::activity.participant_role, 'active'::activity.membership_status, v_joined_at;
END;
$$;


ALTER FUNCTION activity.sp_community_join(p_community_id uuid, p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_community_leave(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_leave(p_community_id uuid, p_user_id uuid) RETURNS TABLE(community_id uuid, user_id uuid, left_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_role activity.participant_role;
    v_status activity.membership_status;
    v_left_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 1. Get membership details
    SELECT cm.role, cm.status
    INTO v_role, v_status
    FROM activity.community_members cm
    WHERE cm.community_id = p_community_id
    AND cm.user_id = p_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'NOT_MEMBER';
    END IF;

    -- Check if already left
    IF v_status != 'active' THEN
        RAISE EXCEPTION 'NOT_MEMBER';
    END IF;

    -- 2. Check user is NOT organizer
    IF v_role = 'organizer' THEN
        RAISE EXCEPTION 'ORGANIZER_CANNOT_LEAVE';
    END IF;

    -- 3. Update membership status
    v_left_at := NOW();
    UPDATE activity.community_members
    SET status = 'left', left_at = v_left_at
    WHERE community_members.community_id = p_community_id
    AND community_members.user_id = p_user_id;

    -- 4. Update member count
    UPDATE activity.communities
    SET member_count = member_count - 1
    WHERE communities.community_id = p_community_id;

    -- 5. Return confirmation
    RETURN QUERY
    SELECT p_community_id, p_user_id, v_left_at;
END;
$$;


ALTER FUNCTION activity.sp_community_leave(p_community_id uuid, p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_community_link_activity(uuid, uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_link_activity(p_community_id uuid, p_activity_id uuid, p_linking_user_id uuid) RETURNS TABLE(community_id uuid, activity_id uuid, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_created_at TIMESTAMP WITH TIME ZONE;
    v_community_status activity.community_status;
    v_activity_status activity.activity_status;
BEGIN
    -- 1. Validate community exists and is active
    SELECT c.status INTO v_community_status
    FROM activity.communities c
    WHERE c.community_id = p_community_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_FOUND';
    END IF;

    IF v_community_status != 'active' THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_ACTIVE';
    END IF;

    -- 2. Validate activity exists and is published
    SELECT a.status INTO v_activity_status
    FROM activity.activities a
    WHERE a.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ACTIVITY_NOT_FOUND';
    END IF;

    -- Note: activity status might be different enum, checking for 'published' as per spec
    -- Adjust if the actual status field uses different values

    -- 3. Check user is community organizer
    IF NOT EXISTS (
        SELECT 1 FROM activity.community_members cm
        WHERE cm.community_id = p_community_id
        AND cm.user_id = p_linking_user_id
        AND cm.role = 'organizer'
        AND cm.status = 'active'
    ) THEN
        RAISE EXCEPTION 'NOT_COMMUNITY_ORGANIZER';
    END IF;

    -- 4. Check user is activity organizer
    IF NOT EXISTS (
        SELECT 1 FROM activity.activity_participants ap
        WHERE ap.activity_id = p_activity_id
        AND ap.user_id = p_linking_user_id
        AND ap.role = 'organizer'
    ) THEN
        RAISE EXCEPTION 'NOT_ACTIVITY_ORGANIZER';
    END IF;

    -- 5. Check link doesn't already exist
    IF EXISTS (
        SELECT 1 FROM activity.community_activities ca
        WHERE ca.community_id = p_community_id
        AND ca.activity_id = p_activity_id
    ) THEN
        RAISE EXCEPTION 'LINK_ALREADY_EXISTS';
    END IF;

    -- 6. Insert link
    v_created_at := NOW();
    INSERT INTO activity.community_activities (
        community_id,
        activity_id,
        is_pinned,
        created_at
    ) VALUES (
        p_community_id,
        p_activity_id,
        FALSE,
        v_created_at
    );

    -- 7. Return link details
    RETURN QUERY
    SELECT p_community_id, p_activity_id, v_created_at;
END;
$$;


ALTER FUNCTION activity.sp_community_link_activity(p_community_id uuid, p_activity_id uuid, p_linking_user_id uuid) OWNER TO postgres;

--
-- Name: sp_community_post_create(uuid, uuid, uuid, character varying, text, activity.content_type); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_post_create(p_community_id uuid, p_author_user_id uuid, p_activity_id uuid, p_title character varying, p_content text, p_content_type activity.content_type DEFAULT 'post'::activity.content_type) RETURNS TABLE(post_id uuid, community_id uuid, author_user_id uuid, created_at timestamp with time zone, status activity.content_status)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_post_id UUID;
    v_created_at TIMESTAMP WITH TIME ZONE;
    v_community_status activity.community_status;
BEGIN
    -- 1. Validate community exists and is active
    SELECT c.status INTO v_community_status
    FROM activity.communities c
    WHERE c.community_id = p_community_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_FOUND';
    END IF;

    IF v_community_status != 'active' THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_ACTIVE';
    END IF;

    -- 2. Check user is active member
    IF NOT EXISTS (
        SELECT 1 FROM activity.community_members cm
        WHERE cm.community_id = p_community_id
        AND cm.user_id = p_author_user_id
        AND cm.status = 'active'
    ) THEN
        RAISE EXCEPTION 'NOT_MEMBER';
    END IF;

    -- 3. If activity_id provided, validate it exists
    IF p_activity_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM activity.activities WHERE activity_id = p_activity_id) THEN
            RAISE EXCEPTION 'ACTIVITY_NOT_FOUND';
        END IF;
    END IF;

    -- 4. Insert post
    v_created_at := NOW();
    INSERT INTO activity.posts (
        community_id,
        author_user_id,
        activity_id,
        title,
        content,
        content_type,
        status,
        view_count,
        comment_count,
        reaction_count,
        created_at
    ) VALUES (
        p_community_id,
        p_author_user_id,
        p_activity_id,
        p_title,
        p_content,
        p_content_type,
        'published',
        0,
        0,
        0,
        v_created_at
    ) RETURNING posts.post_id INTO v_post_id;

    -- 5. Return post details
    RETURN QUERY
    SELECT v_post_id, p_community_id, p_author_user_id, v_created_at, 'published'::activity.content_status;
END;
$$;


ALTER FUNCTION activity.sp_community_post_create(p_community_id uuid, p_author_user_id uuid, p_activity_id uuid, p_title character varying, p_content text, p_content_type activity.content_type) OWNER TO postgres;

--
-- Name: sp_community_post_delete(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_post_delete(p_post_id uuid, p_deleting_user_id uuid) RETURNS TABLE(post_id uuid, deleted_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_author_user_id UUID;
    v_community_id UUID;
    v_deleted_at TIMESTAMP WITH TIME ZONE;
    v_is_organizer BOOLEAN;
BEGIN
    -- 1. Get post details
    SELECT p.author_user_id, p.community_id
    INTO v_author_user_id, v_community_id
    FROM activity.posts p
    WHERE p.post_id = p_post_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'POST_NOT_FOUND';
    END IF;

    -- 2. Check if user is author or community organizer
    v_is_organizer := EXISTS (
        SELECT 1 FROM activity.community_members cm
        WHERE cm.community_id = v_community_id
        AND cm.user_id = p_deleting_user_id
        AND cm.role = 'organizer'
        AND cm.status = 'active'
    );

    IF v_author_user_id != p_deleting_user_id AND NOT v_is_organizer THEN
        RAISE EXCEPTION 'INSUFFICIENT_PERMISSIONS';
    END IF;

    -- 3. Soft delete post
    v_deleted_at := NOW();
    UPDATE activity.posts
    SET status = 'removed', updated_at = v_deleted_at
    WHERE posts.post_id = p_post_id;

    -- 4. Return confirmation
    RETURN QUERY
    SELECT p_post_id, v_deleted_at;
END;
$$;


ALTER FUNCTION activity.sp_community_post_delete(p_post_id uuid, p_deleting_user_id uuid) OWNER TO postgres;

--
-- Name: sp_community_post_get_comments(uuid, uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_post_get_comments(p_post_id uuid, p_parent_comment_id uuid, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0) RETURNS TABLE(comment_id uuid, parent_comment_id uuid, author_user_id uuid, author_username character varying, author_first_name character varying, author_main_photo_url character varying, content text, reaction_count integer, is_deleted boolean, created_at timestamp with time zone, updated_at timestamp with time zone, total_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- 1. Validate post exists
    IF NOT EXISTS (SELECT 1 FROM activity.posts WHERE post_id = p_post_id) THEN
        RAISE EXCEPTION 'POST_NOT_FOUND';
    END IF;

    -- 2. Return comments
    RETURN QUERY
    SELECT
        c.comment_id,
        c.parent_comment_id,
        c.author_user_id,
        u.username,
        u.first_name,
        u.main_photo_url,
        CASE WHEN c.is_deleted THEN '[deleted]' ELSE c.content END as content,
        c.reaction_count,
        c.is_deleted,
        c.created_at,
        c.updated_at,
        COUNT(*) OVER() as total_count
    FROM activity.comments c
    JOIN activity.users u ON c.author_user_id = u.user_id
    WHERE c.post_id = p_post_id
    AND (
        (c.parent_comment_id = p_parent_comment_id) OR
        (c.parent_comment_id IS NULL AND p_parent_comment_id IS NULL)
    )
    ORDER BY c.created_at ASC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_community_post_get_comments(p_post_id uuid, p_parent_comment_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_community_post_get_feed(uuid, uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_post_get_feed(p_community_id uuid, p_requesting_user_id uuid, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(post_id uuid, author_user_id uuid, author_username character varying, author_first_name character varying, author_main_photo_url character varying, activity_id uuid, title character varying, content text, content_type activity.content_type, view_count integer, comment_count integer, reaction_count integer, is_pinned boolean, created_at timestamp with time zone, updated_at timestamp with time zone, total_count bigint)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_community_type activity.community_type;
    v_is_member BOOLEAN;
BEGIN
    -- 1. Validate community exists
    SELECT c.community_type INTO v_community_type
    FROM activity.communities c
    WHERE c.community_id = p_community_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'COMMUNITY_NOT_FOUND';
    END IF;

    -- 2. Check permission (is member OR community is open)
    SELECT EXISTS (
        SELECT 1 FROM activity.community_members cm
        WHERE cm.community_id = p_community_id
        AND cm.user_id = p_requesting_user_id
        AND cm.status = 'active'
    ) INTO v_is_member;

    IF NOT v_is_member AND v_community_type != 'open' THEN
        RAISE EXCEPTION 'INSUFFICIENT_PERMISSIONS';
    END IF;

    -- 3. Return post feed
    RETURN QUERY
    SELECT
        p.post_id,
        p.author_user_id,
        u.username,
        u.first_name,
        u.main_photo_url,
        p.activity_id,
        p.title,
        p.content,
        p.content_type,
        p.view_count,
        p.comment_count,
        p.reaction_count,
        p.is_pinned,
        p.created_at,
        p.updated_at,
        COUNT(*) OVER() as total_count
    FROM activity.posts p
    JOIN activity.users u ON p.author_user_id = u.user_id
    WHERE p.community_id = p_community_id
    AND p.status = 'published'
    ORDER BY p.is_pinned DESC, p.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_community_post_get_feed(p_community_id uuid, p_requesting_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_community_post_update(uuid, uuid, character varying, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_post_update(p_post_id uuid, p_updating_user_id uuid, p_title character varying, p_content text) RETURNS TABLE(post_id uuid, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_author_user_id UUID;
    v_status activity.content_status;
    v_updated_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 1. Get post details
    SELECT p.author_user_id, p.status
    INTO v_author_user_id, v_status
    FROM activity.posts p
    WHERE p.post_id = p_post_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'POST_NOT_FOUND';
    END IF;

    -- Check post is published
    IF v_status != 'published' THEN
        RAISE EXCEPTION 'POST_NOT_PUBLISHED';
    END IF;

    -- 2. Check user is author
    IF v_author_user_id != p_updating_user_id THEN
        RAISE EXCEPTION 'INSUFFICIENT_PERMISSIONS';
    END IF;

    -- 3. Update post
    v_updated_at := NOW();
    UPDATE activity.posts
    SET
        title = COALESCE(p_title, title),
        content = COALESCE(p_content, content),
        updated_at = v_updated_at
    WHERE posts.post_id = p_post_id;

    -- 4. Return updated details
    RETURN QUERY
    SELECT p_post_id, v_updated_at;
END;
$$;


ALTER FUNCTION activity.sp_community_post_update(p_post_id uuid, p_updating_user_id uuid, p_title character varying, p_content text) OWNER TO postgres;

--
-- Name: sp_community_reaction_create(uuid, character varying, uuid, activity.reaction_type); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_reaction_create(p_user_id uuid, p_target_type character varying, p_target_id uuid, p_reaction_type activity.reaction_type) RETURNS TABLE(reaction_id uuid, target_type character varying, target_id uuid, reaction_type activity.reaction_type, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_reaction_id UUID;
    v_existing_reaction_type activity.reaction_type;
    v_created_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 1. Validate target exists
    IF p_target_type = 'post' THEN
        IF NOT EXISTS (SELECT 1 FROM activity.posts WHERE post_id = p_target_id) THEN
            RAISE EXCEPTION 'TARGET_NOT_FOUND';
        END IF;
    ELSIF p_target_type = 'comment' THEN
        IF NOT EXISTS (SELECT 1 FROM activity.comments WHERE comment_id = p_target_id) THEN
            RAISE EXCEPTION 'TARGET_NOT_FOUND';
        END IF;
    ELSE
        RAISE EXCEPTION 'INVALID_TARGET_TYPE';
    END IF;

    -- 2. Check if reaction already exists
    SELECT r.reaction_id, r.reaction_type
    INTO v_reaction_id, v_existing_reaction_type
    FROM activity.reactions r
    WHERE r.user_id = p_user_id
    AND r.target_type = p_target_type
    AND r.target_id = p_target_id;

    IF FOUND THEN
        -- Reaction exists
        IF v_existing_reaction_type = p_reaction_type THEN
            -- Same reaction, do nothing (idempotent)
            SELECT created_at INTO v_created_at
            FROM activity.reactions
            WHERE reaction_id = v_reaction_id;

            RETURN QUERY
            SELECT v_reaction_id, p_target_type, p_target_id, p_reaction_type, v_created_at;
            RETURN;
        ELSE
            -- Different reaction, update
            UPDATE activity.reactions
            SET reaction_type = p_reaction_type, created_at = NOW()
            WHERE reaction_id = v_reaction_id
            RETURNING created_at INTO v_created_at;

            RETURN QUERY
            SELECT v_reaction_id, p_target_type, p_target_id, p_reaction_type, v_created_at;
            RETURN;
        END IF;
    END IF;

    -- 3. Insert new reaction
    v_created_at := NOW();
    INSERT INTO activity.reactions (
        user_id,
        target_type,
        target_id,
        reaction_type,
        created_at
    ) VALUES (
        p_user_id,
        p_target_type,
        p_target_id,
        p_reaction_type,
        v_created_at
    ) RETURNING reactions.reaction_id INTO v_reaction_id;

    -- 4. Update target reaction count
    IF p_target_type = 'post' THEN
        UPDATE activity.posts
        SET reaction_count = reaction_count + 1
        WHERE post_id = p_target_id;
    ELSIF p_target_type = 'comment' THEN
        UPDATE activity.comments
        SET reaction_count = reaction_count + 1
        WHERE comment_id = p_target_id;
    END IF;

    -- 5. Return reaction details
    RETURN QUERY
    SELECT v_reaction_id, p_target_type, p_target_id, p_reaction_type, v_created_at;
END;
$$;


ALTER FUNCTION activity.sp_community_reaction_create(p_user_id uuid, p_target_type character varying, p_target_id uuid, p_reaction_type activity.reaction_type) OWNER TO postgres;

--
-- Name: sp_community_reaction_delete(uuid, character varying, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_reaction_delete(p_user_id uuid, p_target_type character varying, p_target_id uuid) RETURNS TABLE(deleted boolean)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_reaction_exists BOOLEAN;
BEGIN
    -- 1. Check if reaction exists
    SELECT EXISTS (
        SELECT 1 FROM activity.reactions r
        WHERE r.user_id = p_user_id
        AND r.target_type = p_target_type
        AND r.target_id = p_target_id
    ) INTO v_reaction_exists;

    IF NOT v_reaction_exists THEN
        -- Idempotent: no reaction to delete
        RETURN QUERY SELECT FALSE;
        RETURN;
    END IF;

    -- 2. Delete reaction
    DELETE FROM activity.reactions
    WHERE user_id = p_user_id
    AND target_type = p_target_type
    AND target_id = p_target_id;

    -- 3. Update target reaction count
    IF p_target_type = 'post' THEN
        UPDATE activity.posts
        SET reaction_count = reaction_count - 1
        WHERE post_id = p_target_id;
    ELSIF p_target_type = 'comment' THEN
        UPDATE activity.comments
        SET reaction_count = reaction_count - 1
        WHERE comment_id = p_target_id;
    END IF;

    -- 4. Return success
    RETURN QUERY SELECT TRUE;
END;
$$;


ALTER FUNCTION activity.sp_community_reaction_delete(p_user_id uuid, p_target_type character varying, p_target_id uuid) OWNER TO postgres;

--
-- Name: sp_community_search(text, uuid, text[], uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_search(p_search_text text, p_organization_id uuid, p_tags text[], p_requesting_user_id uuid, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(community_id uuid, organization_id uuid, name character varying, slug character varying, description text, community_type activity.community_type, member_count integer, max_members integer, is_featured boolean, cover_image_url character varying, icon_url character varying, created_at timestamp with time zone, is_member boolean, tags text[], total_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.community_id,
        c.organization_id,
        c.name,
        c.slug,
        c.description,
        c.community_type,
        c.member_count,
        c.max_members,
        c.is_featured,
        c.cover_image_url,
        c.icon_url,
        c.created_at,
        CASE WHEN cm.user_id IS NOT NULL THEN TRUE ELSE FALSE END as is_member,
        COALESCE(ARRAY_AGG(ct.tag::TEXT) FILTER (WHERE ct.tag IS NOT NULL), ARRAY[]::TEXT[]) as tags,
        COUNT(*) OVER() as total_count
    FROM activity.communities c
    LEFT JOIN activity.community_members cm
        ON c.community_id = cm.community_id
        AND cm.user_id = p_requesting_user_id
        AND cm.status = 'active'
    LEFT JOIN activity.community_tags ct
        ON c.community_id = ct.community_id
    WHERE c.status = 'active'
        AND (p_search_text IS NULL OR (
            c.name ILIKE '%' || p_search_text || '%' OR
            c.description ILIKE '%' || p_search_text || '%'
        ))
        AND (p_organization_id IS NULL OR c.organization_id = p_organization_id)
        AND (p_tags IS NULL OR EXISTS (
            SELECT 1 FROM activity.community_tags ct2
            WHERE ct2.community_id = c.community_id
            AND ct2.tag = ANY(p_tags)
        ))
    GROUP BY
        c.community_id, c.organization_id, c.name, c.slug, c.description,
        c.community_type, c.member_count, c.max_members, c.is_featured,
        c.cover_image_url, c.icon_url, c.created_at, cm.user_id
    ORDER BY c.is_featured DESC, c.member_count DESC, c.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_community_search(p_search_text text, p_organization_id uuid, p_tags text[], p_requesting_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_community_update(uuid, uuid, character varying, text, character varying, character varying, integer, text[]); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_community_update(p_community_id uuid, p_updating_user_id uuid, p_name character varying, p_description text, p_cover_image_url character varying, p_icon_url character varying, p_max_members integer, p_tags text[]) RETURNS TABLE(community_id uuid, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_updated_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 1. Validate community exists and status='active'
    IF NOT EXISTS (
        SELECT 1 FROM activity.communities
        WHERE communities.community_id = p_community_id
        AND status = 'active'
    ) THEN
        IF NOT EXISTS (SELECT 1 FROM activity.communities WHERE communities.community_id = p_community_id) THEN
            RAISE EXCEPTION 'COMMUNITY_NOT_FOUND';
        ELSE
            RAISE EXCEPTION 'COMMUNITY_NOT_ACTIVE';
        END IF;
    END IF;

    -- 2. Check user is organizer
    IF NOT EXISTS (
        SELECT 1 FROM activity.community_members
        WHERE community_members.community_id = p_community_id
        AND user_id = p_updating_user_id
        AND role = 'organizer'
        AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'INSUFFICIENT_PERMISSIONS';
    END IF;

    -- 3. Update community
    UPDATE activity.communities
    SET
        name = COALESCE(p_name, name),
        description = COALESCE(p_description, description),
        cover_image_url = COALESCE(p_cover_image_url, cover_image_url),
        icon_url = COALESCE(p_icon_url, icon_url),
        max_members = COALESCE(p_max_members, max_members),
        updated_at = NOW()
    WHERE communities.community_id = p_community_id
    RETURNING communities.updated_at INTO v_updated_at;

    -- 4. Handle tags if provided
    IF p_tags IS NOT NULL THEN
        DELETE FROM activity.community_tags WHERE community_tags.community_id = p_community_id;
        IF array_length(p_tags, 1) > 0 THEN
            INSERT INTO activity.community_tags (community_id, tag)
            SELECT p_community_id, unnest(p_tags);
        END IF;
    END IF;

    -- 5. Return updated details
    RETURN QUERY
    SELECT p_community_id, v_updated_at;
END;
$$;


ALTER FUNCTION activity.sp_community_update(p_community_id uuid, p_updating_user_id uuid, p_name character varying, p_description text, p_cover_image_url character varying, p_icon_url character varying, p_max_members integer, p_tags text[]) OWNER TO postgres;

--
-- Name: sp_confirm_attendance(uuid, uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_confirm_attendance(p_activity_id uuid, p_confirmed_user_id uuid, p_confirmer_user_id uuid) RETURNS TABLE(success boolean, confirmation_id uuid, new_verification_count integer, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_confirmed_participant RECORD;
    v_confirmer_participant RECORD;
    v_new_confirmation_id UUID;
    v_verification_count INT;
    v_already_confirmed BOOLEAN;
BEGIN
    RAISE NOTICE 'sp_confirm_attendance called: activity_id=%, confirmed_user_id=%, confirmer_user_id=%',
        p_activity_id, p_confirmed_user_id, p_confirmer_user_id;

    -- Check not confirming self
    IF p_confirmed_user_id = p_confirmer_user_id THEN
        RAISE NOTICE 'Cannot confirm own attendance';
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::INT,
            'SELF_CONFIRMATION'::VARCHAR(50), 'Cannot confirm your own attendance'::TEXT;
        RETURN;
    END IF;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::INT,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check activity has completed
    IF v_activity.scheduled_at > NOW() THEN
        RAISE NOTICE 'Activity has not completed: scheduled_at=%', v_activity.scheduled_at;
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::INT,
            'ACTIVITY_NOT_COMPLETED'::VARCHAR(50), 'Activity has not yet completed'::TEXT;
        RETURN;
    END IF;

    -- Check confirmer attended
    SELECT * INTO v_confirmer_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_confirmer_user_id;

    IF NOT FOUND OR v_confirmer_participant.attendance_status != 'attended' THEN
        RAISE NOTICE 'Confirmer did not attend: status=%',
            COALESCE(v_confirmer_participant.attendance_status::TEXT, 'none');
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::INT,
            'CONFIRMER_NOT_ATTENDED'::VARCHAR(50), 'You must have attended status to confirm others'::TEXT;
        RETURN;
    END IF;

    -- Check confirmed user attended
    SELECT * INTO v_confirmed_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_confirmed_user_id;

    IF NOT FOUND OR v_confirmed_participant.attendance_status != 'attended' THEN
        RAISE NOTICE 'Confirmed user did not attend: status=%',
            COALESCE(v_confirmed_participant.attendance_status::TEXT, 'none');
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::INT,
            'CONFIRMED_NOT_ATTENDED'::VARCHAR(50), 'User does not have attended status'::TEXT;
        RETURN;
    END IF;

    -- Check if already confirmed
    SELECT EXISTS(
        SELECT 1 FROM activity.attendance_confirmations
        WHERE activity_id = p_activity_id
          AND confirmed_user_id = p_confirmed_user_id
          AND confirmer_user_id = p_confirmer_user_id
    ) INTO v_already_confirmed;

    IF v_already_confirmed THEN
        RAISE NOTICE 'Already confirmed this user';
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::INT,
            'ALREADY_CONFIRMED'::VARCHAR(50), 'You already confirmed this user for this activity'::TEXT;
        RETURN;
    END IF;

    -- Insert confirmation
    RAISE NOTICE 'Creating attendance confirmation';
    INSERT INTO activity.attendance_confirmations (activity_id, confirmed_user_id, confirmer_user_id)
    VALUES (p_activity_id, p_confirmed_user_id, p_confirmer_user_id)
    RETURNING confirmation_id INTO v_new_confirmation_id;

    -- Update user's verification count
    UPDATE activity.users
    SET verification_count = verification_count + 1
    WHERE user_id = p_confirmed_user_id
    RETURNING verification_count INTO v_verification_count;

    RAISE NOTICE 'Attendance confirmed: confirmation_id=%, new_verification_count=%',
        v_new_confirmation_id, v_verification_count;

    RETURN QUERY SELECT TRUE, v_new_confirmation_id, v_verification_count,
        NULL::VARCHAR(50), NULL::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_confirm_attendance(p_activity_id uuid, p_confirmed_user_id uuid, p_confirmer_user_id uuid) OWNER TO postgres;

--
-- Name: FUNCTION sp_confirm_attendance(p_activity_id uuid, p_confirmed_user_id uuid, p_confirmer_user_id uuid); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_confirm_attendance(p_activity_id uuid, p_confirmed_user_id uuid, p_confirmer_user_id uuid) IS 'Peer verification of attendance with verification count increment';


--
-- Name: sp_create_notification(uuid, uuid, character varying, character varying, uuid, character varying, text, jsonb); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_create_notification(p_user_id uuid, p_actor_user_id uuid, p_notification_type character varying, p_target_type character varying, p_target_id uuid, p_title character varying, p_message text DEFAULT NULL::text, p_payload jsonb DEFAULT NULL::jsonb) RETURNS TABLE(notification_id uuid, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_notification_id UUID;
    v_created_at TIMESTAMP WITH TIME ZONE;
    v_prefs_exist BOOLEAN;
    v_enabled_types JSONB;
    v_in_app_enabled BOOLEAN;
BEGIN
    -- Check user notification preferences
    SELECT
        in_app_enabled,
        enabled_types
    INTO
        v_in_app_enabled,
        v_enabled_types
    FROM activity.notification_preferences
    WHERE user_id = p_user_id;

    -- If no preferences exist, create defaults
    IF NOT FOUND THEN
        INSERT INTO activity.notification_preferences (user_id)
        VALUES (p_user_id)
        RETURNING in_app_enabled, enabled_types
        INTO v_in_app_enabled, v_enabled_types;
    END IF;

    -- Check if notification type is enabled
    IF v_in_app_enabled = FALSE OR NOT (v_enabled_types ? p_notification_type) THEN
        -- Return empty result (notification skipped)
        RETURN;
    END IF;

    -- Create notification
    INSERT INTO activity.notifications (
        user_id,
        actor_user_id,
        notification_type,
        target_type,
        target_id,
        title,
        message,
        payload
    ) VALUES (
        p_user_id,
        p_actor_user_id,
        p_notification_type::activity.notification_type,
        p_target_type,
        p_target_id,
        p_title,
        p_message,
        p_payload
    )
    RETURNING notifications.notification_id, notifications.created_at
    INTO v_notification_id, v_created_at;

    RETURN QUERY SELECT v_notification_id, v_created_at;
END;
$$;


ALTER FUNCTION activity.sp_create_notification(p_user_id uuid, p_actor_user_id uuid, p_notification_type character varying, p_target_type character varying, p_target_id uuid, p_title character varying, p_message text, p_payload jsonb) OWNER TO postgres;

--
-- Name: sp_create_organization(text, text, text, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_create_organization(p_name text, p_slug text, p_description text, p_creator_user_id uuid) RETURNS TABLE(id uuid, name text, slug text, description text, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Insert organization
    INSERT INTO activity.organizations (name, slug, description)
    VALUES (p_name, p_slug, p_description)
    RETURNING activity.organizations.id INTO v_org_id;

    -- Add creator as owner
    INSERT INTO activity.organization_members (user_id, organization_id, role, invited_by)
    VALUES (p_creator_user_id, v_org_id, 'owner', NULL);

    -- Return created organization
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.description,
        o.created_at
    FROM activity.organizations o
    WHERE o.id = v_org_id;
END;
$$;


ALTER FUNCTION activity.sp_create_organization(p_name text, p_slug text, p_description text, p_creator_user_id uuid) OWNER TO postgres;

--
-- Name: sp_create_organization(uuid, text, text, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_create_organization(p_owner_user_id uuid, p_name text, p_slug text, p_description text DEFAULT NULL::text) RETURNS TABLE(id uuid, name text, slug text, description text, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_org_id uuid;
BEGIN
    -- Insert new organization
    INSERT INTO activity.organizations (name, slug, description)
    VALUES (p_name, p_slug, p_description)
    RETURNING organization_id INTO v_org_id;

    -- Add owner as member with 'owner' role
    INSERT INTO activity.organization_members (organization_id, user_id, role)
    VALUES (v_org_id, p_owner_user_id, 'owner');

    -- Return organization details
    RETURN QUERY
    SELECT
        o.organization_id as id,
        o.name::text,
        o.slug::text,
        o.description::text,
        o.created_at
    FROM activity.organizations o
    WHERE o.organization_id = v_org_id;
END;
$$;


ALTER FUNCTION activity.sp_create_organization(p_owner_user_id uuid, p_name text, p_slug text, p_description text) OWNER TO postgres;

--
-- Name: sp_create_user(character varying, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_create_user(p_email character varying, p_hashed_password character varying) RETURNS TABLE(id uuid, email character varying, hashed_password character varying, is_verified boolean, is_active boolean, created_at timestamp with time zone, verified_at timestamp with time zone, last_login_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_username VARCHAR;
    v_user_id UUID;
    v_email VARCHAR;
    v_password_hash VARCHAR;
    v_is_verified BOOLEAN;
    v_status activity.user_status;
    v_created_at TIMESTAMPTZ;
    v_last_login TIMESTAMPTZ;
BEGIN
    v_username := split_part(p_email, '@', 1);
    WHILE EXISTS (SELECT 1 FROM activity.users WHERE username = v_username) LOOP
        v_username := split_part(p_email, '@', 1) || floor(random() * 10000)::text;
    END LOOP;

    INSERT INTO activity.users (email, username, password_hash, is_verified, status)
    VALUES (LOWER(p_email), v_username, p_hashed_password, FALSE, 'active')
    RETURNING user_id, users.email, users.password_hash, users.is_verified,
              users.status, users.created_at, users.last_login_at
    INTO v_user_id, v_email, v_password_hash, v_is_verified, v_status, v_created_at, v_last_login;
    
    RETURN QUERY SELECT v_user_id, v_email, v_password_hash, v_is_verified,
                        (v_status = 'active'), v_created_at, NULL::TIMESTAMPTZ, v_last_login;
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Email already exists: %', p_email USING ERRCODE = '23505';
END;
$$;


ALTER FUNCTION activity.sp_create_user(p_email character varying, p_hashed_password character varying) OWNER TO postgres;

--
-- Name: sp_deactivate_user(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_deactivate_user(p_user_id uuid) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users SET status = 'deleted' WHERE user_id = p_user_id;
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;


ALTER FUNCTION activity.sp_deactivate_user(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_decline_invitation(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_decline_invitation(p_invitation_id uuid, p_user_id uuid) RETURNS TABLE(success boolean, activity_id uuid, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_invitation RECORD;
BEGIN
    RAISE NOTICE 'sp_decline_invitation called: invitation_id=%, user_id=%', p_invitation_id, p_user_id;

    -- Get invitation details
    SELECT * INTO v_invitation
    FROM activity.activity_invitations
    WHERE invitation_id = p_invitation_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Invitation not found: %', p_invitation_id;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'INVITATION_NOT_FOUND'::VARCHAR(50), 'Invitation does not exist'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'Invitation found: activity_id=%, user_id=%, status=%',
        v_invitation.activity_id, v_invitation.user_id, v_invitation.status;

    -- Check invitation is for this user
    IF v_invitation.user_id != p_user_id THEN
        RAISE NOTICE 'Invitation is for different user: expected=%, actual=%',
            v_invitation.user_id, p_user_id;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'NOT_YOUR_INVITATION'::VARCHAR(50), 'This invitation is not for you'::TEXT;
        RETURN;
    END IF;

    -- Check invitation status
    IF v_invitation.status != 'pending' THEN
        RAISE NOTICE 'Invitation already responded: status=%', v_invitation.status;
        RETURN QUERY SELECT FALSE, NULL::UUID,
            'ALREADY_RESPONDED'::VARCHAR(50), 'Invitation already responded to'::TEXT;
        RETURN;
    END IF;

    -- Decline invitation
    RAISE NOTICE 'Declining invitation';
    UPDATE activity.activity_invitations
    SET status = 'declined', responded_at = NOW()
    WHERE invitation_id = p_invitation_id;

    RAISE NOTICE 'Invitation declined successfully';

    RETURN QUERY SELECT TRUE, v_invitation.activity_id,
        NULL::VARCHAR(50), NULL::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_decline_invitation(p_invitation_id uuid, p_user_id uuid) OWNER TO postgres;

--
-- Name: FUNCTION sp_decline_invitation(p_invitation_id uuid, p_user_id uuid); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_decline_invitation(p_invitation_id uuid, p_user_id uuid) IS 'Decline invitation';


--
-- Name: sp_delete_notification(uuid, uuid, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_delete_notification(p_user_id uuid, p_notification_id uuid, p_permanent boolean DEFAULT false) RETURNS TABLE(success boolean, message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    -- Check if notification exists and belongs to user
    SELECT EXISTS(
        SELECT 1 FROM activity.notifications
        WHERE notification_id = p_notification_id
            AND user_id = p_user_id
    ) INTO v_exists;

    IF NOT v_exists THEN
        RETURN QUERY SELECT FALSE, 'Notification not found'::TEXT;
        RETURN;
    END IF;

    -- Permanent delete
    IF p_permanent THEN
        DELETE FROM activity.notifications
        WHERE notification_id = p_notification_id
            AND user_id = p_user_id;

        RETURN QUERY SELECT TRUE, 'Notification permanently deleted'::TEXT;

    -- Archive (soft delete)
    ELSE
        UPDATE activity.notifications
        SET status = 'archived'::activity.notification_status
        WHERE notification_id = p_notification_id
            AND user_id = p_user_id;

        RETURN QUERY SELECT TRUE, 'Notification archived'::TEXT;
    END IF;
END;
$$;


ALTER FUNCTION activity.sp_delete_notification(p_user_id uuid, p_notification_id uuid, p_permanent boolean) OWNER TO postgres;

--
-- Name: sp_delete_user_account(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_delete_user_account(p_user_id uuid) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Anonymize user data
    UPDATE activity.users
    SET
        email = 'deleted_' || p_user_id::TEXT || '@deleted.local',
        username = 'deleted_' || p_user_id::TEXT,
        first_name = NULL,
        last_name = NULL,
        profile_description = NULL,
        main_photo_url = NULL,
        profile_photos_extra = '[]'::JSONB,
        date_of_birth = NULL,
        status = 'banned',
        updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE;
        RETURN;
    END IF;

    -- Delete related data
    DELETE FROM activity.user_interests WHERE user_id = p_user_id;
    DELETE FROM activity.user_settings WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE;
END;
$$;


ALTER FUNCTION activity.sp_delete_user_account(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_demote_participant(uuid, uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_demote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid) RETURNS TABLE(success boolean, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_participant RECORD;
BEGIN
    RAISE NOTICE 'sp_demote_participant called: activity_id=%, organizer_user_id=%, target_user_id=%',
        p_activity_id, p_organizer_user_id, p_target_user_id;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check requesting user is organizer
    IF v_activity.organizer_user_id != p_organizer_user_id THEN
        RAISE NOTICE 'User is not organizer: user_id=%, actual_organizer=%',
            p_organizer_user_id, v_activity.organizer_user_id;
        RETURN QUERY SELECT FALSE,
            'NOT_ORGANIZER'::VARCHAR(50), 'Only organizer can demote participants'::TEXT;
        RETURN;
    END IF;

    -- Get target participant
    SELECT * INTO v_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_target_user_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Target user is not a participant';
        RETURN QUERY SELECT FALSE,
            'NOT_CO_ORGANIZER'::VARCHAR(50), 'User is not a co-organizer'::TEXT;
        RETURN;
    END IF;

    -- Check target is a co-organizer
    IF v_participant.role != 'co_organizer' THEN
        RAISE NOTICE 'Target user is not co-organizer: role=%', v_participant.role;
        RETURN QUERY SELECT FALSE,
            'NOT_CO_ORGANIZER'::VARCHAR(50), 'User is not a co-organizer'::TEXT;
        RETURN;
    END IF;

    -- Demote to member
    RAISE NOTICE 'Demoting user to member';
    UPDATE activity.participants
    SET role = 'member'
    WHERE activity_id = p_activity_id AND user_id = p_target_user_id;

    RAISE NOTICE 'User demoted successfully';

    RETURN QUERY SELECT TRUE,
        NULL::VARCHAR(50), NULL::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_demote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid) OWNER TO postgres;

--
-- Name: FUNCTION sp_demote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_demote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid) IS 'Demote co-organizer to member (organizer only)';


--
-- Name: sp_get_notification_by_id(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_notification_by_id(p_user_id uuid, p_notification_id uuid) RETURNS TABLE(notification_id uuid, user_id uuid, actor_user_id uuid, actor_username character varying, actor_first_name character varying, actor_last_name character varying, actor_main_photo_url character varying, notification_type character varying, target_type character varying, target_id uuid, title character varying, message text, status character varying, created_at timestamp with time zone, read_at timestamp with time zone, payload jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.notification_id,
        n.user_id,
        n.actor_user_id,
        u.username,
        u.first_name,
        u.last_name,
        u.main_photo_url,
        n.notification_type::VARCHAR,
        n.target_type,
        n.target_id,
        n.title,
        n.message,
        n.status::VARCHAR,
        n.created_at,
        n.read_at,
        n.payload
    FROM activity.notifications n
    LEFT JOIN activity.users u ON n.actor_user_id = u.user_id
    WHERE n.notification_id = p_notification_id
        AND n.user_id = p_user_id;
END;
$$;


ALTER FUNCTION activity.sp_get_notification_by_id(p_user_id uuid, p_notification_id uuid) OWNER TO postgres;

--
-- Name: sp_get_notification_settings(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_notification_settings(p_user_id uuid) RETURNS TABLE(email_enabled boolean, push_enabled boolean, in_app_enabled boolean, enabled_types jsonb, quiet_hours_start time without time zone, quiet_hours_end time without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Ensure preferences exist, create if not
    INSERT INTO activity.notification_preferences (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING;

    RETURN QUERY
    SELECT
        np.email_enabled,
        np.push_enabled,
        np.in_app_enabled,
        np.enabled_types,
        np.quiet_hours_start,
        np.quiet_hours_end
    FROM activity.notification_preferences np
    WHERE np.user_id = p_user_id;
END;
$$;


ALTER FUNCTION activity.sp_get_notification_settings(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_get_organization_by_id(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_organization_by_id(p_org_id uuid) RETURNS TABLE(id uuid, name text, slug text, description text, created_at timestamp with time zone, updated_at timestamp with time zone, member_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.description,
        o.created_at,
        o.updated_at,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.id) as member_count
    FROM activity.organizations o
    WHERE o.id = p_org_id
      AND o.deleted_at IS NULL;
END;
$$;


ALTER FUNCTION activity.sp_get_organization_by_id(p_org_id uuid) OWNER TO postgres;

--
-- Name: sp_get_organization_members(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_organization_members(p_organization_id uuid) RETURNS TABLE(user_id uuid, email text, role text, joined_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id,
        u.email::text,
        om.role::text,
        om.joined_at
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.user_id
    WHERE om.organization_id = p_organization_id
    ORDER BY om.joined_at ASC;
END;
$$;


ALTER FUNCTION activity.sp_get_organization_members(p_organization_id uuid) OWNER TO postgres;

--
-- Name: sp_get_organization_members(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_organization_members(p_org_id uuid, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0) RETURNS TABLE(user_id uuid, email text, role text, joined_at timestamp with time zone, invited_by_email text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        om.user_id,
        u.email,
        om.role,
        om.joined_at,
        inviter.email as invited_by_email
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.id
    LEFT JOIN activity.users inviter ON om.invited_by = inviter.id
    WHERE om.organization_id = p_org_id
    ORDER BY om.joined_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_get_organization_members(p_org_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_get_pending_photo_moderations(integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_pending_photo_moderations(p_limit integer DEFAULT 50, p_offset integer DEFAULT 0) RETURNS TABLE(user_id uuid, username character varying, email character varying, main_photo_url character varying, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id,
        u.username,
        u.email,
        u.main_photo_url,
        u.created_at
    FROM activity.users u
    WHERE u.main_photo_moderation_status = 'pending'
    ORDER BY u.created_at ASC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_get_pending_photo_moderations(p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_get_pending_verifications(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_pending_verifications(p_user_id uuid, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(activity_id uuid, title character varying, scheduled_at timestamp with time zone, participants_to_confirm jsonb, total_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE NOTICE 'sp_get_pending_verifications called: user_id=%, limit=%, offset=%',
        p_user_id, p_limit, p_offset;

    RETURN QUERY
    WITH user_attended_activities AS (
        SELECT a.activity_id, a.title, a.scheduled_at
        FROM activity.participants p
        JOIN activity.activities a ON p.activity_id = a.activity_id
        WHERE p.user_id = p_user_id
            AND p.attendance_status = 'attended'
            AND a.scheduled_at <= NOW()
    )
    SELECT
        uaa.activity_id,
        uaa.title,
        uaa.scheduled_at,
        -- Get participants that user hasn't confirmed yet
        (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'user_id', u.user_id,
                    'username', u.username,
                    'first_name', u.first_name,
                    'profile_photo_url', u.main_photo_url
                )
            )
            FROM activity.participants p2
            JOIN activity.users u ON p2.user_id = u.user_id
            WHERE p2.activity_id = uaa.activity_id
                AND p2.attendance_status = 'attended'
                AND p2.user_id != p_user_id
                AND NOT EXISTS (
                    SELECT 1 FROM activity.attendance_confirmations
                    WHERE activity_id = uaa.activity_id
                        AND confirmed_user_id = p2.user_id
                        AND confirmer_user_id = p_user_id
                )
        ) AS participants_to_confirm,
        COUNT(*) OVER() AS total_count
    FROM user_attended_activities uaa
    WHERE (
        SELECT jsonb_agg(
            jsonb_build_object(
                'user_id', u.user_id,
                'username', u.username,
                'first_name', u.first_name,
                'profile_photo_url', u.main_photo_url
            )
        )
        FROM activity.participants p2
        JOIN activity.users u ON p2.user_id = u.user_id
        WHERE p2.activity_id = uaa.activity_id
            AND p2.attendance_status = 'attended'
            AND p2.user_id != p_user_id
            AND NOT EXISTS (
                SELECT 1 FROM activity.attendance_confirmations
                WHERE activity_id = uaa.activity_id
                    AND confirmed_user_id = p2.user_id
                    AND confirmer_user_id = p_user_id
            )
    ) IS NOT NULL  -- Only activities with unconfirmed participants
    ORDER BY uaa.scheduled_at DESC
    LIMIT p_limit OFFSET p_offset;

    RAISE NOTICE 'Pending verifications returned';
END;
$$;


ALTER FUNCTION activity.sp_get_pending_verifications(p_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_get_pending_verifications(p_user_id uuid, p_limit integer, p_offset integer); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_get_pending_verifications(p_user_id uuid, p_limit integer, p_offset integer) IS 'Get activities with unconfirmed attendances for peer verification';


--
-- Name: sp_get_received_invitations(uuid, activity.invitation_status, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_received_invitations(p_user_id uuid, p_status activity.invitation_status DEFAULT NULL::activity.invitation_status, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(invitation_id uuid, activity_id uuid, activity_title character varying, activity_scheduled_at timestamp with time zone, invited_by_user_id uuid, invited_by_username character varying, status activity.invitation_status, message text, invited_at timestamp with time zone, expires_at timestamp with time zone, responded_at timestamp with time zone, total_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE NOTICE 'sp_get_received_invitations called: user_id=%, status=%, limit=%, offset=%',
        p_user_id, p_status, p_limit, p_offset;

    RETURN QUERY
    SELECT
        i.invitation_id,
        a.activity_id,
        a.title AS activity_title,
        a.scheduled_at AS activity_scheduled_at,
        i.invited_by_user_id,
        u.username AS invited_by_username,
        CASE
            WHEN i.status = 'pending' AND i.expires_at IS NOT NULL AND i.expires_at <= NOW()
            THEN 'expired'::activity.invitation_status
            ELSE i.status
        END AS status,
        i.message,
        i.invited_at,
        i.expires_at,
        i.responded_at,
        COUNT(*) OVER() AS total_count
    FROM activity.activity_invitations i
    JOIN activity.activities a ON i.activity_id = a.activity_id
    JOIN activity.users u ON i.invited_by_user_id = u.user_id
    WHERE i.user_id = p_user_id
        AND (p_status IS NULL OR i.status = p_status)
    ORDER BY i.invited_at DESC
    LIMIT p_limit OFFSET p_offset;

    RAISE NOTICE 'Received invitations returned';
END;
$$;


ALTER FUNCTION activity.sp_get_received_invitations(p_user_id uuid, p_status activity.invitation_status, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_get_received_invitations(p_user_id uuid, p_status activity.invitation_status, p_limit integer, p_offset integer); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_get_received_invitations(p_user_id uuid, p_status activity.invitation_status, p_limit integer, p_offset integer) IS 'Get received invitations with expired status handling';


--
-- Name: sp_get_sent_invitations(uuid, uuid, activity.invitation_status, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_sent_invitations(p_inviting_user_id uuid, p_activity_id uuid DEFAULT NULL::uuid, p_status activity.invitation_status DEFAULT NULL::activity.invitation_status, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(invitation_id uuid, activity_id uuid, activity_title character varying, user_id uuid, username character varying, status activity.invitation_status, invited_at timestamp with time zone, expires_at timestamp with time zone, responded_at timestamp with time zone, total_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE NOTICE 'sp_get_sent_invitations called: inviting_user_id=%, activity_id=%, status=%, limit=%, offset=%',
        p_inviting_user_id, p_activity_id, p_status, p_limit, p_offset;

    RETURN QUERY
    SELECT
        i.invitation_id,
        a.activity_id,
        a.title AS activity_title,
        i.user_id,
        u.username,
        CASE
            WHEN i.status = 'pending' AND i.expires_at IS NOT NULL AND i.expires_at <= NOW()
            THEN 'expired'::activity.invitation_status
            ELSE i.status
        END AS status,
        i.invited_at,
        i.expires_at,
        i.responded_at,
        COUNT(*) OVER() AS total_count
    FROM activity.activity_invitations i
    JOIN activity.activities a ON i.activity_id = a.activity_id
    JOIN activity.users u ON i.user_id = u.user_id
    WHERE i.invited_by_user_id = p_inviting_user_id
        AND (p_activity_id IS NULL OR i.activity_id = p_activity_id)
        AND (p_status IS NULL OR i.status = p_status)
    ORDER BY i.invited_at DESC
    LIMIT p_limit OFFSET p_offset;

    RAISE NOTICE 'Sent invitations returned';
END;
$$;


ALTER FUNCTION activity.sp_get_sent_invitations(p_inviting_user_id uuid, p_activity_id uuid, p_status activity.invitation_status, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_get_sent_invitations(p_inviting_user_id uuid, p_activity_id uuid, p_status activity.invitation_status, p_limit integer, p_offset integer); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_get_sent_invitations(p_inviting_user_id uuid, p_activity_id uuid, p_status activity.invitation_status, p_limit integer, p_offset integer) IS 'Get sent invitations with expired status handling';


--
-- Name: sp_get_unread_count(uuid, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_unread_count(p_user_id uuid, p_include_premium_only boolean DEFAULT false) RETURNS TABLE(total_unread bigint, activity_invite_count bigint, activity_reminder_count bigint, activity_update_count bigint, community_invite_count bigint, new_member_count bigint, new_post_count bigint, comment_count bigint, reaction_count bigint, mention_count bigint, profile_view_count bigint, new_favorite_count bigint, system_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_unread,
        COUNT(*) FILTER (WHERE notification_type = 'activity_invite')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'activity_reminder')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'activity_update')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'community_invite')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'new_member')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'new_post')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'comment')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'reaction')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'mention')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'profile_view')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'new_favorite')::BIGINT,
        COUNT(*) FILTER (WHERE notification_type = 'system')::BIGINT
    FROM activity.notifications
    WHERE user_id = p_user_id
        AND status = 'unread'::activity.notification_status
        AND (
            p_include_premium_only = TRUE
            OR notification_type::VARCHAR NOT IN ('profile_view', 'new_favorite')
        );
END;
$$;


ALTER FUNCTION activity.sp_get_unread_count(p_user_id uuid, p_include_premium_only boolean) OWNER TO postgres;

--
-- Name: sp_get_user_activities(uuid, uuid, character varying, activity.participation_status, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_activities(p_target_user_id uuid, p_requesting_user_id uuid, p_type character varying DEFAULT NULL::character varying, p_status activity.participation_status DEFAULT NULL::activity.participation_status, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(activity_id uuid, title character varying, scheduled_at timestamp with time zone, location_name character varying, city character varying, organizer_user_id uuid, organizer_username character varying, current_participants_count integer, max_participants integer, activity_type activity.activity_type, role activity.participant_role, participation_status activity.participation_status, attendance_status activity.attendance_status, joined_at timestamp with time zone, total_count bigint)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_is_blocked BOOLEAN;
BEGIN
    RAISE NOTICE 'sp_get_user_activities called: target_user_id=%, requesting_user_id=%, type=%, status=%, limit=%, offset=%',
        p_target_user_id, p_requesting_user_id, p_type, p_status, p_limit, p_offset;

    -- Privacy check: if requesting different user, check blocking
    IF p_requesting_user_id != p_target_user_id THEN
        SELECT EXISTS(
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = p_requesting_user_id AND blocked_user_id = p_target_user_id)
               OR (blocker_user_id = p_target_user_id AND blocked_user_id = p_requesting_user_id)
        ) INTO v_is_blocked;

        IF v_is_blocked THEN
            RAISE NOTICE 'User is blocked - returning empty result';
            RETURN;
        END IF;
    END IF;

    RAISE NOTICE 'Privacy check passed, querying activities';

    -- Return activities
    RETURN QUERY
    SELECT
        a.activity_id,
        a.title,
        a.scheduled_at,
        a.location_name,
        a.city,
        a.organizer_user_id,
        u.username AS organizer_username,
        a.current_participants_count,
        a.max_participants,
        a.activity_type,
        p.role,
        p.participation_status,
        p.attendance_status,
        p.joined_at,
        COUNT(*) OVER() AS total_count
    FROM activity.participants p
    JOIN activity.activities a ON p.activity_id = a.activity_id
    JOIN activity.users u ON a.organizer_user_id = u.user_id
    WHERE p.user_id = p_target_user_id
        AND a.status != 'draft'  -- Hide drafts
        -- Type filters
        AND (p_type IS NULL
            OR (p_type = 'upcoming' AND a.scheduled_at > NOW())
            OR (p_type = 'past' AND a.scheduled_at <= NOW())
            OR (p_type = 'organized' AND a.organizer_user_id = p_target_user_id)
            OR (p_type = 'attended' AND p.attendance_status = 'attended')
        )
        -- Status filter
        AND (p_status IS NULL OR p.participation_status = p_status)
    ORDER BY a.scheduled_at DESC
    LIMIT p_limit OFFSET p_offset;

    RAISE NOTICE 'User activities returned';
END;
$$;


ALTER FUNCTION activity.sp_get_user_activities(p_target_user_id uuid, p_requesting_user_id uuid, p_type character varying, p_status activity.participation_status, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_get_user_activities(p_target_user_id uuid, p_requesting_user_id uuid, p_type character varying, p_status activity.participation_status, p_limit integer, p_offset integer); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_get_user_activities(p_target_user_id uuid, p_requesting_user_id uuid, p_type character varying, p_status activity.participation_status, p_limit integer, p_offset integer) IS 'Get user activity history with privacy and blocking checks';


--
-- Name: sp_get_user_by_email(character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_by_email(p_email character varying) RETURNS TABLE(id uuid, email character varying, hashed_password character varying, is_verified boolean, is_active boolean, created_at timestamp with time zone, verified_at timestamp with time zone, last_login_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT u.user_id, u.email, u.password_hash, u.is_verified,
           (u.status = 'active'::activity.user_status), u.created_at, NULL::TIMESTAMPTZ, u.last_login_at
    FROM activity.users u
    WHERE u.email = LOWER(p_email);
END;
$$;


ALTER FUNCTION activity.sp_get_user_by_email(p_email character varying) OWNER TO postgres;

--
-- Name: sp_get_user_by_id(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_by_id(p_user_id uuid) RETURNS TABLE(id uuid, email character varying, hashed_password character varying, is_verified boolean, is_active boolean, created_at timestamp with time zone, verified_at timestamp with time zone, last_login_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT u.user_id, u.email, u.password_hash, u.is_verified,
           (u.status = 'active'::activity.user_status), u.created_at, NULL::TIMESTAMPTZ, u.last_login_at
    FROM activity.users u
    WHERE u.user_id = p_user_id;
END;
$$;


ALTER FUNCTION activity.sp_get_user_by_id(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_get_user_notifications(uuid, character varying, character varying, integer, integer, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_notifications(p_user_id uuid, p_status character varying DEFAULT NULL::character varying, p_notification_type character varying DEFAULT NULL::character varying, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0, p_include_premium_only boolean DEFAULT false) RETURNS TABLE(notification_id uuid, user_id uuid, actor_user_id uuid, actor_username character varying, actor_first_name character varying, actor_last_name character varying, actor_main_photo_url character varying, notification_type character varying, target_type character varying, target_id uuid, title character varying, message text, status character varying, created_at timestamp with time zone, read_at timestamp with time zone, payload jsonb, total_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH filtered_notifications AS (
        SELECT
            n.notification_id,
            n.user_id,
            n.actor_user_id,
            n.notification_type::VARCHAR,
            n.target_type,
            n.target_id,
            n.title,
            n.message,
            n.status::VARCHAR,
            n.created_at,
            n.read_at,
            n.payload,
            u.username,
            u.first_name,
            u.last_name,
            u.main_photo_url
        FROM activity.notifications n
        LEFT JOIN activity.users u ON n.actor_user_id = u.user_id
        WHERE n.user_id = p_user_id
            AND (p_status IS NULL OR n.status::VARCHAR = p_status)
            AND (p_notification_type IS NULL OR n.notification_type::VARCHAR = p_notification_type)
            AND (
                p_include_premium_only = TRUE
                OR n.notification_type::VARCHAR NOT IN ('profile_view', 'new_favorite')
            )
        ORDER BY n.created_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ),
    total AS (
        SELECT COUNT(*) as cnt
        FROM activity.notifications n
        WHERE n.user_id = p_user_id
            AND (p_status IS NULL OR n.status::VARCHAR = p_status)
            AND (p_notification_type IS NULL OR n.notification_type::VARCHAR = p_notification_type)
            AND (
                p_include_premium_only = TRUE
                OR n.notification_type::VARCHAR NOT IN ('profile_view', 'new_favorite')
            )
    )
    SELECT
        fn.notification_id,
        fn.user_id,
        fn.actor_user_id,
        fn.username,
        fn.first_name,
        fn.last_name,
        fn.main_photo_url,
        fn.notification_type,
        fn.target_type,
        fn.target_id,
        fn.title,
        fn.message,
        fn.status,
        fn.created_at,
        fn.read_at,
        fn.payload,
        t.cnt as total_count
    FROM filtered_notifications fn
    CROSS JOIN total t;
END;
$$;


ALTER FUNCTION activity.sp_get_user_notifications(p_user_id uuid, p_status character varying, p_notification_type character varying, p_limit integer, p_offset integer, p_include_premium_only boolean) OWNER TO postgres;

--
-- Name: sp_get_user_org_role(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_org_role(p_user_id uuid, p_org_id uuid) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_role TEXT;
BEGIN
    SELECT role INTO v_role
    FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    RETURN v_role;
END;
$$;


ALTER FUNCTION activity.sp_get_user_org_role(p_user_id uuid, p_org_id uuid) OWNER TO postgres;

--
-- Name: sp_get_user_organizations(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_organizations(p_user_id uuid) RETURNS TABLE(id uuid, name text, slug text, description text, role text, member_count bigint, joined_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.organization_id as id,
        o.name::text,
        o.slug::text,
        o.description::text,
        om.role::text,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.organization_id) as member_count,
        om.joined_at
    FROM activity.organizations o
    INNER JOIN activity.organization_members om ON o.organization_id = om.organization_id
    WHERE om.user_id = p_user_id
    ORDER BY om.joined_at DESC;
END;
$$;


ALTER FUNCTION activity.sp_get_user_organizations(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_get_user_profile(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_profile(p_user_id uuid, p_requesting_user_id uuid) RETURNS TABLE(user_id uuid, email character varying, username character varying, first_name character varying, last_name character varying, profile_description text, main_photo_url character varying, main_photo_moderation_status activity.photo_moderation_status, profile_photos_extra jsonb, date_of_birth date, gender character varying, subscription_level activity.subscription_level, subscription_expires_at timestamp with time zone, is_captain boolean, captain_since timestamp with time zone, is_verified boolean, verification_count integer, no_show_count integer, activities_created_count integer, activities_attended_count integer, created_at timestamp with time zone, last_seen_at timestamp with time zone, interests jsonb, settings jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if requesting user has blocked the target user
    IF EXISTS (
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_requesting_user_id
        AND blocked_user_id = p_user_id
    ) THEN
        RETURN;  -- Return NULL (blocked)
    END IF;

    -- Check if target user has blocked the requesting user
    IF EXISTS (
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_user_id
        AND blocked_user_id = p_requesting_user_id
    ) THEN
        RETURN;  -- Return NULL (blocking)
    END IF;

    -- Return complete profile with aggregated interests and settings
    RETURN QUERY
    SELECT
        u.user_id,
        u.email,
        u.username,
        u.first_name,
        u.last_name,
        u.profile_description,
        u.main_photo_url,
        u.main_photo_moderation_status,
        u.profile_photos_extra,
        u.date_of_birth,
        u.gender,
        u.subscription_level,
        u.subscription_expires_at,
        u.is_captain,
        u.captain_since,
        u.is_verified,
        u.verification_count,
        u.no_show_count,
        u.activities_created_count,
        u.activities_attended_count,
        u.created_at,
        u.last_seen_at,
        COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object('tag', ui.interest_tag, 'weight', ui.weight))
                FROM activity.user_interests ui
                WHERE ui.user_id = p_user_id
            ),
            '[]'::jsonb
        ) AS interests,
        COALESCE(
            (
                SELECT to_jsonb(us.*) - 'user_id' - 'created_at' - 'updated_at' - 'payload' - 'hash_value'
                FROM activity.user_settings us
                WHERE us.user_id = p_user_id
            ),
            '{}'::jsonb
        ) AS settings
    FROM activity.users u
    WHERE u.user_id = p_user_id
    AND u.status != 'banned';
END;
$$;


ALTER FUNCTION activity.sp_get_user_profile(p_user_id uuid, p_requesting_user_id uuid) OWNER TO postgres;

--
-- Name: sp_get_user_role_in_organization(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_role_in_organization(p_user_id uuid, p_organization_id uuid) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_role text;
BEGIN
    SELECT role INTO v_role
    FROM activity.organization_members
    WHERE user_id = p_user_id AND organization_id = p_organization_id;

    RETURN v_role;
END;
$$;


ALTER FUNCTION activity.sp_get_user_role_in_organization(p_user_id uuid, p_organization_id uuid) OWNER TO postgres;

--
-- Name: sp_get_user_settings(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_user_settings(p_user_id uuid) RETURNS TABLE(email_notifications boolean, push_notifications boolean, activity_reminders boolean, community_updates boolean, friend_requests boolean, marketing_emails boolean, ghost_mode boolean, language character varying, timezone character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Create default settings if not exists
    INSERT INTO activity.user_settings (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING;

    -- Return settings
    RETURN QUERY
    SELECT
        us.email_notifications,
        us.push_notifications,
        us.activity_reminders,
        us.community_updates,
        us.friend_requests,
        us.marketing_emails,
        us.ghost_mode,
        us.language,
        us.timezone
    FROM activity.user_settings us
    WHERE us.user_id = p_user_id;
END;
$$;


ALTER FUNCTION activity.sp_get_user_settings(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_get_valid_refresh_token(character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_get_valid_refresh_token(p_token character varying) RETURNS TABLE(id integer, user_id uuid, token character varying, jti character varying, expires_at timestamp without time zone, created_at timestamp without time zone, revoked boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        rt.id,
        rt.user_id,
        rt.token,
        rt.jti,
        rt.expires_at,
        rt.created_at,
        rt.revoked
    FROM activity.refresh_tokens rt
    WHERE rt.token = p_token
      AND rt.revoked = FALSE
      AND rt.expires_at > NOW();
END;
$$;


ALTER FUNCTION activity.sp_get_valid_refresh_token(p_token character varying) OWNER TO postgres;

--
-- Name: sp_increment_no_show_count(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_increment_no_show_count(p_user_id uuid) RETURNS TABLE(new_count integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_new_count INT;
BEGIN
    UPDATE activity.users
    SET
        no_show_count = no_show_count + 1,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING no_show_count INTO v_new_count;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    RETURN QUERY SELECT v_new_count;
END;
$$;


ALTER FUNCTION activity.sp_increment_no_show_count(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_increment_verification_count(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_increment_verification_count(p_user_id uuid) RETURNS TABLE(new_count integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_new_count INT;
BEGIN
    UPDATE activity.users
    SET
        verification_count = verification_count + 1,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING verification_count INTO v_new_count;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    RETURN QUERY SELECT v_new_count;
END;
$$;


ALTER FUNCTION activity.sp_increment_verification_count(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_is_organization_member(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_is_organization_member(p_user_id uuid, p_org_id uuid) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_is_member BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1
        FROM activity.organization_members
        WHERE user_id = p_user_id
          AND organization_id = p_org_id
    ) INTO v_is_member;

    RETURN v_is_member;
END;
$$;


ALTER FUNCTION activity.sp_is_organization_member(p_user_id uuid, p_org_id uuid) OWNER TO postgres;

--
-- Name: sp_join_activity(uuid, uuid, activity.subscription_level); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_join_activity(p_activity_id uuid, p_user_id uuid, p_subscription_level activity.subscription_level) RETURNS TABLE(success boolean, participation_status activity.participation_status, waitlist_position integer, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_user RECORD;
    v_organizer_id UUID;
    v_block_exists BOOLEAN;
    v_friendship_exists BOOLEAN;
    v_invitation_exists BOOLEAN;
    v_already_joined BOOLEAN;
    v_current_count INT;
    v_next_position INT;
BEGIN
    RAISE NOTICE 'sp_join_activity called: activity_id=%, user_id=%, subscription_level=%',
        p_activity_id, p_user_id, p_subscription_level;

    -- Get activity details
    SELECT a.*, a.organizer_user_id INTO v_activity
    FROM activity.activities a
    WHERE a.activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'Activity found: title=%, status=%, organizer_id=%',
        v_activity.title, v_activity.status, v_activity.organizer_user_id;

    -- Check activity status
    IF v_activity.status != 'published' THEN
        RAISE NOTICE 'Activity not published: status=%', v_activity.status;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'ACTIVITY_NOT_PUBLISHED'::VARCHAR(50), 'Activity is not published'::TEXT;
        RETURN;
    END IF;

    -- Check if activity is in the past
    IF v_activity.scheduled_at <= NOW() THEN
        RAISE NOTICE 'Activity is in the past: scheduled_at=%', v_activity.scheduled_at;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'ACTIVITY_IN_PAST'::VARCHAR(50), 'Cannot join past activities'::TEXT;
        RETURN;
    END IF;

    -- Get user details
    SELECT u.* INTO v_user
    FROM activity.users u
    WHERE u.user_id = p_user_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'User not found: %', p_user_id;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'USER_NOT_FOUND'::VARCHAR(50), 'User does not exist'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'User found: username=%, is_active=%, status=%',
        v_user.username, v_user.is_active, v_user.status;

    -- Check user is active
    IF NOT v_user.is_active THEN
        RAISE NOTICE 'User is not active: user_id=%', p_user_id;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'USER_NOT_FOUND'::VARCHAR(50), 'User does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check user is not banned
    IF v_user.status = 'banned' THEN
        RAISE NOTICE 'User is banned: user_id=%', p_user_id;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'USER_BANNED'::VARCHAR(50), 'Account is banned'::TEXT;
        RETURN;
    END IF;

    -- Check user is not the organizer
    IF v_activity.organizer_user_id = p_user_id THEN
        RAISE NOTICE 'User is organizer of activity: user_id=%', p_user_id;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'USER_IS_ORGANIZER'::VARCHAR(50), 'Organizer cannot join own activity'::TEXT;
        RETURN;
    END IF;

    -- Check if already joined or waitlisted
    SELECT EXISTS(
        SELECT 1 FROM activity.participants
        WHERE activity_id = p_activity_id AND user_id = p_user_id
    ) INTO v_already_joined;

    IF v_already_joined THEN
        RAISE NOTICE 'User already joined: user_id=%', p_user_id;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'ALREADY_JOINED'::VARCHAR(50), 'Already joined this activity'::TEXT;
        RETURN;
    END IF;

    SELECT EXISTS(
        SELECT 1 FROM activity.waitlist_entries
        WHERE activity_id = p_activity_id AND user_id = p_user_id
    ) INTO v_already_joined;

    IF v_already_joined THEN
        RAISE NOTICE 'User already on waitlist: user_id=%', p_user_id;
        RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
            'ALREADY_JOINED'::VARCHAR(50), 'Already on waitlist for this activity'::TEXT;
        RETURN;
    END IF;

    -- Blocking check (CRITICAL: skip for XXL activities)
    IF v_activity.activity_type != 'xxl' THEN
        RAISE NOTICE 'Checking blocking for non-XXL activity';
        SELECT EXISTS(
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = p_user_id AND blocked_user_id = v_activity.organizer_user_id)
               OR (blocker_user_id = v_activity.organizer_user_id AND blocked_user_id = p_user_id)
        ) INTO v_block_exists;

        IF v_block_exists THEN
            RAISE NOTICE 'User is blocked: user_id=%, organizer_id=%', p_user_id, v_activity.organizer_user_id;
            RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
                'BLOCKED_USER'::VARCHAR(50), 'Cannot join this activity due to blocking'::TEXT;
            RETURN;
        END IF;
    ELSE
        RAISE NOTICE 'XXL activity - blocking check skipped';
    END IF;

    -- Privacy check: friends_only
    IF v_activity.activity_privacy_level = 'friends_only' THEN
        RAISE NOTICE 'Checking friendship for friends_only activity';
        SELECT EXISTS(
            SELECT 1 FROM activity.friendships
            WHERE ((user_id_1 = p_user_id AND user_id_2 = v_activity.organizer_user_id)
                OR (user_id_1 = v_activity.organizer_user_id AND user_id_2 = p_user_id))
              AND status = 'accepted'
        ) INTO v_friendship_exists;

        IF NOT v_friendship_exists THEN
            RAISE NOTICE 'Not friends with organizer for friends_only activity';
            RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
                'FRIENDS_ONLY'::VARCHAR(50), 'Activity is friends only'::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Privacy check: invite_only
    IF v_activity.activity_privacy_level = 'invite_only' THEN
        RAISE NOTICE 'Checking invitation for invite_only activity';
        SELECT EXISTS(
            SELECT 1 FROM activity.activity_invitations
            WHERE activity_id = p_activity_id
              AND user_id = p_user_id
              AND status = 'pending'
              AND (expires_at IS NULL OR expires_at > NOW())
        ) INTO v_invitation_exists;

        IF NOT v_invitation_exists THEN
            RAISE NOTICE 'No valid invitation for invite_only activity';
            RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
                'INVITE_ONLY'::VARCHAR(50), 'Activity is invite only'::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Premium priority check
    IF v_activity.joinable_at_free IS NOT NULL AND p_subscription_level = 'free' THEN
        IF NOW() < v_activity.joinable_at_free THEN
            RAISE NOTICE 'Premium only period active: joinable_at_free=%, now=%',
                v_activity.joinable_at_free, NOW();
            RETURN QUERY SELECT FALSE, NULL::activity.participation_status, NULL::INT,
                'PREMIUM_ONLY_PERIOD'::VARCHAR(50), 'Activity is currently only open to Premium members'::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Capacity check
    v_current_count := v_activity.current_participants_count;
    RAISE NOTICE 'Capacity check: current=%, max=%', v_current_count, v_activity.max_participants;

    IF v_current_count >= v_activity.max_participants THEN
        -- Add to waitlist
        RAISE NOTICE 'Activity full - adding to waitlist';

        SELECT COALESCE(MAX(position), 0) + 1 INTO v_next_position
        FROM activity.waitlist_entries
        WHERE activity_id = p_activity_id;

        INSERT INTO activity.waitlist_entries (activity_id, user_id, position)
        VALUES (p_activity_id, p_user_id, v_next_position);

        UPDATE activity.activities
        SET waitlist_count = waitlist_count + 1
        WHERE activity_id = p_activity_id;

        RAISE NOTICE 'Added to waitlist: position=%', v_next_position;

        RETURN QUERY SELECT TRUE, 'waitlisted'::activity.participation_status, v_next_position,
            NULL::VARCHAR(50), NULL::TEXT;
        RETURN;
    ELSE
        -- Add as participant
        RAISE NOTICE 'Spots available - adding as participant';

        INSERT INTO activity.participants (activity_id, user_id, role, participation_status)
        VALUES (p_activity_id, p_user_id, 'member', 'registered');

        UPDATE activity.activities
        SET current_participants_count = current_participants_count + 1
        WHERE activity_id = p_activity_id;

        -- If invite_only, mark invitation as accepted
        IF v_activity.activity_privacy_level = 'invite_only' THEN
            UPDATE activity.activity_invitations
            SET status = 'accepted', responded_at = NOW()
            WHERE activity_id = p_activity_id AND user_id = p_user_id AND status = 'pending';
            RAISE NOTICE 'Marked invitation as accepted';
        END IF;

        RAISE NOTICE 'Successfully joined activity';

        RETURN QUERY SELECT TRUE, 'registered'::activity.participation_status, NULL::INT,
            NULL::VARCHAR(50), NULL::TEXT;
        RETURN;
    END IF;
END;
$$;


ALTER FUNCTION activity.sp_join_activity(p_activity_id uuid, p_user_id uuid, p_subscription_level activity.subscription_level) OWNER TO postgres;

--
-- Name: FUNCTION sp_join_activity(p_activity_id uuid, p_user_id uuid, p_subscription_level activity.subscription_level); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_join_activity(p_activity_id uuid, p_user_id uuid, p_subscription_level activity.subscription_level) IS 'Join activity or add to waitlist with comprehensive validation including blocking, privacy, and premium priority checks';


--
-- Name: sp_leave_activity(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_leave_activity(p_activity_id uuid, p_user_id uuid) RETURNS TABLE(success boolean, was_participant boolean, was_waitlisted boolean, promoted_user_id uuid, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_participant RECORD;
    v_waitlist RECORD;
    v_next_waitlist RECORD;
    v_old_position INT;
BEGIN
    RAISE NOTICE 'sp_leave_activity called: activity_id=%, user_id=%', p_activity_id, p_user_id;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE, FALSE, FALSE, NULL::UUID,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'Activity found: title=%, organizer_id=%', v_activity.title, v_activity.organizer_user_id;

    -- Check user is not the organizer
    IF v_activity.organizer_user_id = p_user_id THEN
        RAISE NOTICE 'User is organizer - cannot leave';
        RETURN QUERY SELECT FALSE, FALSE, FALSE, NULL::UUID,
            'IS_ORGANIZER'::VARCHAR(50), 'Organizer cannot leave activity'::TEXT;
        RETURN;
    END IF;

    -- Check activity is not in the past
    IF v_activity.scheduled_at <= NOW() THEN
        RAISE NOTICE 'Activity is in the past: scheduled_at=%', v_activity.scheduled_at;
        RETURN QUERY SELECT FALSE, FALSE, FALSE, NULL::UUID,
            'ACTIVITY_IN_PAST'::VARCHAR(50), 'Cannot leave past activities'::TEXT;
        RETURN;
    END IF;

    -- Check if user is participant
    SELECT * INTO v_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_user_id;

    IF FOUND AND v_participant.participation_status = 'registered' THEN
        RAISE NOTICE 'User is registered participant - removing and promoting waitlist';

        -- Delete participant
        DELETE FROM activity.participants
        WHERE activity_id = p_activity_id AND user_id = p_user_id;

        UPDATE activity.activities
        SET current_participants_count = current_participants_count - 1
        WHERE activity_id = p_activity_id;

        -- Promote next from waitlist
        SELECT * INTO v_next_waitlist
        FROM activity.waitlist_entries
        WHERE activity_id = p_activity_id
        ORDER BY position ASC
        LIMIT 1;

        IF FOUND THEN
            RAISE NOTICE 'Promoting from waitlist: user_id=%, position=%',
                v_next_waitlist.user_id, v_next_waitlist.position;

            -- Add promoted user as participant
            INSERT INTO activity.participants (activity_id, user_id, role, participation_status)
            VALUES (p_activity_id, v_next_waitlist.user_id, 'member', 'registered');

            -- Remove from waitlist
            DELETE FROM activity.waitlist_entries
            WHERE waitlist_id = v_next_waitlist.waitlist_id;

            -- Update counts
            UPDATE activity.activities
            SET waitlist_count = waitlist_count - 1,
                current_participants_count = current_participants_count + 1
            WHERE activity_id = p_activity_id;

            -- Update waitlist positions
            UPDATE activity.waitlist_entries
            SET position = position - 1
            WHERE activity_id = p_activity_id;

            RAISE NOTICE 'Waitlist promotion complete';

            RETURN QUERY SELECT TRUE, TRUE, FALSE, v_next_waitlist.user_id,
                NULL::VARCHAR(50), NULL::TEXT;
            RETURN;
        ELSE
            RAISE NOTICE 'No waitlist to promote';
            RETURN QUERY SELECT TRUE, TRUE, FALSE, NULL::UUID,
                NULL::VARCHAR(50), NULL::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Check if user is on waitlist
    SELECT * INTO v_waitlist
    FROM activity.waitlist_entries
    WHERE activity_id = p_activity_id AND user_id = p_user_id;

    IF FOUND THEN
        RAISE NOTICE 'User is on waitlist - removing: position=%', v_waitlist.position;
        v_old_position := v_waitlist.position;

        -- Delete from waitlist
        DELETE FROM activity.waitlist_entries
        WHERE waitlist_id = v_waitlist.waitlist_id;

        UPDATE activity.activities
        SET waitlist_count = waitlist_count - 1
        WHERE activity_id = p_activity_id;

        -- Update positions for users after this one
        UPDATE activity.waitlist_entries
        SET position = position - 1
        WHERE activity_id = p_activity_id AND position > v_old_position;

        RAISE NOTICE 'Removed from waitlist and updated positions';

        RETURN QUERY SELECT TRUE, FALSE, TRUE, NULL::UUID,
            NULL::VARCHAR(50), NULL::TEXT;
        RETURN;
    END IF;

    -- Not a participant or on waitlist
    RAISE NOTICE 'User is not a participant or on waitlist';
    RETURN QUERY SELECT FALSE, FALSE, FALSE, NULL::UUID,
        'NOT_PARTICIPANT'::VARCHAR(50), 'Not a participant of this activity'::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_leave_activity(p_activity_id uuid, p_user_id uuid) OWNER TO postgres;

--
-- Name: FUNCTION sp_leave_activity(p_activity_id uuid, p_user_id uuid); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_leave_activity(p_activity_id uuid, p_user_id uuid) IS 'Leave activity with automatic waitlist promotion';


--
-- Name: sp_mark_attendance(uuid, uuid, jsonb); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mark_attendance(p_activity_id uuid, p_marking_user_id uuid, p_attendances jsonb) RETURNS TABLE(success boolean, updated_count integer, failed_updates jsonb, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_marking_participant RECORD;
    v_attendance JSONB;
    v_target_user_id UUID;
    v_target_status activity.attendance_status;
    v_update_count INT := 0;
    v_failed_array JSONB := '[]'::jsonb;
    v_attendance_count INT;
BEGIN
    RAISE NOTICE 'sp_mark_attendance called: activity_id=%, marking_user_id=%, attendance_count=%',
        p_activity_id, p_marking_user_id, jsonb_array_length(p_attendances);

    -- Count attendances
    v_attendance_count := jsonb_array_length(p_attendances);

    IF v_attendance_count > 100 THEN
        RAISE NOTICE 'Too many attendance updates: count=%', v_attendance_count;
        RETURN QUERY SELECT FALSE, 0, NULL::JSONB,
            'TOO_MANY_UPDATES'::VARCHAR(50), 'Maximum 100 attendances per request'::TEXT;
        RETURN;
    END IF;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE, 0, NULL::JSONB,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check activity has completed
    IF v_activity.scheduled_at > NOW() THEN
        RAISE NOTICE 'Activity has not completed: scheduled_at=%', v_activity.scheduled_at;
        RETURN QUERY SELECT FALSE, 0, NULL::JSONB,
            'ACTIVITY_NOT_COMPLETED'::VARCHAR(50), 'Activity has not yet completed'::TEXT;
        RETURN;
    END IF;

    -- Check marking user is organizer or co-organizer
    SELECT * INTO v_marking_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_marking_user_id;

    IF NOT FOUND OR (v_marking_participant.role != 'organizer' AND v_marking_participant.role != 'co_organizer') THEN
        RAISE NOTICE 'User is not authorized to mark attendance: role=%',
            COALESCE(v_marking_participant.role::TEXT, 'none');
        RETURN QUERY SELECT FALSE, 0, NULL::JSONB,
            'NOT_AUTHORIZED'::VARCHAR(50), 'Only organizer or co-organizer can mark attendance'::TEXT;
        RETURN;
    END IF;

    RAISE NOTICE 'Authorization passed, processing % attendances', v_attendance_count;

    -- Process each attendance
    FOR v_attendance IN SELECT * FROM jsonb_array_elements(p_attendances)
    LOOP
        v_target_user_id := (v_attendance->>'user_id')::UUID;
        v_target_status := (v_attendance->>'status')::activity.attendance_status;

        RAISE NOTICE 'Processing attendance: user_id=%, status=%', v_target_user_id, v_target_status;

        -- Check if user is a registered participant
        IF EXISTS (
            SELECT 1 FROM activity.participants
            WHERE activity_id = p_activity_id
              AND user_id = v_target_user_id
              AND participation_status = 'registered'
        ) THEN
            -- Update attendance status
            UPDATE activity.participants
            SET attendance_status = v_target_status
            WHERE activity_id = p_activity_id AND user_id = v_target_user_id;

            -- If no_show, increment user's no_show_count
            IF v_target_status = 'no_show' THEN
                UPDATE activity.users
                SET no_show_count = no_show_count + 1
                WHERE user_id = v_target_user_id;
                RAISE NOTICE 'Incremented no_show_count for user: %', v_target_user_id;
            END IF;

            v_update_count := v_update_count + 1;
            RAISE NOTICE 'Updated attendance successfully';
        ELSE
            -- Add to failed updates
            v_failed_array := v_failed_array || jsonb_build_object(
                'user_id', v_target_user_id,
                'reason', 'Not a registered participant'
            );
            RAISE NOTICE 'Failed to update - not a registered participant';
        END IF;
    END LOOP;

    RAISE NOTICE 'Attendance marking complete: updated=%, failed=%',
        v_update_count, jsonb_array_length(v_failed_array);

    RETURN QUERY SELECT TRUE, v_update_count, v_failed_array,
        NULL::VARCHAR(50), NULL::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_mark_attendance(p_activity_id uuid, p_marking_user_id uuid, p_attendances jsonb) OWNER TO postgres;

--
-- Name: FUNCTION sp_mark_attendance(p_activity_id uuid, p_marking_user_id uuid, p_attendances jsonb); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_mark_attendance(p_activity_id uuid, p_marking_user_id uuid, p_attendances jsonb) IS 'Bulk mark attendance after activity completion (organizer/co-organizer only)';


--
-- Name: sp_mark_notification_as_read(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mark_notification_as_read(p_user_id uuid, p_notification_id uuid) RETURNS TABLE(notification_id uuid, status character varying, read_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE activity.notifications
    SET
        status = 'read'::activity.notification_status,
        read_at = NOW()
    WHERE notifications.notification_id = p_notification_id
        AND notifications.user_id = p_user_id
        AND notifications.status = 'unread'::activity.notification_status;

    RETURN QUERY
    SELECT
        n.notification_id AS notification_id,
        n.status::VARCHAR AS status,
        n.read_at AS read_at
    FROM activity.notifications n
    WHERE n.notification_id = p_notification_id
        AND n.user_id = p_user_id;
END;
$$;


ALTER FUNCTION activity.sp_mark_notification_as_read(p_user_id uuid, p_notification_id uuid) OWNER TO postgres;

--
-- Name: sp_mark_notifications_as_read_bulk(uuid, uuid[], character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mark_notifications_as_read_bulk(p_user_id uuid, p_notification_ids uuid[] DEFAULT NULL::uuid[], p_notification_type character varying DEFAULT NULL::character varying) RETURNS TABLE(updated_count bigint)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_updated_count BIGINT;
BEGIN
    -- If notification_ids provided, mark those
    IF p_notification_ids IS NOT NULL THEN
        UPDATE activity.notifications
        SET
            status = 'read'::activity.notification_status,
            read_at = NOW()
        WHERE user_id = p_user_id
            AND notification_id = ANY(p_notification_ids)
            AND status = 'unread'::activity.notification_status;

        GET DIAGNOSTICS v_updated_count = ROW_COUNT;

    -- If notification_type provided, mark all of that type
    ELSIF p_notification_type IS NOT NULL THEN
        UPDATE activity.notifications
        SET
            status = 'read'::activity.notification_status,
            read_at = NOW()
        WHERE user_id = p_user_id
            AND notification_type::VARCHAR = p_notification_type
            AND status = 'unread'::activity.notification_status;

        GET DIAGNOSTICS v_updated_count = ROW_COUNT;

    -- Otherwise mark all unread
    ELSE
        UPDATE activity.notifications
        SET
            status = 'read'::activity.notification_status,
            read_at = NOW()
        WHERE user_id = p_user_id
            AND status = 'unread'::activity.notification_status;

        GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    END IF;

    RETURN QUERY SELECT v_updated_count;
END;
$$;


ALTER FUNCTION activity.sp_mark_notifications_as_read_bulk(p_user_id uuid, p_notification_ids uuid[], p_notification_type character varying) OWNER TO postgres;

--
-- Name: sp_mod_ban_user(uuid, uuid, character varying, text, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_ban_user(p_admin_user_id uuid, p_user_id uuid, p_ban_type character varying, p_ban_reason text, p_ban_duration_hours integer DEFAULT NULL::integer) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_user_status VARCHAR(20);
    v_ban_expires_at TIMESTAMP WITH TIME ZONE;
    v_new_status VARCHAR(20);
    v_username VARCHAR(100);
    v_email VARCHAR(255);
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Check for self-ban
    IF p_admin_user_id = p_user_id THEN
        RAISE EXCEPTION 'CANNOT_SELF_BAN: You cannot ban yourself';
    END IF;

    -- 3. Validate ban_type
    IF p_ban_type NOT IN ('permanent', 'temporary') THEN
        RAISE EXCEPTION 'INVALID_BAN_TYPE: ban_type must be permanent or temporary';
    END IF;

    -- 4. Get user status
    SELECT status::VARCHAR, username, email INTO v_user_status, v_username, v_email
    FROM activity.users
    WHERE user_id = p_user_id;

    IF v_user_status IS NULL THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: User with specified ID does not exist';
    END IF;

    IF v_user_status IN ('temporary_ban', 'banned') THEN
        RAISE EXCEPTION 'USER_ALREADY_BANNED: User is already banned';
    END IF;

    -- 5. Calculate ban expiry and new status
    IF p_ban_type = 'temporary' THEN
        IF p_ban_duration_hours IS NULL OR p_ban_duration_hours <= 0 THEN
            RAISE EXCEPTION 'DURATION_REQUIRED: ban_duration_hours is required for temporary bans';
        END IF;
        v_ban_expires_at := NOW() + (p_ban_duration_hours || ' hours')::INTERVAL;
        v_new_status := 'temporary_ban';
    ELSE
        v_ban_expires_at := NULL;
        v_new_status := 'banned';
    END IF;

    -- 6. Update user status
    UPDATE activity.users
    SET status = v_new_status::activity.user_status,
        ban_expires_at = v_ban_expires_at,
        ban_reason = p_ban_reason,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    -- 7. Return result (including email and username for API layer)
    v_result := json_build_object(
        'success', TRUE,
        'user_id', p_user_id,
        'status', v_new_status,
        'ban_expires_at', v_ban_expires_at,
        'ban_reason', p_ban_reason,
        'banned_at', NOW(),
        'email', v_email,
        'username', v_username
    );

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_ban_user(p_admin_user_id uuid, p_user_id uuid, p_ban_type character varying, p_ban_reason text, p_ban_duration_hours integer) OWNER TO postgres;

--
-- Name: sp_mod_create_report(uuid, uuid, character varying, uuid, character varying, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_create_report(p_reporter_user_id uuid, p_reported_user_id uuid, p_target_type character varying, p_target_id uuid, p_report_type character varying, p_description text) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_report_id UUID;
    v_reporter_active BOOLEAN;
    v_target_exists BOOLEAN := FALSE;
    v_duplicate_count INT;
    v_result JSON;
BEGIN
    -- 1. Validate reporter exists and is active
    SELECT is_active INTO v_reporter_active
    FROM activity.users
    WHERE user_id = p_reporter_user_id;

    IF v_reporter_active IS NULL THEN
        RAISE EXCEPTION 'REPORTER_NOT_FOUND: Reporter user does not exist';
    END IF;

    IF NOT v_reporter_active THEN
        RAISE EXCEPTION 'REPORTER_INACTIVE: Reporter user is not active';
    END IF;

    -- 2. Validate target_type
    IF p_target_type NOT IN ('user', 'post', 'comment', 'activity', 'community') THEN
        RAISE EXCEPTION 'INVALID_TARGET_TYPE: target_type must be user, post, comment, activity, or community';
    END IF;

    -- 3. Validate report_type
    IF p_report_type NOT IN ('spam', 'harassment', 'inappropriate', 'fake', 'no_show', 'other') THEN
        RAISE EXCEPTION 'INVALID_REPORT_TYPE: report_type must be spam, harassment, inappropriate, fake, no_show, or other';
    END IF;

    -- 4. Check if target exists based on target_type
    CASE p_target_type
        WHEN 'user' THEN
            SELECT EXISTS(SELECT 1 FROM activity.users WHERE user_id = p_target_id) INTO v_target_exists;
            -- Set reported_user_id to target_id for user reports
            p_reported_user_id := p_target_id;
        WHEN 'post' THEN
            SELECT EXISTS(SELECT 1 FROM activity.posts WHERE post_id = p_target_id) INTO v_target_exists;
        WHEN 'comment' THEN
            SELECT EXISTS(SELECT 1 FROM activity.comments WHERE comment_id = p_target_id) INTO v_target_exists;
        WHEN 'activity' THEN
            SELECT EXISTS(SELECT 1 FROM activity.activities WHERE activity_id = p_target_id) INTO v_target_exists;
        WHEN 'community' THEN
            SELECT EXISTS(SELECT 1 FROM activity.communities WHERE community_id = p_target_id) INTO v_target_exists;
    END CASE;

    IF NOT v_target_exists THEN
        RAISE EXCEPTION 'TARGET_NOT_FOUND: The specified target does not exist';
    END IF;

    -- 5. Check for self-reporting
    IF p_reported_user_id = p_reporter_user_id THEN
        RAISE EXCEPTION 'CANNOT_SELF_REPORT: You cannot report yourself';
    END IF;

    -- 6. Check for duplicate reports within 24 hours
    SELECT COUNT(*) INTO v_duplicate_count
    FROM activity.reports
    WHERE reporter_user_id = p_reporter_user_id
      AND target_id = p_target_id
      AND report_type = p_report_type::activity.report_type
      AND created_at > NOW() - INTERVAL '24 hours';

    IF v_duplicate_count > 0 THEN
        RAISE EXCEPTION 'DUPLICATE_REPORT: You have already reported this target within the last 24 hours';
    END IF;

    -- 7. Generate report_id using uuidv7()
    v_report_id := uuidv7();

    -- 8. Insert report
    INSERT INTO activity.reports (
        report_id,
        reporter_user_id,
        reported_user_id,
        target_type,
        target_id,
        report_type,
        description,
        status,
        created_at,
        updated_at
    ) VALUES (
        v_report_id,
        p_reporter_user_id,
        p_reported_user_id,
        p_target_type,
        p_target_id,
        p_report_type::activity.report_type,
        p_description,
        'pending'::activity.report_status,
        NOW(),
        NOW()
    );

    -- 9. If no_show report on user, increment no_show_count
    IF p_report_type = 'no_show' AND p_target_type = 'user' THEN
        UPDATE activity.users
        SET no_show_count = no_show_count + 1,
            updated_at = NOW()
        WHERE user_id = p_reported_user_id;
    END IF;

    -- 10. Return JSON result
    v_result := json_build_object(
        'success', TRUE,
        'report_id', v_report_id,
        'status', 'pending',
        'created_at', NOW()
    );

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_create_report(p_reporter_user_id uuid, p_reported_user_id uuid, p_target_type character varying, p_target_id uuid, p_report_type character varying, p_description text) OWNER TO postgres;

--
-- Name: sp_mod_get_pending_photos(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_get_pending_photos(p_admin_user_id uuid, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0) RETURNS TABLE(user_id uuid, username character varying, email character varying, main_photo_url character varying, created_at timestamp with time zone, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE activity.users.user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Return pending photos (oldest first - FIFO queue)
    RETURN QUERY
    SELECT
        u.user_id,
        u.username,
        u.email,
        u.main_photo_url,
        u.created_at,
        u.updated_at
    FROM activity.users u
    WHERE u.main_photo_moderation_status = 'pending'::activity.photo_moderation_status
      AND u.main_photo_url IS NOT NULL
      AND u.main_photo_url != ''
    ORDER BY u.created_at ASC
    LIMIT p_limit OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_mod_get_pending_photos(p_admin_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_mod_get_report_by_id(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_get_report_by_id(p_admin_user_id uuid, p_report_id uuid) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Fetch report with all details
    SELECT json_build_object(
        'success', TRUE,
        'report', json_build_object(
            'report_id', r.report_id,
            'reporter', json_build_object(
                'user_id', reporter.user_id,
                'username', reporter.username,
                'email', reporter.email
            ),
            'reported_user', CASE
                WHEN r.reported_user_id IS NOT NULL THEN
                    json_build_object(
                        'user_id', reported.user_id,
                        'username', reported.username,
                        'email', reported.email,
                        'no_show_count', reported.no_show_count,
                        'verification_count', reported.verification_count
                    )
                ELSE NULL
            END,
            'target_type', r.target_type,
            'target_id', r.target_id,
            'report_type', r.report_type,
            'description', r.description,
            'status', r.status,
            'reviewed_by', CASE
                WHEN r.reviewed_by_user_id IS NOT NULL THEN
                    json_build_object(
                        'user_id', reviewer.user_id,
                        'username', reviewer.username,
                        'email', reviewer.email
                    )
                ELSE NULL
            END,
            'reviewed_at', r.reviewed_at,
            'resolution_notes', r.resolution_notes,
            'created_at', r.created_at,
            'updated_at', r.updated_at
        )
    ) INTO v_result
    FROM activity.reports r
    INNER JOIN activity.users reporter ON r.reporter_user_id = reporter.user_id
    LEFT JOIN activity.users reported ON r.reported_user_id = reported.user_id
    LEFT JOIN activity.users reviewer ON r.reviewed_by_user_id = reviewer.user_id
    WHERE r.report_id = p_report_id;

    IF v_result IS NULL THEN
        RAISE EXCEPTION 'REPORT_NOT_FOUND: Report with specified ID does not exist';
    END IF;

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_get_report_by_id(p_admin_user_id uuid, p_report_id uuid) OWNER TO postgres;

--
-- Name: sp_mod_get_reports(uuid, character varying, character varying, character varying, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_get_reports(p_admin_user_id uuid, p_status character varying DEFAULT NULL::character varying, p_target_type character varying DEFAULT NULL::character varying, p_report_type character varying DEFAULT NULL::character varying, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0) RETURNS TABLE(report_id uuid, reporter_user_id uuid, reporter_username character varying, reporter_email character varying, reported_user_id uuid, reported_username character varying, reported_email character varying, target_type character varying, target_id uuid, report_type character varying, description text, status character varying, reviewed_by_user_id uuid, reviewed_by_username character varying, reviewed_at timestamp with time zone, resolution_notes text, created_at timestamp with time zone, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
BEGIN
    -- 1. Validate admin exists and is active
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    IF NOT v_admin_active THEN
        RAISE EXCEPTION 'ADMIN_INACTIVE: Admin user is not active';
    END IF;

    -- Note: Admin permission check would normally happen here via JWT roles in the API layer

    -- 2. Validate filters if provided
    IF p_status IS NOT NULL AND p_status NOT IN ('pending', 'reviewing', 'resolved', 'dismissed') THEN
        RAISE EXCEPTION 'INVALID_STATUS: status must be pending, reviewing, resolved, or dismissed';
    END IF;

    IF p_target_type IS NOT NULL AND p_target_type NOT IN ('user', 'post', 'comment', 'activity', 'community') THEN
        RAISE EXCEPTION 'INVALID_TARGET_TYPE: target_type must be user, post, comment, activity, or community';
    END IF;

    IF p_report_type IS NOT NULL AND p_report_type NOT IN ('spam', 'harassment', 'inappropriate', 'fake', 'no_show', 'other') THEN
        RAISE EXCEPTION 'INVALID_REPORT_TYPE: Invalid report_type value';
    END IF;

    -- 3. Return filtered and paginated reports
    RETURN QUERY
    SELECT
        r.report_id,
        r.reporter_user_id,
        reporter.username AS reporter_username,
        reporter.email AS reporter_email,
        r.reported_user_id,
        reported.username AS reported_username,
        reported.email AS reported_email,
        r.target_type,
        r.target_id,
        r.report_type::VARCHAR,
        r.description,
        r.status::VARCHAR,
        r.reviewed_by_user_id,
        reviewer.username AS reviewed_by_username,
        r.reviewed_at,
        r.resolution_notes,
        r.created_at,
        r.updated_at
    FROM activity.reports r
    INNER JOIN activity.users reporter ON r.reporter_user_id = reporter.user_id
    LEFT JOIN activity.users reported ON r.reported_user_id = reported.user_id
    LEFT JOIN activity.users reviewer ON r.reviewed_by_user_id = reviewer.user_id
    WHERE (p_status IS NULL OR r.status::VARCHAR = p_status)
      AND (p_target_type IS NULL OR r.target_type = p_target_type)
      AND (p_report_type IS NULL OR r.report_type::VARCHAR = p_report_type)
    ORDER BY r.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_mod_get_reports(p_admin_user_id uuid, p_status character varying, p_target_type character varying, p_report_type character varying, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_mod_get_statistics(uuid, timestamp with time zone, timestamp with time zone); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_get_statistics(p_admin_user_id uuid, p_date_from timestamp with time zone DEFAULT NULL::timestamp with time zone, p_date_to timestamp with time zone DEFAULT NULL::timestamp with time zone) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_date_from TIMESTAMP WITH TIME ZONE;
    v_date_to TIMESTAMP WITH TIME ZONE;
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Set date range defaults
    v_date_from := COALESCE(p_date_from, NOW() - INTERVAL '30 days');
    v_date_to := COALESCE(p_date_to, NOW());

    -- Validate date range
    IF v_date_from > v_date_to THEN
        RAISE EXCEPTION 'INVALID_DATE_RANGE: date_from must be before date_to';
    END IF;

    -- 3. Calculate statistics
    SELECT json_build_object(
        'success', TRUE,
        'date_range', json_build_object(
            'from', v_date_from,
            'to', v_date_to
        ),
        'reports', json_build_object(
            'total', (
                SELECT COUNT(*)
                FROM activity.reports
                WHERE created_at BETWEEN v_date_from AND v_date_to
            ),
            'pending', (
                SELECT COUNT(*)
                FROM activity.reports
                WHERE created_at BETWEEN v_date_from AND v_date_to
                AND status = 'pending'::activity.report_status
            ),
            'reviewing', (
                SELECT COUNT(*)
                FROM activity.reports
                WHERE created_at BETWEEN v_date_from AND v_date_to
                AND status = 'reviewing'::activity.report_status
            ),
            'resolved', (
                SELECT COUNT(*)
                FROM activity.reports
                WHERE created_at BETWEEN v_date_from AND v_date_to
                AND status = 'resolved'::activity.report_status
            ),
            'dismissed', (
                SELECT COUNT(*)
                FROM activity.reports
                WHERE created_at BETWEEN v_date_from AND v_date_to
                AND status = 'dismissed'::activity.report_status
            ),
            'by_type', (
                SELECT json_object_agg(report_type::VARCHAR, count)
                FROM (
                    SELECT report_type, COUNT(*) AS count
                    FROM activity.reports
                    WHERE created_at BETWEEN v_date_from AND v_date_to
                    GROUP BY report_type
                ) AS report_types
            ),
            'avg_resolution_time_hours', (
                SELECT COALESCE(
                    AVG(EXTRACT(EPOCH FROM (reviewed_at - created_at)) / 3600),
                    0
                )
                FROM activity.reports
                WHERE reviewed_at BETWEEN v_date_from AND v_date_to
                AND reviewed_at IS NOT NULL
            )
        ),
        'users', json_build_object(
            'total_banned', (
                SELECT COUNT(*)
                FROM activity.users
                WHERE status IN ('banned'::activity.user_status, 'temporary_ban'::activity.user_status)
            ),
            'permanent_bans', (
                SELECT COUNT(*)
                FROM activity.users
                WHERE status = 'banned'::activity.user_status
            ),
            'temporary_bans', (
                SELECT COUNT(*)
                FROM activity.users
                WHERE status = 'temporary_ban'::activity.user_status
            ),
            'unbanned', 0  -- Would need ban history tracking
        ),
        'content', json_build_object(
            'posts_removed', (
                SELECT COUNT(*)
                FROM activity.posts
                WHERE status = 'removed'::activity.content_status
                AND updated_at BETWEEN v_date_from AND v_date_to
            ),
            'comments_removed', 0  -- Comments are hard-deleted, no soft delete tracking
        ),
        'photos', json_build_object(
            'pending_moderation', (
                SELECT COUNT(*)
                FROM activity.users
                WHERE main_photo_moderation_status = 'pending'::activity.photo_moderation_status
            ),
            'approved', (
                SELECT COUNT(*)
                FROM activity.users
                WHERE main_photo_moderation_status = 'approved'::activity.photo_moderation_status
                AND updated_at BETWEEN v_date_from AND v_date_to
            ),
            'rejected', (
                SELECT COUNT(*)
                FROM activity.users
                WHERE main_photo_moderation_status = 'rejected'::activity.photo_moderation_status
                AND updated_at BETWEEN v_date_from AND v_date_to
            )
        )
    ) INTO v_result;

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_get_statistics(p_admin_user_id uuid, p_date_from timestamp with time zone, p_date_to timestamp with time zone) OWNER TO postgres;

--
-- Name: sp_mod_get_user_moderation_history(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_get_user_moderation_history(p_admin_user_id uuid, p_target_user_id uuid) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_user_exists BOOLEAN;
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Validate target user exists
    SELECT EXISTS(SELECT 1 FROM activity.users WHERE user_id = p_target_user_id) INTO v_user_exists;

    IF NOT v_user_exists THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: User with specified ID does not exist';
    END IF;

    -- 3. Build comprehensive history JSON
    SELECT json_build_object(
        'success', TRUE,
        'user', (
            SELECT json_build_object(
                'user_id', u.user_id,
                'username', u.username,
                'email', u.email,
                'status', u.status,
                'no_show_count', u.no_show_count,
                'verification_count', u.verification_count,
                'created_at', u.created_at
            )
            FROM activity.users u
            WHERE u.user_id = p_target_user_id
        ),
        'moderation_summary', json_build_object(
            'total_reports_received', (
                SELECT COUNT(*)
                FROM activity.reports
                WHERE reported_user_id = p_target_user_id
            ),
            'total_reports_made', (
                SELECT COUNT(*)
                FROM activity.reports
                WHERE reporter_user_id = p_target_user_id
            ),
            'total_bans', 0,  -- Would need ban history tracking
            'total_content_removed', (
                SELECT COUNT(*) FROM activity.posts
                WHERE author_user_id = p_target_user_id
                AND status = 'removed'::activity.content_status
            ),
            'total_photo_rejections', 0  -- Would need photo rejection history
        ),
        'history', (
            SELECT COALESCE(json_agg(event ORDER BY event_date DESC), '[]'::json)
            FROM (
                -- Reports about this user
                SELECT
                    'report' AS event_type,
                    r.created_at AS event_date,
                    r.report_type::VARCHAR AS report_type,
                    r.reporter_user_id,
                    r.status::VARCHAR AS status
                FROM activity.reports r
                WHERE r.reported_user_id = p_target_user_id
                LIMIT 20
            ) AS event
        )
    ) INTO v_result;

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_get_user_moderation_history(p_admin_user_id uuid, p_target_user_id uuid) OWNER TO postgres;

--
-- Name: sp_mod_moderate_main_photo(uuid, uuid, character varying, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_moderate_main_photo(p_admin_user_id uuid, p_user_id uuid, p_moderation_status character varying, p_rejection_reason text DEFAULT NULL::text) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_user_exists BOOLEAN;
    v_main_photo_url VARCHAR(500);
    v_username VARCHAR(100);
    v_email VARCHAR(255);
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Validate moderation_status
    IF p_moderation_status NOT IN ('approved', 'rejected') THEN
        RAISE EXCEPTION 'INVALID_MODERATION_STATUS: status must be approved or rejected';
    END IF;

    -- 3. Check user exists and has main photo
    SELECT main_photo_url, username, email INTO v_main_photo_url, v_username, v_email
    FROM activity.users
    WHERE user_id = p_user_id;

    IF v_main_photo_url IS NULL THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: User with specified ID does not exist';
    END IF;

    IF v_main_photo_url = '' THEN
        RAISE EXCEPTION 'NO_MAIN_PHOTO: User has not uploaded a main profile photo';
    END IF;

    -- 4. Update user photo moderation status
    UPDATE activity.users
    SET main_photo_moderation_status = p_moderation_status::activity.photo_moderation_status,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    -- 5. If rejected, store reason in payload
    IF p_moderation_status = 'rejected' AND p_rejection_reason IS NOT NULL THEN
        UPDATE activity.users
        SET payload = COALESCE(payload, '{}'::JSONB) ||
                     jsonb_build_object('photo_rejection_reason', p_rejection_reason)
        WHERE user_id = p_user_id;
    END IF;

    -- 6. Return result (including email and username for API layer to send notification)
    v_result := json_build_object(
        'success', TRUE,
        'user_id', p_user_id,
        'main_photo_url', v_main_photo_url,
        'moderation_status', p_moderation_status,
        'moderated_at', NOW(),
        'email', v_email,
        'username', v_username
    );

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_moderate_main_photo(p_admin_user_id uuid, p_user_id uuid, p_moderation_status character varying, p_rejection_reason text) OWNER TO postgres;

--
-- Name: sp_mod_remove_content(uuid, character varying, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_remove_content(p_admin_user_id uuid, p_content_type character varying, p_content_id uuid, p_removal_reason text) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_author_user_id UUID;
    v_author_email VARCHAR(255);
    v_author_username VARCHAR(100);
    v_content_exists BOOLEAN := FALSE;
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Validate content_type
    IF p_content_type NOT IN ('post', 'comment') THEN
        RAISE EXCEPTION 'INVALID_CONTENT_TYPE: content_type must be post or comment';
    END IF;

    -- 3. Remove content based on type
    IF p_content_type = 'post' THEN
        -- Check post exists and get author
        SELECT author_user_id INTO v_author_user_id
        FROM activity.posts
        WHERE post_id = p_content_id;

        IF v_author_user_id IS NULL THEN
            RAISE EXCEPTION 'CONTENT_NOT_FOUND: Post with specified ID does not exist';
        END IF;

        -- Check if already removed
        IF EXISTS (
            SELECT 1 FROM activity.posts
            WHERE post_id = p_content_id
            AND status = 'removed'::activity.content_status
        ) THEN
            RAISE EXCEPTION 'CONTENT_ALREADY_REMOVED: This content has already been removed';
        END IF;

        -- Update post status
        UPDATE activity.posts
        SET status = 'removed'::activity.content_status,
            updated_at = NOW()
        WHERE post_id = p_content_id;

        v_content_exists := TRUE;

    ELSIF p_content_type = 'comment' THEN
        -- Check comment exists and get author
        SELECT author_user_id INTO v_author_user_id
        FROM activity.comments
        WHERE comment_id = p_content_id;

        IF v_author_user_id IS NULL THEN
            RAISE EXCEPTION 'CONTENT_NOT_FOUND: Comment with specified ID does not exist';
        END IF;

        -- Delete comment (comments don't have soft delete, they CASCADE on post deletion)
        DELETE FROM activity.comments
        WHERE comment_id = p_content_id;

        v_content_exists := TRUE;
    END IF;

    -- 4. Get author details for email notification
    SELECT username, email INTO v_author_username, v_author_email
    FROM activity.users
    WHERE user_id = v_author_user_id;

    -- 5. Return result
    v_result := json_build_object(
        'success', TRUE,
        'content_type', p_content_type,
        'content_id', p_content_id,
        'status', 'removed',
        'removed_at', NOW(),
        'removed_by_user_id', p_admin_user_id,
        'author_user_id', v_author_user_id,
        'author_email', v_author_email,
        'author_username', v_author_username
    );

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_remove_content(p_admin_user_id uuid, p_content_type character varying, p_content_id uuid, p_removal_reason text) OWNER TO postgres;

--
-- Name: sp_mod_unban_user(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_unban_user(p_admin_user_id uuid, p_user_id uuid, p_unban_reason text) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_user_status VARCHAR(20);
    v_username VARCHAR(100);
    v_email VARCHAR(255);
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Get user status
    SELECT status::VARCHAR, username, email INTO v_user_status, v_username, v_email
    FROM activity.users
    WHERE user_id = p_user_id;

    IF v_user_status IS NULL THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: User with specified ID does not exist';
    END IF;

    IF v_user_status NOT IN ('temporary_ban', 'banned') THEN
        RAISE EXCEPTION 'USER_NOT_BANNED: User is not currently banned';
    END IF;

    -- 3. Unban user
    UPDATE activity.users
    SET status = 'active'::activity.user_status,
        ban_expires_at = NULL,
        ban_reason = NULL,
        updated_at = NOW(),
        payload = COALESCE(payload, '{}'::JSONB) ||
                 jsonb_build_object(
                     'unban_reason', p_unban_reason,
                     'unbanned_at', NOW(),
                     'unbanned_by', p_admin_user_id
                 )
    WHERE user_id = p_user_id;

    -- 4. Return result
    v_result := json_build_object(
        'success', TRUE,
        'user_id', p_user_id,
        'status', 'active',
        'unbanned_at', NOW(),
        'unbanned_by_user_id', p_admin_user_id,
        'email', v_email,
        'username', v_username
    );

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_unban_user(p_admin_user_id uuid, p_user_id uuid, p_unban_reason text) OWNER TO postgres;

--
-- Name: sp_mod_update_report_status(uuid, uuid, character varying, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_mod_update_report_status(p_admin_user_id uuid, p_report_id uuid, p_new_status character varying, p_resolution_notes text DEFAULT NULL::text) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_admin_active BOOLEAN;
    v_current_status VARCHAR(20);
    v_result JSON;
BEGIN
    -- 1. Validate admin exists
    SELECT is_active INTO v_admin_active
    FROM activity.users
    WHERE user_id = p_admin_user_id;

    IF v_admin_active IS NULL THEN
        RAISE EXCEPTION 'ADMIN_NOT_FOUND: Admin user does not exist';
    END IF;

    -- 2. Validate new_status
    IF p_new_status NOT IN ('reviewing', 'resolved', 'dismissed') THEN
        RAISE EXCEPTION 'INVALID_STATUS: status must be reviewing, resolved, or dismissed';
    END IF;

    -- 3. Get current status and validate transition
    SELECT status::VARCHAR INTO v_current_status
    FROM activity.reports
    WHERE report_id = p_report_id;

    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'REPORT_NOT_FOUND: Report with specified ID does not exist';
    END IF;

    -- Check valid transitions
    IF v_current_status IN ('resolved', 'dismissed') THEN
        RAISE EXCEPTION 'INVALID_STATUS_TRANSITION: Cannot change status from final state';
    END IF;

    -- 4. Update report
    UPDATE activity.reports
    SET status = p_new_status::activity.report_status,
        reviewed_by_user_id = p_admin_user_id,
        reviewed_at = NOW(),
        resolution_notes = p_resolution_notes,
        updated_at = NOW()
    WHERE report_id = p_report_id;

    -- 5. Return result
    v_result := json_build_object(
        'success', TRUE,
        'report_id', p_report_id,
        'status', p_new_status,
        'reviewed_by_user_id', p_admin_user_id,
        'reviewed_at', NOW()
    );

    RETURN v_result;
END;
$$;


ALTER FUNCTION activity.sp_mod_update_report_status(p_admin_user_id uuid, p_report_id uuid, p_new_status character varying, p_resolution_notes text) OWNER TO postgres;

--
-- Name: sp_moderate_main_photo(uuid, activity.photo_moderation_status, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_moderate_main_photo(p_user_id uuid, p_moderation_status activity.photo_moderation_status, p_moderator_user_id uuid) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Validate status
    IF p_moderation_status NOT IN ('approved', 'rejected') THEN
        RAISE EXCEPTION 'Moderation status must be approved or rejected';
    END IF;

    -- Update moderation status
    UPDATE activity.users
    SET
        main_photo_moderation_status = p_moderation_status,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT FOUND;
END;
$$;


ALTER FUNCTION activity.sp_moderate_main_photo(p_user_id uuid, p_moderation_status activity.photo_moderation_status, p_moderator_user_id uuid) OWNER TO postgres;

--
-- Name: sp_promote_participant(uuid, uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_promote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid) RETURNS TABLE(success boolean, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_participant RECORD;
BEGIN
    RAISE NOTICE 'sp_promote_participant called: activity_id=%, organizer_user_id=%, target_user_id=%',
        p_activity_id, p_organizer_user_id, p_target_user_id;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check requesting user is organizer
    IF v_activity.organizer_user_id != p_organizer_user_id THEN
        RAISE NOTICE 'User is not organizer: user_id=%, actual_organizer=%',
            p_organizer_user_id, v_activity.organizer_user_id;
        RETURN QUERY SELECT FALSE,
            'NOT_ORGANIZER'::VARCHAR(50), 'Only organizer can promote participants'::TEXT;
        RETURN;
    END IF;

    -- Get target participant
    SELECT * INTO v_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_target_user_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Target user is not a participant';
        RETURN QUERY SELECT FALSE,
            'TARGET_NOT_MEMBER'::VARCHAR(50), 'User is not a member participant'::TEXT;
        RETURN;
    END IF;

    -- Check target is a member with registered status
    IF v_participant.role != 'member' THEN
        IF v_participant.role = 'co_organizer' THEN
            RAISE NOTICE 'Target user is already co-organizer';
            RETURN QUERY SELECT FALSE,
                'ALREADY_CO_ORGANIZER'::VARCHAR(50), 'User is already a co-organizer'::TEXT;
            RETURN;
        END IF;

        RAISE NOTICE 'Target user is not a member: role=%', v_participant.role;
        RETURN QUERY SELECT FALSE,
            'TARGET_NOT_MEMBER'::VARCHAR(50), 'User is not a member participant'::TEXT;
        RETURN;
    END IF;

    IF v_participant.participation_status != 'registered' THEN
        RAISE NOTICE 'Target user is not registered: status=%', v_participant.participation_status;
        RETURN QUERY SELECT FALSE,
            'TARGET_NOT_MEMBER'::VARCHAR(50), 'User is not a registered participant'::TEXT;
        RETURN;
    END IF;

    -- Promote to co-organizer
    RAISE NOTICE 'Promoting user to co-organizer';
    UPDATE activity.participants
    SET role = 'co_organizer'
    WHERE activity_id = p_activity_id AND user_id = p_target_user_id;

    RAISE NOTICE 'User promoted successfully';

    RETURN QUERY SELECT TRUE,
        NULL::VARCHAR(50), NULL::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_promote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid) OWNER TO postgres;

--
-- Name: FUNCTION sp_promote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_promote_participant(p_activity_id uuid, p_organizer_user_id uuid, p_target_user_id uuid) IS 'Promote member to co-organizer (organizer only)';


--
-- Name: sp_remove_organization_member(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_remove_organization_member(p_user_id uuid, p_org_id uuid) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_deleted BOOLEAN;
BEGIN
    DELETE FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted > 0;
END;
$$;


ALTER FUNCTION activity.sp_remove_organization_member(p_user_id uuid, p_org_id uuid) OWNER TO postgres;

--
-- Name: sp_remove_profile_photo(uuid, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_remove_profile_photo(p_user_id uuid, p_photo_url character varying) RETURNS TABLE(success boolean, photo_count integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_current_photos JSONB;
    v_new_photos JSONB;
    v_photo_count INT;
BEGIN
    -- Get current photos
    SELECT profile_photos_extra INTO v_current_photos
    FROM activity.users
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 0;
        RETURN;
    END IF;

    -- Remove photo from array
    SELECT jsonb_agg(elem)
    INTO v_new_photos
    FROM jsonb_array_elements_text(v_current_photos) elem
    WHERE elem != p_photo_url;

    -- Handle case where all photos were removed
    v_new_photos := COALESCE(v_new_photos, '[]'::jsonb);
    v_photo_count := jsonb_array_length(v_new_photos);

    -- Update photos
    UPDATE activity.users
    SET
        profile_photos_extra = v_new_photos,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE, v_photo_count;
END;
$$;


ALTER FUNCTION activity.sp_remove_profile_photo(p_user_id uuid, p_photo_url character varying) OWNER TO postgres;

--
-- Name: sp_remove_user_interest(uuid, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_remove_user_interest(p_user_id uuid, p_interest_tag character varying) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM activity.user_interests
    WHERE user_id = p_user_id
    AND interest_tag = p_interest_tag;

    RETURN QUERY SELECT TRUE;
END;
$$;


ALTER FUNCTION activity.sp_remove_user_interest(p_user_id uuid, p_interest_tag character varying) OWNER TO postgres;

--
-- Name: sp_revoke_refresh_token(uuid, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_revoke_refresh_token(p_user_id uuid, p_token character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.refresh_tokens
    SET revoked = TRUE
    WHERE user_id = p_user_id AND token = p_token AND revoked = FALSE;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;


ALTER FUNCTION activity.sp_revoke_refresh_token(p_user_id uuid, p_token character varying) OWNER TO postgres;

--
-- Name: sp_save_refresh_token(uuid, character varying, character varying, timestamp without time zone); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_save_refresh_token(p_user_id uuid, p_token character varying, p_jti character varying, p_expires_at timestamp without time zone) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    INSERT INTO activity.refresh_tokens (user_id, token, jti, expires_at)
    VALUES (p_user_id, p_token, p_jti, p_expires_at);

    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;


ALTER FUNCTION activity.sp_save_refresh_token(p_user_id uuid, p_token character varying, p_jti character varying, p_expires_at timestamp without time zone) OWNER TO postgres;

--
-- Name: sp_search_users(text, uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_search_users(p_query text, p_requesting_user_id uuid, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS TABLE(user_id uuid, username character varying, first_name character varying, last_name character varying, main_photo_url character varying, is_verified boolean, verification_count integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id,
        u.username,
        u.first_name,
        u.last_name,
        u.main_photo_url,
        u.is_verified,
        u.verification_count
    FROM activity.users u
    WHERE
        u.status = 'active'
        AND (
            u.username ILIKE '%' || p_query || '%'
            OR u.first_name ILIKE '%' || p_query || '%'
            OR u.last_name ILIKE '%' || p_query || '%'
        )
        -- Exclude blocked users (either direction)
        AND NOT EXISTS (
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = p_requesting_user_id AND blocked_user_id = u.user_id)
            OR (blocker_user_id = u.user_id AND blocked_user_id = p_requesting_user_id)
        )
    ORDER BY u.verification_count DESC, u.username ASC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION activity.sp_search_users(p_query text, p_requesting_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_send_invitations(uuid, uuid, uuid[], text, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_send_invitations(p_activity_id uuid, p_inviting_user_id uuid, p_user_ids uuid[], p_message text DEFAULT NULL::text, p_expires_in_hours integer DEFAULT 72) RETURNS TABLE(success boolean, invited_count integer, failed_count integer, invitations jsonb, failed_invitations jsonb, error_code character varying, error_message text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_activity RECORD;
    v_inviting_participant RECORD;
    v_user_id UUID;
    v_user_exists BOOLEAN;
    v_already_invited BOOLEAN;
    v_already_participant BOOLEAN;
    v_is_blocked BOOLEAN;
    v_invite_count INT := 0;
    v_fail_count INT := 0;
    v_invitations_array JSONB := '[]'::jsonb;
    v_failed_array JSONB := '[]'::jsonb;
    v_new_invitation_id UUID;
    v_expires_at TIMESTAMP WITH TIME ZONE;
BEGIN
    RAISE NOTICE 'sp_send_invitations called: activity_id=%, inviting_user_id=%, user_count=%, expires_in_hours=%',
        p_activity_id, p_inviting_user_id, array_length(p_user_ids, 1), p_expires_in_hours;

    -- Check max invitations
    IF array_length(p_user_ids, 1) > 50 THEN
        RAISE NOTICE 'Too many invitations: count=%', array_length(p_user_ids, 1);
        RETURN QUERY SELECT FALSE, 0, 0, NULL::JSONB, NULL::JSONB,
            'TOO_MANY_INVITATIONS'::VARCHAR(50), 'Maximum 50 invitations per request'::TEXT;
        RETURN;
    END IF;

    -- Get activity details
    SELECT * INTO v_activity
    FROM activity.activities
    WHERE activity_id = p_activity_id;

    IF NOT FOUND THEN
        RAISE NOTICE 'Activity not found: %', p_activity_id;
        RETURN QUERY SELECT FALSE, 0, 0, NULL::JSONB, NULL::JSONB,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity does not exist'::TEXT;
        RETURN;
    END IF;

    -- Check activity is published
    IF v_activity.status != 'published' THEN
        RAISE NOTICE 'Activity not published: status=%', v_activity.status;
        RETURN QUERY SELECT FALSE, 0, 0, NULL::JSONB, NULL::JSONB,
            'ACTIVITY_NOT_FOUND'::VARCHAR(50), 'Activity is not published'::TEXT;
        RETURN;
    END IF;

    -- Check activity is invite_only
    IF v_activity.activity_privacy_level != 'invite_only' THEN
        RAISE NOTICE 'Activity is not invite_only: activity_privacy_level=%', v_activity.activity_privacy_level;
        RETURN QUERY SELECT FALSE, 0, 0, NULL::JSONB, NULL::JSONB,
            'NOT_INVITE_ONLY'::VARCHAR(50), 'Activity is not invite-only'::TEXT;
        RETURN;
    END IF;

    -- Check inviting user is organizer or co-organizer
    SELECT * INTO v_inviting_participant
    FROM activity.participants
    WHERE activity_id = p_activity_id AND user_id = p_inviting_user_id;

    IF NOT FOUND OR (v_inviting_participant.role != 'organizer' AND v_inviting_participant.role != 'co_organizer') THEN
        RAISE NOTICE 'User is not authorized to send invitations: role=%',
            COALESCE(v_inviting_participant.role::TEXT, 'none');
        RETURN QUERY SELECT FALSE, 0, 0, NULL::JSONB, NULL::JSONB,
            'NOT_AUTHORIZED'::VARCHAR(50), 'Only organizer or co-organizer can send invitations'::TEXT;
        RETURN;
    END IF;

    -- Calculate expiry
    v_expires_at := NOW() + (p_expires_in_hours * INTERVAL '1 hour');
    RAISE NOTICE 'Invitations will expire at: %', v_expires_at;

    -- Process each user
    FOREACH v_user_id IN ARRAY p_user_ids
    LOOP
        RAISE NOTICE 'Processing invitation for user: %', v_user_id;

        -- Check user exists
        SELECT EXISTS(SELECT 1 FROM activity.users WHERE user_id = v_user_id) INTO v_user_exists;
        IF NOT v_user_exists THEN
            v_failed_array := v_failed_array || jsonb_build_object(
                'user_id', v_user_id,
                'reason', 'User does not exist'
            );
            v_fail_count := v_fail_count + 1;
            RAISE NOTICE 'User does not exist: %', v_user_id;
            CONTINUE;
        END IF;

        -- Check not already invited
        SELECT EXISTS(
            SELECT 1 FROM activity.activity_invitations
            WHERE activity_id = p_activity_id
              AND user_id = v_user_id
              AND status = 'pending'
        ) INTO v_already_invited;

        IF v_already_invited THEN
            v_failed_array := v_failed_array || jsonb_build_object(
                'user_id', v_user_id,
                'reason', 'Already invited'
            );
            v_fail_count := v_fail_count + 1;
            RAISE NOTICE 'User already invited: %', v_user_id;
            CONTINUE;
        END IF;

        -- Check not already participant
        SELECT EXISTS(
            SELECT 1 FROM activity.participants
            WHERE activity_id = p_activity_id AND user_id = v_user_id
        ) INTO v_already_participant;

        IF v_already_participant THEN
            v_failed_array := v_failed_array || jsonb_build_object(
                'user_id', v_user_id,
                'reason', 'Already a participant'
            );
            v_fail_count := v_fail_count + 1;
            RAISE NOTICE 'User already participant: %', v_user_id;
            CONTINUE;
        END IF;

        -- Check not blocked
        SELECT EXISTS(
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = p_inviting_user_id AND blocked_user_id = v_user_id)
               OR (blocker_user_id = v_user_id AND blocked_user_id = p_inviting_user_id)
        ) INTO v_is_blocked;

        IF v_is_blocked THEN
            v_failed_array := v_failed_array || jsonb_build_object(
                'user_id', v_user_id,
                'reason', 'User is blocked'
            );
            v_fail_count := v_fail_count + 1;
            RAISE NOTICE 'User is blocked: %', v_user_id;
            CONTINUE;
        END IF;

        -- Create invitation
        INSERT INTO activity.activity_invitations (
            activity_id, user_id, invited_by_user_id, message, expires_at
        )
        VALUES (
            p_activity_id, v_user_id, p_inviting_user_id, p_message, v_expires_at
        )
        RETURNING invitation_id INTO v_new_invitation_id;

        v_invitations_array := v_invitations_array || jsonb_build_object(
            'invitation_id', v_new_invitation_id,
            'user_id', v_user_id,
            'status', 'pending',
            'invited_at', NOW(),
            'expires_at', v_expires_at
        );
        v_invite_count := v_invite_count + 1;
        RAISE NOTICE 'Invitation created: invitation_id=%', v_new_invitation_id;
    END LOOP;

    RAISE NOTICE 'Invitations processing complete: invited=%, failed=%', v_invite_count, v_fail_count;

    RETURN QUERY SELECT TRUE, v_invite_count, v_fail_count,
        v_invitations_array, v_failed_array,
        NULL::VARCHAR(50), NULL::TEXT;
    RETURN;
END;
$$;


ALTER FUNCTION activity.sp_send_invitations(p_activity_id uuid, p_inviting_user_id uuid, p_user_ids uuid[], p_message text, p_expires_in_hours integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_send_invitations(p_activity_id uuid, p_inviting_user_id uuid, p_user_ids uuid[], p_message text, p_expires_in_hours integer); Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON FUNCTION activity.sp_send_invitations(p_activity_id uuid, p_inviting_user_id uuid, p_user_ids uuid[], p_message text, p_expires_in_hours integer) IS 'Bulk send invitations with validation and blocking checks';


--
-- Name: sp_set_captain_status(uuid, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_set_captain_status(p_user_id uuid, p_is_captain boolean) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF p_is_captain = TRUE THEN
        -- Grant captain status
        UPDATE activity.users
        SET
            is_captain = TRUE,
            captain_since = NOW(),
            subscription_level = 'premium',
            subscription_expires_at = NOW() + INTERVAL '1 year',
            updated_at = NOW()
        WHERE user_id = p_user_id;
    ELSE
        -- Revoke captain status
        UPDATE activity.users
        SET
            is_captain = FALSE,
            captain_since = NULL,
            subscription_level = 'free',
            subscription_expires_at = NULL,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    END IF;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE;
END;
$$;


ALTER FUNCTION activity.sp_set_captain_status(p_user_id uuid, p_is_captain boolean) OWNER TO postgres;

--
-- Name: sp_set_main_photo(uuid, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_set_main_photo(p_user_id uuid, p_photo_url character varying) RETURNS TABLE(success boolean, moderation_status activity.photo_moderation_status)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Validate URL format
    IF p_photo_url !~ '^https?://' THEN
        RAISE EXCEPTION 'Photo URL must be a valid HTTP/HTTPS URL';
    END IF;

    -- Update main photo and set moderation status to pending
    UPDATE activity.users
    SET
        main_photo_url = p_photo_url,
        main_photo_moderation_status = 'pending',
        updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::activity.photo_moderation_status;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, 'pending'::activity.photo_moderation_status;
END;
$$;


ALTER FUNCTION activity.sp_set_main_photo(p_user_id uuid, p_photo_url character varying) OWNER TO postgres;

--
-- Name: sp_set_user_interests(uuid, jsonb); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_set_user_interests(p_user_id uuid, p_interests jsonb) RETURNS TABLE(success boolean, interest_count integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_interest_count INT;
    v_interest JSONB;
BEGIN
    -- Validate JSONB structure and count
    IF jsonb_typeof(p_interests) != 'array' THEN
        RAISE EXCEPTION 'Interests must be a JSON array';
    END IF;

    v_interest_count := jsonb_array_length(p_interests);

    IF v_interest_count > 20 THEN
        RETURN QUERY SELECT FALSE, v_interest_count;
        RETURN;
    END IF;

    -- Validate each interest object
    FOR v_interest IN SELECT * FROM jsonb_array_elements(p_interests)
    LOOP
        IF NOT (v_interest ? 'tag' AND v_interest ? 'weight') THEN
            RAISE EXCEPTION 'Each interest must have tag and weight fields';
        END IF;

        IF (v_interest->>'weight')::DECIMAL < 0 OR (v_interest->>'weight')::DECIMAL > 1 THEN
            RAISE EXCEPTION 'Interest weight must be between 0.0 and 1.0';
        END IF;
    END LOOP;

    -- Delete existing interests
    DELETE FROM activity.user_interests
    WHERE user_id = p_user_id;

    -- Insert new interests
    INSERT INTO activity.user_interests (user_id, interest_tag, weight)
    SELECT
        p_user_id,
        interest->>'tag',
        (interest->>'weight')::DECIMAL
    FROM jsonb_array_elements(p_interests) AS interest;

    RETURN QUERY SELECT TRUE, v_interest_count;
END;
$$;


ALTER FUNCTION activity.sp_set_user_interests(p_user_id uuid, p_interests jsonb) OWNER TO postgres;

--
-- Name: sp_social_accept_friend_request(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_accept_friend_request(p_accepting_user_id uuid, p_requester_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id_1 UUID;
    v_user_id_2 UUID;
    v_friendship RECORD;
BEGIN
    IF p_accepting_user_id < p_requester_user_id THEN
        v_user_id_1 := p_accepting_user_id;
        v_user_id_2 := p_requester_user_id;
    ELSE
        v_user_id_1 := p_requester_user_id;
        v_user_id_2 := p_accepting_user_id;
    END IF;

    SELECT * INTO v_friendship
    FROM activity.friendships
    WHERE user_id_1 = v_user_id_1
    AND user_id_2 = v_user_id_2
    AND status = 'pending'
    AND initiated_by = p_requester_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'FRIENDSHIP_NOT_FOUND: No pending friend request found';
    END IF;

    IF p_accepting_user_id = p_requester_user_id THEN
        RAISE EXCEPTION 'INVALID_ACCEPTOR: You cannot accept your own friend request';
    END IF;

    UPDATE activity.friendships
    SET status = 'accepted',
        accepted_at = NOW(),
        updated_at = NOW()
    WHERE user_id_1 = v_user_id_1
    AND user_id_2 = v_user_id_2;

    RETURN jsonb_build_object(
        'friendship_id', v_user_id_1::TEXT || ':' || v_user_id_2::TEXT,
        'user_id_1', v_user_id_1,
        'user_id_2', v_user_id_2,
        'status', 'accepted',
        'initiated_by', v_friendship.initiated_by,
        'accepted_at', NOW(),
        'created_at', v_friendship.created_at
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_accept_friend_request(p_accepting_user_id uuid, p_requester_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_block_user(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_block_user(p_blocker_user_id uuid, p_blocked_user_id uuid, p_reason text DEFAULT NULL::text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_exists BOOLEAN;
    v_already_blocked BOOLEAN;
    v_friendship_removed BOOLEAN := FALSE;
BEGIN
    IF p_blocker_user_id = p_blocked_user_id THEN
        RAISE EXCEPTION 'SELF_BLOCK_ERROR: Cannot block yourself';
    END IF;

    SELECT EXISTS(SELECT 1 FROM activity.users WHERE user_id = p_blocked_user_id)
    INTO v_user_exists;

    IF NOT v_user_exists THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: User does not exist';
    END IF;

    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_blocker_user_id
        AND blocked_user_id = p_blocked_user_id
    ) INTO v_already_blocked;

    IF v_already_blocked THEN
        RAISE EXCEPTION 'ALREADY_BLOCKED: User is already blocked';
    END IF;

    INSERT INTO activity.user_blocks (
        blocker_user_id, blocked_user_id, created_at, reason
    ) VALUES (
        p_blocker_user_id, p_blocked_user_id, NOW(), p_reason
    );

    DELETE FROM activity.friendships
    WHERE (user_id_1 = LEAST(p_blocker_user_id, p_blocked_user_id)
       AND user_id_2 = GREATEST(p_blocker_user_id, p_blocked_user_id));

    IF FOUND THEN
        v_friendship_removed := TRUE;
    END IF;

    RETURN jsonb_build_object(
        'blocker_user_id', p_blocker_user_id,
        'blocked_user_id', p_blocked_user_id,
        'blocked_at', NOW(),
        'friendship_removed', v_friendship_removed
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_block_user(p_blocker_user_id uuid, p_blocked_user_id uuid, p_reason text) OWNER TO postgres;

--
-- Name: sp_social_check_block_status(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_check_block_status(p_user_id_1 uuid, p_user_id_2 uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_1_blocked_user_2 BOOLEAN;
    v_user_2_blocked_user_1 BOOLEAN;
    v_any_block_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_user_id_1
        AND blocked_user_id = p_user_id_2
    ) INTO v_user_1_blocked_user_2;

    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_user_id_2
        AND blocked_user_id = p_user_id_1
    ) INTO v_user_2_blocked_user_1;

    v_any_block_exists := v_user_1_blocked_user_2 OR v_user_2_blocked_user_1;

    RETURN jsonb_build_object(
        'user_1_blocked_user_2', v_user_1_blocked_user_2,
        'user_2_blocked_user_1', v_user_2_blocked_user_1,
        'any_block_exists', v_any_block_exists
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_check_block_status(p_user_id_1 uuid, p_user_id_2 uuid) OWNER TO postgres;

--
-- Name: sp_social_check_can_interact(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_check_can_interact(p_user_id_1 uuid, p_user_id_2 uuid, p_activity_type text DEFAULT 'standard'::text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_any_block_exists BOOLEAN;
    v_can_interact BOOLEAN;
    v_reason TEXT;
BEGIN
    -- XXL EXCEPTION: Blocking does NOT apply to XXL activities
    IF p_activity_type = 'xxl' THEN
        RETURN jsonb_build_object(
            'can_interact', TRUE,
            'reason', 'xxl_exception',
            'activity_type', p_activity_type
        );
    END IF;

    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE (blocker_user_id = p_user_id_1 AND blocked_user_id = p_user_id_2)
        OR (blocker_user_id = p_user_id_2 AND blocked_user_id = p_user_id_1)
    ) INTO v_any_block_exists;

    IF v_any_block_exists THEN
        v_can_interact := FALSE;
        v_reason := 'blocked';
    ELSE
        v_can_interact := TRUE;
        v_reason := 'no_blocks';
    END IF;

    RETURN jsonb_build_object(
        'can_interact', v_can_interact,
        'reason', v_reason,
        'activity_type', p_activity_type
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_check_can_interact(p_user_id_1 uuid, p_user_id_2 uuid, p_activity_type text) OWNER TO postgres;

--
-- Name: sp_social_check_favorite_status(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_check_favorite_status(p_favoriting_user_id uuid, p_favorited_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_favorite RECORD;
BEGIN
    SELECT * INTO v_favorite
    FROM activity.user_favorites
    WHERE favoriting_user_id = p_favoriting_user_id
    AND favorited_user_id = p_favorited_user_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('is_favorited', FALSE);
    END IF;

    RETURN jsonb_build_object(
        'is_favorited', TRUE,
        'favorited_at', v_favorite.created_at
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_check_favorite_status(p_favoriting_user_id uuid, p_favorited_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_check_friendship_status(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_check_friendship_status(p_user_id_1 uuid, p_user_id_2 uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id_1 UUID;
    v_user_id_2 UUID;
    v_friendship RECORD;
BEGIN
    IF p_user_id_1 < p_user_id_2 THEN
        v_user_id_1 := p_user_id_1;
        v_user_id_2 := p_user_id_2;
    ELSE
        v_user_id_1 := p_user_id_2;
        v_user_id_2 := p_user_id_1;
    END IF;

    SELECT * INTO v_friendship
    FROM activity.friendships
    WHERE user_id_1 = v_user_id_1
    AND user_id_2 = v_user_id_2;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('status', 'none');
    END IF;

    RETURN jsonb_build_object(
        'status', v_friendship.status,
        'initiated_by', v_friendship.initiated_by,
        'created_at', v_friendship.created_at,
        'accepted_at', v_friendship.accepted_at
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_check_friendship_status(p_user_id_1 uuid, p_user_id_2 uuid) OWNER TO postgres;

--
-- Name: sp_social_decline_friend_request(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_decline_friend_request(p_declining_user_id uuid, p_requester_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id_1 UUID;
    v_user_id_2 UUID;
    v_deleted_count INT;
BEGIN
    IF p_declining_user_id < p_requester_user_id THEN
        v_user_id_1 := p_declining_user_id;
        v_user_id_2 := p_requester_user_id;
    ELSE
        v_user_id_1 := p_requester_user_id;
        v_user_id_2 := p_declining_user_id;
    END IF;

    IF p_declining_user_id = p_requester_user_id THEN
        RAISE EXCEPTION 'INVALID_DECLINER: You cannot decline your own friend request';
    END IF;

    DELETE FROM activity.friendships
    WHERE user_id_1 = v_user_id_1
    AND user_id_2 = v_user_id_2
    AND status = 'pending'
    AND initiated_by = p_requester_user_id;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    IF v_deleted_count = 0 THEN
        RAISE EXCEPTION 'FRIENDSHIP_NOT_FOUND: No pending friend request found';
    END IF;

    RETURN jsonb_build_object(
        'message', 'Friend request declined',
        'requester_user_id', p_requester_user_id,
        'declined_at', NOW()
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_decline_friend_request(p_declining_user_id uuid, p_requester_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_favorite_user(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_favorite_user(p_favoriting_user_id uuid, p_favorited_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_exists BOOLEAN;
    v_already_favorited BOOLEAN;
    v_any_block_exists BOOLEAN;
BEGIN
    -- Validation 1: Cannot favorite yourself
    IF p_favoriting_user_id = p_favorited_user_id THEN
        RAISE EXCEPTION 'SELF_FAVORITE_ERROR: Cannot favorite yourself';
    END IF;

    -- Validation 2: Check favorited user exists
    SELECT EXISTS(SELECT 1 FROM activity.users WHERE user_id = p_favorited_user_id)
    INTO v_user_exists;

    IF NOT v_user_exists THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: User does not exist';
    END IF;

    -- Validation 3: Check not already favorited
    SELECT EXISTS(
        SELECT 1 FROM activity.user_favorites
        WHERE favoriting_user_id = p_favoriting_user_id
        AND favorited_user_id = p_favorited_user_id
    ) INTO v_already_favorited;

    IF v_already_favorited THEN
        RAISE EXCEPTION 'ALREADY_FAVORITED: User is already favorited';
    END IF;

    -- Validation 4: Check for blocks (either direction)
    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE (blocker_user_id = p_favoriting_user_id AND blocked_user_id = p_favorited_user_id)
        OR (blocker_user_id = p_favorited_user_id AND blocked_user_id = p_favoriting_user_id)
    ) INTO v_any_block_exists;

    IF v_any_block_exists THEN
        RAISE EXCEPTION 'BLOCKED_USER: Cannot favorite blocked user';
    END IF;

    -- Insert favorite
    INSERT INTO activity.user_favorites (
        favoriting_user_id, favorited_user_id, created_at
    ) VALUES (
        p_favoriting_user_id, p_favorited_user_id, NOW()
    );

    -- Return success response
    RETURN jsonb_build_object(
        'favoriting_user_id', p_favoriting_user_id,
        'favorited_user_id', p_favorited_user_id,
        'favorited_at', NOW()
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_favorite_user(p_favoriting_user_id uuid, p_favorited_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_get_blocked_users(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_blocked_users(p_blocker_user_id uuid, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_blocked_users JSONB;
    v_total_count INT;
BEGIN
    SELECT COUNT(*)
    INTO v_total_count
    FROM activity.user_blocks
    WHERE blocker_user_id = p_blocker_user_id;

    SELECT COALESCE(jsonb_agg(blocked_user_data), '[]'::jsonb)
    INTO v_blocked_users
    FROM (
        SELECT jsonb_build_object(
            'blocked_user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'blocked_at', b.created_at,
            'reason', b.reason
        ) AS blocked_user_data
        FROM activity.user_blocks b
        JOIN activity.users u ON u.user_id = b.blocked_user_id
        WHERE b.blocker_user_id = p_blocker_user_id
        ORDER BY b.created_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ) blocked;

    RETURN jsonb_build_object(
        'blocked_users', v_blocked_users,
        'total_count', v_total_count,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_blocked_users(p_blocker_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_get_friends_list(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_friends_list(p_user_id uuid, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_friends JSONB;
    v_total_count INT;
BEGIN
    SELECT COUNT(*)
    INTO v_total_count
    FROM activity.friendships f
    WHERE (f.user_id_1 = p_user_id OR f.user_id_2 = p_user_id)
    AND f.status = 'accepted';

    SELECT COALESCE(jsonb_agg(friend_data), '[]'::jsonb)
    INTO v_friends
    FROM (
        SELECT jsonb_build_object(
            'user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'is_verified', u.is_verified,
            'friendship_since', f.accepted_at
        ) AS friend_data
        FROM activity.friendships f
        JOIN activity.users u ON (
            CASE
                WHEN f.user_id_1 = p_user_id THEN u.user_id = f.user_id_2
                ELSE u.user_id = f.user_id_1
            END
        )
        WHERE (f.user_id_1 = p_user_id OR f.user_id_2 = p_user_id)
        AND f.status = 'accepted'
        ORDER BY f.accepted_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ) friends;

    RETURN jsonb_build_object(
        'friends', v_friends,
        'total_count', v_total_count,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_friends_list(p_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_get_my_favorites(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_my_favorites(p_user_id uuid, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_favorites JSONB;
    v_total_count INT;
BEGIN
    SELECT COUNT(*)
    INTO v_total_count
    FROM activity.user_favorites
    WHERE favoriting_user_id = p_user_id;

    SELECT COALESCE(jsonb_agg(favorite_data), '[]'::jsonb)
    INTO v_favorites
    FROM (
        SELECT jsonb_build_object(
            'user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'is_verified', u.is_verified,
            'favorited_at', f.created_at
        ) AS favorite_data
        FROM activity.user_favorites f
        JOIN activity.users u ON u.user_id = f.favorited_user_id
        WHERE f.favoriting_user_id = p_user_id
        ORDER BY f.created_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ) favorites;

    RETURN jsonb_build_object(
        'favorites', v_favorites,
        'total_count', v_total_count,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_my_favorites(p_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_get_pending_friend_requests(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_pending_friend_requests(p_user_id uuid, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_requests JSONB;
    v_total_count INT;
BEGIN
    SELECT COUNT(*)
    INTO v_total_count
    FROM activity.friendships f
    WHERE (f.user_id_1 = p_user_id OR f.user_id_2 = p_user_id)
    AND f.status = 'pending'
    AND f.initiated_by != p_user_id;

    SELECT COALESCE(jsonb_agg(request_data), '[]'::jsonb)
    INTO v_requests
    FROM (
        SELECT jsonb_build_object(
            'requester_user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'is_verified', u.is_verified,
            'requested_at', f.created_at
        ) AS request_data
        FROM activity.friendships f
        JOIN activity.users u ON u.user_id = f.initiated_by
        WHERE (f.user_id_1 = p_user_id OR f.user_id_2 = p_user_id)
        AND f.status = 'pending'
        AND f.initiated_by != p_user_id
        ORDER BY f.created_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ) requests;

    RETURN jsonb_build_object(
        'requests', v_requests,
        'total_count', v_total_count,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_pending_friend_requests(p_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_get_profile_view_count(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_profile_view_count(p_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_total_views INT;
    v_unique_viewers INT;
BEGIN
    -- Get total views
    SELECT COUNT(*)
    INTO v_total_views
    FROM activity.profile_views
    WHERE viewed_user_id = p_user_id;

    -- Get unique viewers
    SELECT COUNT(DISTINCT viewer_user_id)
    INTO v_unique_viewers
    FROM activity.profile_views
    WHERE viewed_user_id = p_user_id;

    RETURN jsonb_build_object(
        'user_id', p_user_id,
        'total_views', v_total_views,
        'unique_viewers', v_unique_viewers
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_profile_view_count(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_get_sent_friend_requests(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_sent_friend_requests(p_user_id uuid, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_requests JSONB;
    v_total_count INT;
BEGIN
    SELECT COUNT(*)
    INTO v_total_count
    FROM activity.friendships f
    WHERE f.status = 'pending'
    AND f.initiated_by = p_user_id;

    SELECT COALESCE(jsonb_agg(request_data), '[]'::jsonb)
    INTO v_requests
    FROM (
        SELECT jsonb_build_object(
            'target_user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'is_verified', u.is_verified,
            'requested_at', f.created_at
        ) AS request_data
        FROM activity.friendships f
        JOIN activity.users u ON (
            CASE
                WHEN f.user_id_1 = p_user_id THEN u.user_id = f.user_id_2
                ELSE u.user_id = f.user_id_1
            END
        )
        WHERE f.status = 'pending'
        AND f.initiated_by = p_user_id
        ORDER BY f.created_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ) requests;

    RETURN jsonb_build_object(
        'requests', v_requests,
        'total_count', v_total_count,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_sent_friend_requests(p_user_id uuid, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_get_who_favorited_me(uuid, text, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_who_favorited_me(p_user_id uuid, p_subscription_level text, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_favorited_by JSONB;
    v_total_count INT;
BEGIN
    -- Premium check
    IF p_subscription_level NOT IN ('premium', 'club') THEN
        RAISE EXCEPTION 'PREMIUM_REQUIRED: This feature requires Premium or Club subscription';
    END IF;

    SELECT COUNT(*)
    INTO v_total_count
    FROM activity.user_favorites
    WHERE favorited_user_id = p_user_id;

    SELECT COALESCE(jsonb_agg(favoriter_data), '[]'::jsonb)
    INTO v_favorited_by
    FROM (
        SELECT jsonb_build_object(
            'user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'is_verified', u.is_verified,
            'favorited_at', f.created_at
        ) AS favoriter_data
        FROM activity.user_favorites f
        JOIN activity.users u ON u.user_id = f.favoriting_user_id
        WHERE f.favorited_user_id = p_user_id
        ORDER BY f.created_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ) favoriters;

    RETURN jsonb_build_object(
        'favorited_by', v_favorited_by,
        'total_count', v_total_count,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_who_favorited_me(p_user_id uuid, p_subscription_level text, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_get_who_viewed_my_profile(uuid, text, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_get_who_viewed_my_profile(p_user_id uuid, p_subscription_level text, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_viewers JSONB;
    v_total_viewers INT;
    v_total_views INT;
BEGIN
    -- Premium check
    IF p_subscription_level NOT IN ('premium', 'club') THEN
        RAISE EXCEPTION 'PREMIUM_REQUIRED: This feature requires Premium or Club subscription';
    END IF;

    -- Get total views count
    SELECT COUNT(*)
    INTO v_total_views
    FROM activity.profile_views
    WHERE viewed_user_id = p_user_id;

    -- Get unique viewers count
    SELECT COUNT(DISTINCT viewer_user_id)
    INTO v_total_viewers
    FROM activity.profile_views
    WHERE viewed_user_id = p_user_id;

    -- Get viewers with aggregated data
    SELECT COALESCE(jsonb_agg(viewer_data), '[]'::jsonb)
    INTO v_viewers
    FROM (
        SELECT jsonb_build_object(
            'viewer_user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'is_verified', u.is_verified,
            'last_viewed_at', MAX(pv.viewed_at),
            'view_count', COUNT(pv.view_id)
        ) AS viewer_data
        FROM activity.profile_views pv
        JOIN activity.users u ON u.user_id = pv.viewer_user_id
        WHERE pv.viewed_user_id = p_user_id
        GROUP BY u.user_id, u.username, u.first_name, u.last_name,
                 u.main_photo_url, u.is_verified
        ORDER BY MAX(pv.viewed_at) DESC
        LIMIT p_limit
        OFFSET p_offset
    ) viewers;

    RETURN jsonb_build_object(
        'viewers', v_viewers,
        'total_viewers', v_total_viewers,
        'total_views', v_total_views,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_get_who_viewed_my_profile(p_user_id uuid, p_subscription_level text, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_record_profile_view(uuid, uuid, boolean); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_record_profile_view(p_viewer_user_id uuid, p_viewed_user_id uuid, p_ghost_mode boolean) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_exists BOOLEAN;
    v_any_block_exists BOOLEAN;
    v_view_id UUID;
BEGIN
    -- Validation 1: Cannot view your own profile
    IF p_viewer_user_id = p_viewed_user_id THEN
        RAISE EXCEPTION 'SELF_VIEW_ERROR: Cannot record self-profile view';
    END IF;

    -- Validation 2: Check viewed user exists
    SELECT EXISTS(SELECT 1 FROM activity.users WHERE user_id = p_viewed_user_id)
    INTO v_user_exists;

    IF NOT v_user_exists THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: User does not exist';
    END IF;

    -- Validation 3: Check for blocks (either direction)
    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE (blocker_user_id = p_viewer_user_id AND blocked_user_id = p_viewed_user_id)
        OR (blocker_user_id = p_viewed_user_id AND blocked_user_id = p_viewer_user_id)
    ) INTO v_any_block_exists;

    IF v_any_block_exists THEN
        RAISE EXCEPTION 'BLOCKED_USER: Cannot view blocked user profile';
    END IF;

    -- Ghost Mode: Return without recording
    IF p_ghost_mode = TRUE THEN
        RETURN jsonb_build_object(
            'view_recorded', FALSE,
            'ghost_mode', TRUE,
            'viewed_user_id', p_viewed_user_id
        );
    END IF;

    -- Normal Mode: Record the view
    v_view_id := gen_random_uuid();

    INSERT INTO activity.profile_views (
        view_id, viewer_user_id, viewed_user_id, viewed_at
    ) VALUES (
        v_view_id, p_viewer_user_id, p_viewed_user_id, NOW()
    );

    RETURN jsonb_build_object(
        'view_recorded', TRUE,
        'view_id', v_view_id,
        'viewer_user_id', p_viewer_user_id,
        'viewed_user_id', p_viewed_user_id,
        'viewed_at', NOW()
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_record_profile_view(p_viewer_user_id uuid, p_viewed_user_id uuid, p_ghost_mode boolean) OWNER TO postgres;

--
-- Name: sp_social_remove_friend(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_remove_friend(p_user_id uuid, p_friend_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id_1 UUID;
    v_user_id_2 UUID;
    v_deleted_count INT;
BEGIN
    IF p_user_id < p_friend_user_id THEN
        v_user_id_1 := p_user_id;
        v_user_id_2 := p_friend_user_id;
    ELSE
        v_user_id_1 := p_friend_user_id;
        v_user_id_2 := p_user_id;
    END IF;

    DELETE FROM activity.friendships
    WHERE user_id_1 = v_user_id_1
    AND user_id_2 = v_user_id_2;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    IF v_deleted_count = 0 THEN
        RAISE EXCEPTION 'FRIENDSHIP_NOT_FOUND: No friendship found with this user';
    END IF;

    RETURN jsonb_build_object(
        'message', 'Friendship removed',
        'removed_user_id', p_friend_user_id,
        'removed_at', NOW()
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_remove_friend(p_user_id uuid, p_friend_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_search_users(uuid, text, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_search_users(p_searcher_user_id uuid, p_search_query text, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_users JSONB;
    v_total_count INT;
    v_search_pattern TEXT;
BEGIN
    -- Validation: Query must be at least 2 characters
    IF LENGTH(TRIM(p_search_query)) < 2 THEN
        RAISE EXCEPTION 'INVALID_QUERY: Search query must be at least 2 characters';
    END IF;

    v_search_pattern := '%' || LOWER(TRIM(p_search_query)) || '%';

    -- Get total count of matching users
    SELECT COUNT(*)
    INTO v_total_count
    FROM activity.users u
    WHERE (
        LOWER(u.username) LIKE v_search_pattern
        OR LOWER(u.first_name) LIKE v_search_pattern
        OR LOWER(u.last_name) LIKE v_search_pattern
        OR LOWER(CONCAT(u.first_name, ' ', u.last_name)) LIKE v_search_pattern
    )
    AND u.user_id != p_searcher_user_id
    AND NOT EXISTS (
        SELECT 1 FROM activity.user_blocks
        WHERE (blocker_user_id = p_searcher_user_id AND blocked_user_id = u.user_id)
        OR (blocker_user_id = u.user_id AND blocked_user_id = p_searcher_user_id)
    );

    -- Get matching users with details
    SELECT COALESCE(jsonb_agg(user_data), '[]'::jsonb)
    INTO v_users
    FROM (
        SELECT jsonb_build_object(
            'user_id', u.user_id,
            'username', u.username,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'main_photo_url', u.main_photo_url,
            'is_verified', u.is_verified,
            'activities_created_count', COALESCE(u.activities_created_count, 0),
            'activities_attended_count', COALESCE(u.activities_attended_count, 0)
        ) AS user_data
        FROM activity.users u
        WHERE (
            LOWER(u.username) LIKE v_search_pattern
            OR LOWER(u.first_name) LIKE v_search_pattern
            OR LOWER(u.last_name) LIKE v_search_pattern
            OR LOWER(CONCAT(u.first_name, ' ', u.last_name)) LIKE v_search_pattern
        )
        AND u.user_id != p_searcher_user_id
        AND NOT EXISTS (
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = p_searcher_user_id AND blocked_user_id = u.user_id)
            OR (blocker_user_id = u.user_id AND blocked_user_id = p_searcher_user_id)
        )
        ORDER BY
            u.is_verified DESC,
            CASE
                WHEN LOWER(u.username) = LOWER(TRIM(p_search_query)) THEN 1
                WHEN LOWER(u.first_name) = LOWER(TRIM(p_search_query)) THEN 2
                WHEN LOWER(u.last_name) = LOWER(TRIM(p_search_query)) THEN 3
                ELSE 4
            END,
            u.username ASC
        LIMIT p_limit
        OFFSET p_offset
    ) users;

    RETURN jsonb_build_object(
        'users', v_users,
        'total_count', v_total_count,
        'search_query', p_search_query,
        'limit', p_limit,
        'offset', p_offset
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_search_users(p_searcher_user_id uuid, p_search_query text, p_limit integer, p_offset integer) OWNER TO postgres;

--
-- Name: sp_social_send_friend_request(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_send_friend_request(p_requester_user_id uuid, p_target_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id_1 UUID;
    v_user_id_2 UUID;
    v_target_exists BOOLEAN;
    v_friendship_exists BOOLEAN;
    v_existing_status TEXT;
    v_is_blocked BOOLEAN;
    v_has_blocked BOOLEAN;
BEGIN
    -- Validation 1: Cannot friend yourself
    IF p_requester_user_id = p_target_user_id THEN
        RAISE EXCEPTION 'SELF_FRIEND_ERROR: Cannot send friend request to yourself';
    END IF;

    -- Validation 2: Check target user exists
    SELECT EXISTS(SELECT 1 FROM activity.users WHERE user_id = p_target_user_id)
    INTO v_target_exists;

    IF NOT v_target_exists THEN
        RAISE EXCEPTION 'USER_NOT_FOUND: Target user does not exist';
    END IF;

    -- Validation 3: Check for existing friendship
    IF p_requester_user_id < p_target_user_id THEN
        v_user_id_1 := p_requester_user_id;
        v_user_id_2 := p_target_user_id;
    ELSE
        v_user_id_1 := p_target_user_id;
        v_user_id_2 := p_requester_user_id;
    END IF;

    SELECT EXISTS(
        SELECT 1 FROM activity.friendships
        WHERE user_id_1 = v_user_id_1 AND user_id_2 = v_user_id_2
    ), status
    INTO v_friendship_exists, v_existing_status
    FROM activity.friendships
    WHERE user_id_1 = v_user_id_1 AND user_id_2 = v_user_id_2;

    IF v_friendship_exists THEN
        RAISE EXCEPTION 'FRIENDSHIP_EXISTS: Friendship already exists with status: %', v_existing_status;
    END IF;

    -- Validation 4: Check if requester is blocked by target
    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_target_user_id
        AND blocked_user_id = p_requester_user_id
    ) INTO v_is_blocked;

    IF v_is_blocked THEN
        RAISE EXCEPTION 'BLOCKED_BY_USER: You cannot send friend request to this user';
    END IF;

    -- Validation 5: Check if requester has blocked target
    SELECT EXISTS(
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_requester_user_id
        AND blocked_user_id = p_target_user_id
    ) INTO v_has_blocked;

    IF v_has_blocked THEN
        RAISE EXCEPTION 'USER_BLOCKED: Cannot send friend request to blocked user';
    END IF;

    -- Insert friendship
    INSERT INTO activity.friendships (
        user_id_1, user_id_2, status, initiated_by, created_at
    ) VALUES (
        v_user_id_1, v_user_id_2, 'pending', p_requester_user_id, NOW()
    );

    -- Return success response
    RETURN jsonb_build_object(
        'friendship_id', v_user_id_1::TEXT || ':' || v_user_id_2::TEXT,
        'requester_user_id', p_requester_user_id,
        'target_user_id', p_target_user_id,
        'status', 'pending',
        'initiated_by', p_requester_user_id,
        'created_at', NOW()
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_send_friend_request(p_requester_user_id uuid, p_target_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_unblock_user(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_unblock_user(p_blocker_user_id uuid, p_blocked_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_deleted_count INT;
BEGIN
    DELETE FROM activity.user_blocks
    WHERE blocker_user_id = p_blocker_user_id
    AND blocked_user_id = p_blocked_user_id;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    IF v_deleted_count = 0 THEN
        RAISE EXCEPTION 'BLOCK_NOT_FOUND: No block found for this user';
    END IF;

    RETURN jsonb_build_object(
        'blocker_user_id', p_blocker_user_id,
        'unblocked_user_id', p_blocked_user_id,
        'unblocked_at', NOW()
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_unblock_user(p_blocker_user_id uuid, p_blocked_user_id uuid) OWNER TO postgres;

--
-- Name: sp_social_unfavorite_user(uuid, uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_social_unfavorite_user(p_favoriting_user_id uuid, p_favorited_user_id uuid) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_deleted_count INT;
BEGIN
    DELETE FROM activity.user_favorites
    WHERE favoriting_user_id = p_favoriting_user_id
    AND favorited_user_id = p_favorited_user_id;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    IF v_deleted_count = 0 THEN
        RAISE EXCEPTION 'FAVORITE_NOT_FOUND: Favorite not found';
    END IF;

    RETURN jsonb_build_object(
        'favoriting_user_id', p_favoriting_user_id,
        'unfavorited_user_id', p_favorited_user_id,
        'unfavorited_at', NOW()
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE;
END;
$$;


ALTER FUNCTION activity.sp_social_unfavorite_user(p_favoriting_user_id uuid, p_favorited_user_id uuid) OWNER TO postgres;

--
-- Name: sp_unban_user(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_unban_user(p_user_id uuid) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE activity.users
    SET
        status = 'active',
        ban_reason = NULL,
        ban_expires_at = NULL,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT FOUND;
END;
$$;


ALTER FUNCTION activity.sp_unban_user(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_update_activity_counts(uuid, integer, integer); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_activity_counts(p_user_id uuid, p_created_delta integer, p_attended_delta integer) RETURNS TABLE(new_created_count integer, new_attended_count integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_new_created INT;
    v_new_attended INT;
BEGIN
    UPDATE activity.users
    SET
        activities_created_count = GREATEST(0, activities_created_count + p_created_delta),
        activities_attended_count = GREATEST(0, activities_attended_count + p_attended_delta),
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING activities_created_count, activities_attended_count
    INTO v_new_created, v_new_attended;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    -- Verify counts didn't go negative
    IF v_new_created < 0 OR v_new_attended < 0 THEN
        RAISE EXCEPTION 'Activity counts cannot be negative';
    END IF;

    RETURN QUERY SELECT v_new_created, v_new_attended;
END;
$$;


ALTER FUNCTION activity.sp_update_activity_counts(p_user_id uuid, p_created_delta integer, p_attended_delta integer) OWNER TO postgres;

--
-- Name: sp_update_last_login(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_last_login(p_user_id uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE activity.users SET last_login_at = NOW() WHERE user_id = p_user_id;
END;
$$;


ALTER FUNCTION activity.sp_update_last_login(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_update_last_seen(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_last_seen(p_user_id uuid) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE activity.users
    SET last_seen_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT FOUND;
END;
$$;


ALTER FUNCTION activity.sp_update_last_seen(p_user_id uuid) OWNER TO postgres;

--
-- Name: sp_update_member_role(uuid, uuid, text); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_member_role(p_user_id uuid, p_org_id uuid, p_new_role text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_updated BOOLEAN;
BEGIN
    UPDATE activity.organization_members
    SET role = p_new_role
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated > 0;
END;
$$;


ALTER FUNCTION activity.sp_update_member_role(p_user_id uuid, p_org_id uuid, p_new_role text) OWNER TO postgres;

--
-- Name: sp_update_notification_settings(uuid, boolean, boolean, boolean, jsonb, time without time zone, time without time zone); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_notification_settings(p_user_id uuid, p_email_enabled boolean DEFAULT NULL::boolean, p_push_enabled boolean DEFAULT NULL::boolean, p_in_app_enabled boolean DEFAULT NULL::boolean, p_enabled_types jsonb DEFAULT NULL::jsonb, p_quiet_hours_start time without time zone DEFAULT NULL::time without time zone, p_quiet_hours_end time without time zone DEFAULT NULL::time without time zone) RETURNS TABLE(email_enabled boolean, push_enabled boolean, in_app_enabled boolean, enabled_types jsonb, quiet_hours_start time without time zone, quiet_hours_end time without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Ensure preferences exist
    INSERT INTO activity.notification_preferences (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING;

    -- Update only provided fields
    UPDATE activity.notification_preferences
    SET
        email_enabled = COALESCE(p_email_enabled, email_enabled),
        push_enabled = COALESCE(p_push_enabled, push_enabled),
        in_app_enabled = COALESCE(p_in_app_enabled, in_app_enabled),
        enabled_types = COALESCE(p_enabled_types, enabled_types),
        quiet_hours_start = COALESCE(p_quiet_hours_start, quiet_hours_start),
        quiet_hours_end = COALESCE(p_quiet_hours_end, quiet_hours_end),
        updated_at = NOW()
    WHERE user_id = p_user_id;

    -- Return updated settings
    RETURN QUERY
    SELECT
        np.email_enabled,
        np.push_enabled,
        np.in_app_enabled,
        np.enabled_types,
        np.quiet_hours_start,
        np.quiet_hours_end
    FROM activity.notification_preferences np
    WHERE np.user_id = p_user_id;
END;
$$;


ALTER FUNCTION activity.sp_update_notification_settings(p_user_id uuid, p_email_enabled boolean, p_push_enabled boolean, p_in_app_enabled boolean, p_enabled_types jsonb, p_quiet_hours_start time without time zone, p_quiet_hours_end time without time zone) OWNER TO postgres;

--
-- Name: sp_update_password(uuid, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_password(p_user_id uuid, p_new_hashed_password character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users SET password_hash = p_new_hashed_password WHERE user_id = p_user_id;
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;


ALTER FUNCTION activity.sp_update_password(p_user_id uuid, p_new_hashed_password character varying) OWNER TO postgres;

--
-- Name: sp_update_subscription(uuid, activity.subscription_level, timestamp with time zone); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_subscription(p_user_id uuid, p_subscription_level activity.subscription_level, p_subscription_expires_at timestamp with time zone DEFAULT NULL::timestamp with time zone) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Validate: free requires NULL expiry, club/premium require expiry
    IF p_subscription_level = 'free' AND p_subscription_expires_at IS NOT NULL THEN
        RAISE EXCEPTION 'Free subscription cannot have expiry date';
    END IF;

    IF p_subscription_level IN ('club', 'premium') AND p_subscription_expires_at IS NULL THEN
        RAISE EXCEPTION 'Club and Premium subscriptions must have expiry date';
    END IF;

    -- Update subscription
    UPDATE activity.users
    SET
        subscription_level = p_subscription_level,
        subscription_expires_at = p_subscription_expires_at,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE;
        RETURN;
    END IF;

    -- If downgrading from premium, disable ghost_mode
    IF p_subscription_level != 'premium' THEN
        UPDATE activity.user_settings
        SET ghost_mode = FALSE, updated_at = NOW()
        WHERE user_id = p_user_id AND ghost_mode = TRUE;
    END IF;

    RETURN QUERY SELECT TRUE;
END;
$$;


ALTER FUNCTION activity.sp_update_subscription(p_user_id uuid, p_subscription_level activity.subscription_level, p_subscription_expires_at timestamp with time zone) OWNER TO postgres;

--
-- Name: sp_update_user_profile(uuid, character varying, character varying, text, date, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_user_profile(p_user_id uuid, p_first_name character varying DEFAULT NULL::character varying, p_last_name character varying DEFAULT NULL::character varying, p_profile_description text DEFAULT NULL::text, p_date_of_birth date DEFAULT NULL::date, p_gender character varying DEFAULT NULL::character varying) RETURNS TABLE(success boolean, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_status activity.user_status;
BEGIN
    -- Check user exists and get status
    SELECT status INTO v_user_status
    FROM activity.users
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::TIMESTAMP WITH TIME ZONE;
        RETURN;
    END IF;

    -- Check user is not banned
    IF v_user_status = 'banned' THEN
        RAISE EXCEPTION 'User is banned and cannot update profile';
    END IF;

    -- Validate date_of_birth (must not be in future, must be 18+ years old)
    IF p_date_of_birth IS NOT NULL THEN
        IF p_date_of_birth >= CURRENT_DATE THEN
            RAISE EXCEPTION 'Date of birth cannot be in the future';
        END IF;
        IF p_date_of_birth > CURRENT_DATE - INTERVAL '18 years' THEN
            RAISE EXCEPTION 'User must be at least 18 years old';
        END IF;
    END IF;

    -- Update only non-NULL fields
    UPDATE activity.users
    SET
        first_name = COALESCE(p_first_name, first_name),
        last_name = COALESCE(p_last_name, last_name),
        profile_description = COALESCE(p_profile_description, profile_description),
        date_of_birth = COALESCE(p_date_of_birth, date_of_birth),
        gender = COALESCE(p_gender, gender),
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE, NOW();
END;
$$;


ALTER FUNCTION activity.sp_update_user_profile(p_user_id uuid, p_first_name character varying, p_last_name character varying, p_profile_description text, p_date_of_birth date, p_gender character varying) OWNER TO postgres;

--
-- Name: sp_update_user_settings(uuid, boolean, boolean, boolean, boolean, boolean, boolean, boolean, character varying, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_user_settings(p_user_id uuid, p_email_notifications boolean DEFAULT NULL::boolean, p_push_notifications boolean DEFAULT NULL::boolean, p_activity_reminders boolean DEFAULT NULL::boolean, p_community_updates boolean DEFAULT NULL::boolean, p_friend_requests boolean DEFAULT NULL::boolean, p_marketing_emails boolean DEFAULT NULL::boolean, p_ghost_mode boolean DEFAULT NULL::boolean, p_language character varying DEFAULT NULL::character varying, p_timezone character varying DEFAULT NULL::character varying) RETURNS TABLE(success boolean)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_subscription_level activity.subscription_level;
BEGIN
    -- Create settings if not exists
    INSERT INTO activity.user_settings (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING;

    -- Check subscription level for ghost_mode
    IF p_ghost_mode = TRUE THEN
        SELECT subscription_level INTO v_subscription_level
        FROM activity.users
        WHERE user_id = p_user_id;

        IF v_subscription_level != 'premium' THEN
            RAISE EXCEPTION 'Ghost mode requires Premium subscription';
        END IF;
    END IF;

    -- Update only non-NULL fields
    UPDATE activity.user_settings
    SET
        email_notifications = COALESCE(p_email_notifications, email_notifications),
        push_notifications = COALESCE(p_push_notifications, push_notifications),
        activity_reminders = COALESCE(p_activity_reminders, activity_reminders),
        community_updates = COALESCE(p_community_updates, community_updates),
        friend_requests = COALESCE(p_friend_requests, friend_requests),
        marketing_emails = COALESCE(p_marketing_emails, marketing_emails),
        ghost_mode = COALESCE(p_ghost_mode, ghost_mode),
        language = COALESCE(p_language, language),
        timezone = COALESCE(p_timezone, timezone),
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE;
END;
$$;


ALTER FUNCTION activity.sp_update_user_settings(p_user_id uuid, p_email_notifications boolean, p_push_notifications boolean, p_activity_reminders boolean, p_community_updates boolean, p_friend_requests boolean, p_marketing_emails boolean, p_ghost_mode boolean, p_language character varying, p_timezone character varying) OWNER TO postgres;

--
-- Name: sp_update_username(uuid, character varying); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_update_username(p_user_id uuid, p_new_username character varying) RETURNS TABLE(success boolean, message text)
    LANGUAGE plpgsql
    AS $_$
DECLARE
    v_username_exists BOOLEAN;
BEGIN
    -- Validate username format (alphanumeric + underscore, 3-30 chars)
    IF NOT p_new_username ~ '^[a-zA-Z0-9_]{3,30}$' THEN
        RAISE EXCEPTION 'Username must be 3-30 characters and contain only letters, numbers, and underscores';
    END IF;

    -- Check uniqueness (case insensitive)
    SELECT EXISTS (
        SELECT 1 FROM activity.users
        WHERE LOWER(username) = LOWER(p_new_username)
        AND user_id != p_user_id
    ) INTO v_username_exists;

    IF v_username_exists THEN
        RETURN QUERY SELECT FALSE, 'Username already taken'::TEXT;
        RETURN;
    END IF;

    -- Update username
    UPDATE activity.users
    SET username = p_new_username, updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'User not found'::TEXT;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, 'Username updated successfully'::TEXT;
END;
$_$;


ALTER FUNCTION activity.sp_update_username(p_user_id uuid, p_new_username character varying) OWNER TO postgres;

--
-- Name: sp_verify_user_email(uuid); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.sp_verify_user_email(p_user_id uuid) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users SET is_verified = TRUE WHERE user_id = p_user_id;
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;


ALTER FUNCTION activity.sp_verify_user_email(p_user_id uuid) OWNER TO postgres;

--
-- Name: update_organizations_updated_at(); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.update_organizations_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION activity.update_organizations_updated_at() OWNER TO postgres;

--
-- Name: update_timestamp(); Type: FUNCTION; Schema: activity; Owner: postgres
--

CREATE FUNCTION activity.update_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION activity.update_timestamp() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activities; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.activities (
    activity_id uuid DEFAULT public.uuidv7() NOT NULL,
    organizer_user_id uuid NOT NULL,
    category_id uuid,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    activity_type activity.activity_type DEFAULT 'standard'::activity.activity_type NOT NULL,
    activity_privacy_level activity.activity_privacy_level DEFAULT 'public'::activity.activity_privacy_level NOT NULL,
    status activity.activity_status DEFAULT 'published'::activity.activity_status NOT NULL,
    scheduled_at timestamp with time zone NOT NULL,
    duration_minutes integer,
    joinable_at_free timestamp with time zone,
    max_participants integer NOT NULL,
    current_participants_count integer DEFAULT 0 NOT NULL,
    waitlist_count integer DEFAULT 0 NOT NULL,
    location_name character varying(255),
    city character varying(100),
    language character varying(5) DEFAULT 'en'::character varying NOT NULL,
    external_chat_id character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_duration CHECK (((duration_minutes IS NULL) OR (duration_minutes > 0))),
    CONSTRAINT check_joinable_time CHECK (((joinable_at_free IS NULL) OR (joinable_at_free >= created_at))),
    CONSTRAINT check_max_participants CHECK ((max_participants > 0)),
    CONSTRAINT check_participants_count CHECK (((current_participants_count >= 0) AND (current_participants_count <= max_participants))),
    CONSTRAINT check_scheduled_time CHECK ((scheduled_at > created_at)),
    CONSTRAINT check_waitlist_count CHECK ((waitlist_count >= 0))
);


ALTER TABLE activity.activities OWNER TO postgres;

--
-- Name: activity_invitations; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.activity_invitations (
    invitation_id uuid DEFAULT public.uuidv7() NOT NULL,
    activity_id uuid NOT NULL,
    user_id uuid NOT NULL,
    invited_by_user_id uuid NOT NULL,
    status activity.invitation_status DEFAULT 'pending'::activity.invitation_status NOT NULL,
    invited_at timestamp with time zone DEFAULT now() NOT NULL,
    responded_at timestamp with time zone,
    expires_at timestamp with time zone,
    message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_invitation_dates CHECK (((expires_at IS NULL) OR (expires_at > invited_at)))
);


ALTER TABLE activity.activity_invitations OWNER TO postgres;

--
-- Name: activity_locations; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.activity_locations (
    location_id uuid DEFAULT public.uuidv7() NOT NULL,
    activity_id uuid NOT NULL,
    venue_name character varying(255),
    address_line1 character varying(255),
    address_line2 character varying(255),
    city character varying(100),
    state_province character varying(100),
    postal_code character varying(20),
    country character varying(100),
    latitude numeric(10,8),
    longitude numeric(11,8),
    place_id character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_coordinates CHECK ((((latitude IS NULL) AND (longitude IS NULL)) OR ((latitude IS NOT NULL) AND (longitude IS NOT NULL) AND (latitude >= ('-90'::integer)::numeric) AND (latitude <= (90)::numeric) AND (longitude >= ('-180'::integer)::numeric) AND (longitude <= (180)::numeric))))
);


ALTER TABLE activity.activity_locations OWNER TO postgres;

--
-- Name: activity_reviews; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.activity_reviews (
    review_id uuid DEFAULT public.uuidv7() NOT NULL,
    activity_id uuid NOT NULL,
    reviewer_user_id uuid NOT NULL,
    rating integer NOT NULL,
    review_text text,
    is_anonymous boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_rating_range CHECK (((rating >= 1) AND (rating <= 5)))
);


ALTER TABLE activity.activity_reviews OWNER TO postgres;

--
-- Name: activity_tags; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.activity_tags (
    activity_id uuid NOT NULL,
    tag character varying(100) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE activity.activity_tags OWNER TO postgres;

--
-- Name: attendance_confirmations; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.attendance_confirmations (
    confirmation_id uuid DEFAULT public.uuidv7() NOT NULL,
    activity_id uuid NOT NULL,
    confirmed_user_id uuid NOT NULL,
    confirmer_user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    CONSTRAINT check_not_self_confirm CHECK ((confirmed_user_id <> confirmer_user_id))
);


ALTER TABLE activity.attendance_confirmations OWNER TO postgres;

--
-- Name: categories; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.categories (
    category_id uuid DEFAULT public.uuidv7() NOT NULL,
    name character varying(100) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    icon_url character varying(500),
    display_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    CONSTRAINT check_slug_format CHECK (((slug)::text ~ '^[a-z0-9-]+$'::text))
);


ALTER TABLE activity.categories OWNER TO postgres;

--
-- Name: comments; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.comments (
    comment_id uuid DEFAULT public.uuidv7() NOT NULL,
    post_id uuid NOT NULL,
    parent_comment_id uuid,
    author_user_id uuid NOT NULL,
    content text NOT NULL,
    reaction_count integer DEFAULT 0 NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_reaction_count_positive CHECK ((reaction_count >= 0))
);


ALTER TABLE activity.comments OWNER TO postgres;

--
-- Name: communities; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.communities (
    community_id uuid DEFAULT public.uuidv7() NOT NULL,
    organization_id uuid,
    creator_user_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    community_type activity.community_type DEFAULT 'open'::activity.community_type NOT NULL,
    status activity.community_status DEFAULT 'active'::activity.community_status NOT NULL,
    member_count integer DEFAULT 0 NOT NULL,
    max_members integer,
    is_featured boolean DEFAULT false NOT NULL,
    cover_image_url character varying(500),
    icon_url character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_max_members CHECK (((max_members IS NULL) OR (max_members > 0))),
    CONSTRAINT check_member_count CHECK ((member_count >= 0))
);


ALTER TABLE activity.communities OWNER TO postgres;

--
-- Name: community_activities; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.community_activities (
    community_id uuid NOT NULL,
    activity_id uuid NOT NULL,
    is_pinned boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64)
);


ALTER TABLE activity.community_activities OWNER TO postgres;

--
-- Name: community_members; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.community_members (
    community_id uuid NOT NULL,
    user_id uuid NOT NULL,
    status activity.membership_status DEFAULT 'active'::activity.membership_status NOT NULL,
    role activity.participant_role DEFAULT 'member'::activity.participant_role NOT NULL,
    invited_by_user_id uuid,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    left_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64)
);


ALTER TABLE activity.community_members OWNER TO postgres;

--
-- Name: community_tags; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.community_tags (
    community_id uuid NOT NULL,
    tag character varying(100) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE activity.community_tags OWNER TO postgres;

--
-- Name: friendships; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.friendships (
    user_id_1 uuid NOT NULL,
    user_id_2 uuid NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    initiated_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    accepted_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'accepted'::character varying, 'blocked'::character varying])::text[]))),
    CONSTRAINT check_user_order CHECK ((user_id_1 < user_id_2))
);


ALTER TABLE activity.friendships OWNER TO postgres;

--
-- Name: media_assets; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.media_assets (
    asset_id uuid DEFAULT public.uuidv7() NOT NULL,
    user_id uuid NOT NULL,
    asset_type character varying(50) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_size_bytes bigint NOT NULL,
    mime_type character varying(100) NOT NULL,
    storage_url character varying(1000) NOT NULL,
    thumbnail_url character varying(1000),
    width integer,
    height integer,
    duration_seconds integer,
    is_processed boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_asset_type CHECK (((asset_type)::text = ANY ((ARRAY['image'::character varying, 'video'::character varying, 'audio'::character varying, 'document'::character varying])::text[]))),
    CONSTRAINT check_dimensions CHECK ((((width IS NULL) AND (height IS NULL)) OR ((width > 0) AND (height > 0)))),
    CONSTRAINT check_file_size CHECK ((file_size_bytes > 0))
);


ALTER TABLE activity.media_assets OWNER TO postgres;

--
-- Name: notification_preferences; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.notification_preferences (
    user_id uuid NOT NULL,
    email_enabled boolean DEFAULT true NOT NULL,
    push_enabled boolean DEFAULT true NOT NULL,
    in_app_enabled boolean DEFAULT true NOT NULL,
    enabled_types jsonb DEFAULT '["activity_invite", "activity_reminder", "activity_update", "community_invite", "new_member", "new_post", "comment", "reaction", "mention", "system"]'::jsonb NOT NULL,
    quiet_hours_start time without time zone,
    quiet_hours_end time without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE activity.notification_preferences OWNER TO postgres;

--
-- Name: notifications; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.notifications (
    notification_id uuid DEFAULT public.uuidv7() NOT NULL,
    user_id uuid NOT NULL,
    actor_user_id uuid,
    notification_type activity.notification_type NOT NULL,
    target_type character varying(50),
    target_id uuid,
    title character varying(255) NOT NULL,
    message text,
    status activity.notification_status DEFAULT 'unread'::activity.notification_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    read_at timestamp with time zone,
    payload jsonb,
    hash_value character varying(64)
);


ALTER TABLE activity.notifications OWNER TO postgres;

--
-- Name: organization_members; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.organization_members (
    organization_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role activity.organization_role DEFAULT 'member'::activity.organization_role NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64)
);


ALTER TABLE activity.organization_members OWNER TO postgres;

--
-- Name: organizations; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.organizations (
    organization_id uuid DEFAULT public.uuidv7() NOT NULL,
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    website_url character varying(500),
    logo_url character varying(500),
    is_verified boolean DEFAULT false NOT NULL,
    status activity.organization_status DEFAULT 'active'::activity.organization_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_slug_format CHECK (((slug)::text ~ '^[a-z0-9-]+$'::text))
);


ALTER TABLE activity.organizations OWNER TO postgres;

--
-- Name: participants; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.participants (
    activity_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role activity.participant_role DEFAULT 'member'::activity.participant_role NOT NULL,
    participation_status activity.participation_status DEFAULT 'registered'::activity.participation_status NOT NULL,
    attendance_status activity.attendance_status DEFAULT 'registered'::activity.attendance_status NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    left_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64)
);


ALTER TABLE activity.participants OWNER TO postgres;

--
-- Name: posts; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.posts (
    post_id uuid DEFAULT public.uuidv7() NOT NULL,
    community_id uuid NOT NULL,
    author_user_id uuid NOT NULL,
    activity_id uuid,
    title character varying(500),
    content text NOT NULL,
    content_type activity.content_type DEFAULT 'post'::activity.content_type NOT NULL,
    status activity.content_status DEFAULT 'published'::activity.content_status NOT NULL,
    view_count integer DEFAULT 0 NOT NULL,
    comment_count integer DEFAULT 0 NOT NULL,
    reaction_count integer DEFAULT 0 NOT NULL,
    is_pinned boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    published_at timestamp with time zone,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_counts_positive CHECK (((view_count >= 0) AND (comment_count >= 0) AND (reaction_count >= 0)))
);


ALTER TABLE activity.posts OWNER TO postgres;

--
-- Name: private_chats; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.private_chats (
    private_chat_id uuid DEFAULT public.uuidv7() NOT NULL,
    user_id_1 uuid NOT NULL,
    user_id_2 uuid NOT NULL,
    external_chat_id character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_message_at timestamp with time zone,
    payload jsonb,
    CONSTRAINT check_user_order CHECK ((user_id_1 < user_id_2))
);


ALTER TABLE activity.private_chats OWNER TO postgres;

--
-- Name: profile_views; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.profile_views (
    view_id uuid DEFAULT public.uuidv7() NOT NULL,
    viewer_user_id uuid NOT NULL,
    viewed_user_id uuid NOT NULL,
    viewed_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    CONSTRAINT check_not_self_view CHECK ((viewer_user_id <> viewed_user_id))
);


ALTER TABLE activity.profile_views OWNER TO postgres;

--
-- Name: reactions; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.reactions (
    reaction_id uuid DEFAULT public.uuidv7() NOT NULL,
    user_id uuid NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id uuid NOT NULL,
    reaction_type activity.reaction_type NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_target_type CHECK (((target_type)::text = ANY ((ARRAY['post'::character varying, 'comment'::character varying, 'memory'::character varying])::text[])))
);


ALTER TABLE activity.reactions OWNER TO postgres;

--
-- Name: refresh_tokens; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.refresh_tokens (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    token character varying(500) NOT NULL,
    jti character varying(50) NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    revoked boolean DEFAULT false NOT NULL
);


ALTER TABLE activity.refresh_tokens OWNER TO postgres;

--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: activity; Owner: postgres
--

CREATE SEQUENCE activity.refresh_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE activity.refresh_tokens_id_seq OWNER TO postgres;

--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: activity; Owner: postgres
--

ALTER SEQUENCE activity.refresh_tokens_id_seq OWNED BY activity.refresh_tokens.id;


--
-- Name: reports; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.reports (
    report_id uuid DEFAULT public.uuidv7() NOT NULL,
    reporter_user_id uuid NOT NULL,
    reported_user_id uuid,
    target_type character varying(50) NOT NULL,
    target_id uuid NOT NULL,
    report_type activity.report_type NOT NULL,
    description text,
    status activity.report_status DEFAULT 'pending'::activity.report_status NOT NULL,
    reviewed_by_user_id uuid,
    reviewed_at timestamp with time zone,
    resolution_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_target_type CHECK (((target_type)::text = ANY ((ARRAY['user'::character varying, 'post'::character varying, 'comment'::character varying, 'activity'::character varying, 'community'::character varying])::text[])))
);


ALTER TABLE activity.reports OWNER TO postgres;

--
-- Name: user_badges; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.user_badges (
    badge_id uuid DEFAULT public.uuidv7() NOT NULL,
    user_id uuid NOT NULL,
    badge_type character varying(100) NOT NULL,
    badge_category activity.badge_category NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    icon_url character varying(500),
    earned_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64)
);


ALTER TABLE activity.user_badges OWNER TO postgres;

--
-- Name: user_blocks; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.user_blocks (
    blocker_user_id uuid NOT NULL,
    blocked_user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    reason text,
    payload jsonb,
    CONSTRAINT check_not_self_block CHECK ((blocker_user_id <> blocked_user_id))
);


ALTER TABLE activity.user_blocks OWNER TO postgres;

--
-- Name: user_favorites; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.user_favorites (
    favoriting_user_id uuid NOT NULL,
    favorited_user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    CONSTRAINT check_not_self_favorite CHECK ((favoriting_user_id <> favorited_user_id))
);


ALTER TABLE activity.user_favorites OWNER TO postgres;

--
-- Name: user_interests; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.user_interests (
    user_id uuid NOT NULL,
    interest_tag character varying(100) NOT NULL,
    weight numeric(3,2) DEFAULT 1.0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_weight_range CHECK (((weight >= 0.0) AND (weight <= 1.0)))
);


ALTER TABLE activity.user_interests OWNER TO postgres;

--
-- Name: user_settings; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.user_settings (
    user_id uuid NOT NULL,
    email_notifications boolean DEFAULT true NOT NULL,
    push_notifications boolean DEFAULT true NOT NULL,
    activity_reminders boolean DEFAULT true NOT NULL,
    community_updates boolean DEFAULT true NOT NULL,
    friend_requests boolean DEFAULT true NOT NULL,
    marketing_emails boolean DEFAULT false NOT NULL,
    ghost_mode boolean DEFAULT false NOT NULL,
    language character varying(10) DEFAULT 'en'::character varying NOT NULL,
    timezone character varying(50) DEFAULT 'UTC'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64)
);


ALTER TABLE activity.user_settings OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.users (
    user_id uuid DEFAULT public.uuidv7() NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    profile_description text,
    main_photo_url character varying(500),
    main_photo_moderation_status activity.photo_moderation_status DEFAULT 'pending'::activity.photo_moderation_status,
    profile_photos_extra jsonb DEFAULT '[]'::jsonb,
    date_of_birth date,
    gender character varying(50),
    subscription_level activity.subscription_level DEFAULT 'free'::activity.subscription_level NOT NULL,
    subscription_expires_at timestamp with time zone,
    status activity.user_status DEFAULT 'active'::activity.user_status NOT NULL,
    ban_expires_at timestamp with time zone,
    ban_reason text,
    is_captain boolean DEFAULT false NOT NULL,
    captain_since timestamp with time zone,
    last_seen_at timestamp with time zone,
    activities_created_count integer DEFAULT 0 NOT NULL,
    activities_attended_count integer DEFAULT 0 NOT NULL,
    is_verified boolean DEFAULT false NOT NULL,
    verification_count integer DEFAULT 0 NOT NULL,
    no_show_count integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login_at timestamp with time zone,
    payload jsonb,
    hash_value character varying(64),
    is_active boolean DEFAULT true NOT NULL,
    roles jsonb DEFAULT '[]'::jsonb,
    CONSTRAINT check_ban_expiry CHECK (((status <> 'temporary_ban'::activity.user_status) OR (ban_expires_at IS NOT NULL))),
    CONSTRAINT check_counts_non_negative CHECK (((activities_created_count >= 0) AND (activities_attended_count >= 0) AND (verification_count >= 0) AND (no_show_count >= 0))),
    CONSTRAINT check_subscription_expiry CHECK (((subscription_level = 'free'::activity.subscription_level) OR (subscription_expires_at IS NOT NULL)))
);


ALTER TABLE activity.users OWNER TO postgres;

--
-- Name: COLUMN users.roles; Type: COMMENT; Schema: activity; Owner: postgres
--

COMMENT ON COLUMN activity.users.roles IS 'User roles for authorization (e.g., ["admin", "moderator"])';


--
-- Name: waitlist_entries; Type: TABLE; Schema: activity; Owner: postgres
--

CREATE TABLE activity.waitlist_entries (
    waitlist_id uuid DEFAULT public.uuidv7() NOT NULL,
    activity_id uuid NOT NULL,
    user_id uuid NOT NULL,
    "position" integer NOT NULL,
    notified_at timestamp with time zone,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    payload jsonb,
    hash_value character varying(64),
    CONSTRAINT check_position_positive CHECK (("position" > 0))
);


ALTER TABLE activity.waitlist_entries OWNER TO postgres;

--
-- Name: refresh_tokens id; Type: DEFAULT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('activity.refresh_tokens_id_seq'::regclass);


--
-- Name: activities activities_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activities
    ADD CONSTRAINT activities_pkey PRIMARY KEY (activity_id);


--
-- Name: activity_invitations activity_invitations_activity_id_user_id_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_invitations
    ADD CONSTRAINT activity_invitations_activity_id_user_id_key UNIQUE (activity_id, user_id);


--
-- Name: activity_invitations activity_invitations_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_invitations
    ADD CONSTRAINT activity_invitations_pkey PRIMARY KEY (invitation_id);


--
-- Name: activity_locations activity_locations_activity_id_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_locations
    ADD CONSTRAINT activity_locations_activity_id_key UNIQUE (activity_id);


--
-- Name: activity_locations activity_locations_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_locations
    ADD CONSTRAINT activity_locations_pkey PRIMARY KEY (location_id);


--
-- Name: activity_reviews activity_reviews_activity_id_reviewer_user_id_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_reviews
    ADD CONSTRAINT activity_reviews_activity_id_reviewer_user_id_key UNIQUE (activity_id, reviewer_user_id);


--
-- Name: activity_reviews activity_reviews_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_reviews
    ADD CONSTRAINT activity_reviews_pkey PRIMARY KEY (review_id);


--
-- Name: activity_tags activity_tags_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_tags
    ADD CONSTRAINT activity_tags_pkey PRIMARY KEY (activity_id, tag);


--
-- Name: attendance_confirmations attendance_confirmations_activity_id_confirmed_user_id_conf_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.attendance_confirmations
    ADD CONSTRAINT attendance_confirmations_activity_id_confirmed_user_id_conf_key UNIQUE (activity_id, confirmed_user_id, confirmer_user_id);


--
-- Name: attendance_confirmations attendance_confirmations_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.attendance_confirmations
    ADD CONSTRAINT attendance_confirmations_pkey PRIMARY KEY (confirmation_id);


--
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (category_id);


--
-- Name: categories categories_slug_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.categories
    ADD CONSTRAINT categories_slug_key UNIQUE (slug);


--
-- Name: comments comments_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.comments
    ADD CONSTRAINT comments_pkey PRIMARY KEY (comment_id);


--
-- Name: communities communities_organization_id_slug_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.communities
    ADD CONSTRAINT communities_organization_id_slug_key UNIQUE (organization_id, slug);


--
-- Name: communities communities_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.communities
    ADD CONSTRAINT communities_pkey PRIMARY KEY (community_id);


--
-- Name: community_activities community_activities_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_activities
    ADD CONSTRAINT community_activities_pkey PRIMARY KEY (community_id, activity_id);


--
-- Name: community_members community_members_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_members
    ADD CONSTRAINT community_members_pkey PRIMARY KEY (community_id, user_id);


--
-- Name: community_tags community_tags_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_tags
    ADD CONSTRAINT community_tags_pkey PRIMARY KEY (community_id, tag);


--
-- Name: friendships friendships_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.friendships
    ADD CONSTRAINT friendships_pkey PRIMARY KEY (user_id_1, user_id_2);


--
-- Name: media_assets media_assets_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.media_assets
    ADD CONSTRAINT media_assets_pkey PRIMARY KEY (asset_id);


--
-- Name: notification_preferences notification_preferences_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.notification_preferences
    ADD CONSTRAINT notification_preferences_pkey PRIMARY KEY (user_id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: organization_members organization_members_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.organization_members
    ADD CONSTRAINT organization_members_pkey PRIMARY KEY (organization_id, user_id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (organization_id);


--
-- Name: organizations organizations_slug_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.organizations
    ADD CONSTRAINT organizations_slug_key UNIQUE (slug);


--
-- Name: participants participants_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.participants
    ADD CONSTRAINT participants_pkey PRIMARY KEY (activity_id, user_id);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (post_id);


--
-- Name: private_chats private_chats_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.private_chats
    ADD CONSTRAINT private_chats_pkey PRIMARY KEY (private_chat_id);


--
-- Name: private_chats private_chats_user_id_1_user_id_2_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.private_chats
    ADD CONSTRAINT private_chats_user_id_1_user_id_2_key UNIQUE (user_id_1, user_id_2);


--
-- Name: profile_views profile_views_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.profile_views
    ADD CONSTRAINT profile_views_pkey PRIMARY KEY (view_id);


--
-- Name: reactions reactions_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.reactions
    ADD CONSTRAINT reactions_pkey PRIMARY KEY (reaction_id);


--
-- Name: reactions reactions_user_id_target_type_target_id_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.reactions
    ADD CONSTRAINT reactions_user_id_target_type_target_id_key UNIQUE (user_id, target_type, target_id);


--
-- Name: refresh_tokens refresh_tokens_jti_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.refresh_tokens
    ADD CONSTRAINT refresh_tokens_jti_key UNIQUE (jti);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: reports reports_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (report_id);


--
-- Name: user_badges user_badges_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_badges
    ADD CONSTRAINT user_badges_pkey PRIMARY KEY (badge_id);


--
-- Name: user_blocks user_blocks_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_blocks
    ADD CONSTRAINT user_blocks_pkey PRIMARY KEY (blocker_user_id, blocked_user_id);


--
-- Name: user_favorites user_favorites_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_favorites
    ADD CONSTRAINT user_favorites_pkey PRIMARY KEY (favoriting_user_id, favorited_user_id);


--
-- Name: user_interests user_interests_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_interests
    ADD CONSTRAINT user_interests_pkey PRIMARY KEY (user_id, interest_tag);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: waitlist_entries waitlist_entries_activity_id_user_id_key; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.waitlist_entries
    ADD CONSTRAINT waitlist_entries_activity_id_user_id_key UNIQUE (activity_id, user_id);


--
-- Name: waitlist_entries waitlist_entries_pkey; Type: CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.waitlist_entries
    ADD CONSTRAINT waitlist_entries_pkey PRIMARY KEY (waitlist_id);


--
-- Name: idx_activities_category; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_category ON activity.activities USING btree (category_id);


--
-- Name: idx_activities_city; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_city ON activity.activities USING btree (city) WHERE (city IS NOT NULL);


--
-- Name: idx_activities_joinable_free; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_joinable_free ON activity.activities USING btree (joinable_at_free) WHERE (joinable_at_free IS NOT NULL);


--
-- Name: idx_activities_language; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_language ON activity.activities USING btree (language);


--
-- Name: idx_activities_organizer; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_organizer ON activity.activities USING btree (organizer_user_id);


--
-- Name: idx_activities_privacy; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_privacy ON activity.activities USING btree (activity_privacy_level);


--
-- Name: idx_activities_scheduled; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_scheduled ON activity.activities USING btree (scheduled_at) WHERE (status = 'published'::activity.activity_status);


--
-- Name: idx_activities_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_status ON activity.activities USING btree (status);


--
-- Name: idx_activities_type; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activities_type ON activity.activities USING btree (activity_type);


--
-- Name: idx_activity_invitations_activity; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_invitations_activity ON activity.activity_invitations USING btree (activity_id, status);


--
-- Name: idx_activity_invitations_expires; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_invitations_expires ON activity.activity_invitations USING btree (expires_at) WHERE ((expires_at IS NOT NULL) AND (status = 'pending'::activity.invitation_status));


--
-- Name: idx_activity_invitations_invited_by; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_invitations_invited_by ON activity.activity_invitations USING btree (invited_by_user_id);


--
-- Name: idx_activity_invitations_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_invitations_user ON activity.activity_invitations USING btree (user_id, status);


--
-- Name: idx_activity_locations_coords; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_locations_coords ON activity.activity_locations USING btree (latitude, longitude) WHERE ((latitude IS NOT NULL) AND (longitude IS NOT NULL));


--
-- Name: idx_activity_reviews_activity; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_reviews_activity ON activity.activity_reviews USING btree (activity_id);


--
-- Name: idx_activity_reviews_reviewer; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_reviews_reviewer ON activity.activity_reviews USING btree (reviewer_user_id);


--
-- Name: idx_activity_tags_tag; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_activity_tags_tag ON activity.activity_tags USING btree (tag);


--
-- Name: idx_attendance_confirmations_activity; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_attendance_confirmations_activity ON activity.attendance_confirmations USING btree (activity_id);


--
-- Name: idx_attendance_confirmations_confirmed; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_attendance_confirmations_confirmed ON activity.attendance_confirmations USING btree (confirmed_user_id);


--
-- Name: idx_categories_active; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_categories_active ON activity.categories USING btree (is_active, display_order) WHERE (is_active = true);


--
-- Name: idx_comments_author; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_comments_author ON activity.comments USING btree (author_user_id);


--
-- Name: idx_comments_parent; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_comments_parent ON activity.comments USING btree (parent_comment_id) WHERE (parent_comment_id IS NOT NULL);


--
-- Name: idx_comments_post; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_comments_post ON activity.comments USING btree (post_id, created_at);


--
-- Name: idx_communities_org; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_communities_org ON activity.communities USING btree (organization_id);


--
-- Name: idx_communities_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_communities_status ON activity.communities USING btree (status) WHERE (status = 'active'::activity.community_status);


--
-- Name: idx_community_activities_activity; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_community_activities_activity ON activity.community_activities USING btree (activity_id);


--
-- Name: idx_community_members_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_community_members_status ON activity.community_members USING btree (community_id, status);


--
-- Name: idx_community_members_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_community_members_user ON activity.community_members USING btree (user_id);


--
-- Name: idx_community_tags_tag; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_community_tags_tag ON activity.community_tags USING btree (tag);


--
-- Name: idx_friendships_user1_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_friendships_user1_status ON activity.friendships USING btree (user_id_1, status);


--
-- Name: idx_friendships_user2_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_friendships_user2_status ON activity.friendships USING btree (user_id_2, status);


--
-- Name: idx_media_assets_type; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_media_assets_type ON activity.media_assets USING btree (asset_type);


--
-- Name: idx_media_assets_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_media_assets_user ON activity.media_assets USING btree (user_id, created_at DESC);


--
-- Name: idx_notification_preferences_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_notification_preferences_user ON activity.notification_preferences USING btree (user_id);


--
-- Name: idx_notifications_created; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_notifications_created ON activity.notifications USING btree (created_at) WHERE (status = 'unread'::activity.notification_status);


--
-- Name: idx_notifications_user_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_notifications_user_status ON activity.notifications USING btree (user_id, status, created_at DESC);


--
-- Name: idx_org_members_org_id; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_org_members_org_id ON activity.organization_members USING btree (organization_id);


--
-- Name: idx_org_members_role; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_org_members_role ON activity.organization_members USING btree (role);


--
-- Name: idx_org_members_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_org_members_user ON activity.organization_members USING btree (user_id);


--
-- Name: idx_org_members_user_id; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_org_members_user_id ON activity.organization_members USING btree (user_id);


--
-- Name: idx_org_members_user_org; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_org_members_user_org ON activity.organization_members USING btree (user_id, organization_id);


--
-- Name: idx_organizations_created_at; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_organizations_created_at ON activity.organizations USING btree (created_at);


--
-- Name: idx_participants_attendance; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_participants_attendance ON activity.participants USING btree (attendance_status) WHERE (attendance_status <> 'registered'::activity.attendance_status);


--
-- Name: idx_participants_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_participants_status ON activity.participants USING btree (participation_status);


--
-- Name: idx_participants_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_participants_user ON activity.participants USING btree (user_id);


--
-- Name: idx_posts_activity; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_posts_activity ON activity.posts USING btree (activity_id) WHERE (activity_id IS NOT NULL);


--
-- Name: idx_posts_author; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_posts_author ON activity.posts USING btree (author_user_id);


--
-- Name: idx_posts_community; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_posts_community ON activity.posts USING btree (community_id, status, created_at DESC);


--
-- Name: idx_private_chats_external; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_private_chats_external ON activity.private_chats USING btree (external_chat_id);


--
-- Name: idx_private_chats_user1; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_private_chats_user1 ON activity.private_chats USING btree (user_id_1);


--
-- Name: idx_private_chats_user2; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_private_chats_user2 ON activity.private_chats USING btree (user_id_2);


--
-- Name: idx_profile_views_viewed; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_profile_views_viewed ON activity.profile_views USING btree (viewed_user_id, viewed_at DESC);


--
-- Name: idx_profile_views_viewer; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_profile_views_viewer ON activity.profile_views USING btree (viewer_user_id);


--
-- Name: idx_reactions_target; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_reactions_target ON activity.reactions USING btree (target_type, target_id);


--
-- Name: idx_reactions_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_reactions_user ON activity.reactions USING btree (user_id);


--
-- Name: idx_refresh_tokens_expires; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_refresh_tokens_expires ON activity.refresh_tokens USING btree (expires_at);


--
-- Name: idx_refresh_tokens_jti; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_refresh_tokens_jti ON activity.refresh_tokens USING btree (jti);


--
-- Name: idx_refresh_tokens_user_id; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_refresh_tokens_user_id ON activity.refresh_tokens USING btree (user_id);


--
-- Name: idx_reports_reported_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_reports_reported_user ON activity.reports USING btree (reported_user_id) WHERE (reported_user_id IS NOT NULL);


--
-- Name: idx_reports_reporter; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_reports_reporter ON activity.reports USING btree (reporter_user_id);


--
-- Name: idx_reports_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_reports_status ON activity.reports USING btree (status, created_at);


--
-- Name: idx_reports_target; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_reports_target ON activity.reports USING btree (target_type, target_id);


--
-- Name: idx_user_badges_category; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_badges_category ON activity.user_badges USING btree (badge_category);


--
-- Name: idx_user_badges_type; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_badges_type ON activity.user_badges USING btree (badge_type);


--
-- Name: idx_user_badges_user; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_badges_user ON activity.user_badges USING btree (user_id, earned_at DESC);


--
-- Name: idx_user_blocks_blocked; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_blocks_blocked ON activity.user_blocks USING btree (blocked_user_id);


--
-- Name: idx_user_blocks_blocker; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_blocks_blocker ON activity.user_blocks USING btree (blocker_user_id);


--
-- Name: idx_user_favorites_favorited; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_favorites_favorited ON activity.user_favorites USING btree (favorited_user_id);


--
-- Name: idx_user_interests_tag; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_interests_tag ON activity.user_interests USING btree (interest_tag);


--
-- Name: idx_user_settings_ghost_mode; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_user_settings_ghost_mode ON activity.user_settings USING btree (ghost_mode) WHERE (ghost_mode = true);


--
-- Name: idx_users_captain; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_captain ON activity.users USING btree (is_captain) WHERE (is_captain = true);


--
-- Name: idx_users_email; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_email ON activity.users USING btree (email);


--
-- Name: idx_users_main_photo_moderation; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_main_photo_moderation ON activity.users USING btree (main_photo_moderation_status) WHERE (main_photo_moderation_status = 'pending'::activity.photo_moderation_status);


--
-- Name: idx_users_roles; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_roles ON activity.users USING gin (roles);


--
-- Name: idx_users_status; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_status ON activity.users USING btree (status) WHERE (status <> 'active'::activity.user_status);


--
-- Name: idx_users_subscription; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_subscription ON activity.users USING btree (subscription_level, subscription_expires_at);


--
-- Name: idx_users_username; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_username ON activity.users USING btree (username);


--
-- Name: idx_users_verified; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_users_verified ON activity.users USING btree (is_verified) WHERE (is_verified = true);


--
-- Name: idx_waitlist_activity_position; Type: INDEX; Schema: activity; Owner: postgres
--

CREATE INDEX idx_waitlist_activity_position ON activity.waitlist_entries USING btree (activity_id, "position");


--
-- Name: activities set_activities_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_activities_timestamp BEFORE UPDATE ON activity.activities FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: activity_invitations set_activity_invitations_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_activity_invitations_timestamp BEFORE UPDATE ON activity.activity_invitations FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: activity_locations set_activity_locations_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_activity_locations_timestamp BEFORE UPDATE ON activity.activity_locations FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: activity_reviews set_activity_reviews_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_activity_reviews_timestamp BEFORE UPDATE ON activity.activity_reviews FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: categories set_categories_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_categories_timestamp BEFORE UPDATE ON activity.categories FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: comments set_comments_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_comments_timestamp BEFORE UPDATE ON activity.comments FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: communities set_communities_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_communities_timestamp BEFORE UPDATE ON activity.communities FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: community_activities set_community_activities_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_community_activities_timestamp BEFORE UPDATE ON activity.community_activities FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: community_members set_community_members_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_community_members_timestamp BEFORE UPDATE ON activity.community_members FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: friendships set_friendships_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_friendships_timestamp BEFORE UPDATE ON activity.friendships FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: organization_members set_organization_members_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_organization_members_timestamp BEFORE UPDATE ON activity.organization_members FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: organizations set_organizations_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_organizations_timestamp BEFORE UPDATE ON activity.organizations FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: participants set_participants_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_participants_timestamp BEFORE UPDATE ON activity.participants FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: posts set_posts_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_posts_timestamp BEFORE UPDATE ON activity.posts FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: reports set_reports_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_reports_timestamp BEFORE UPDATE ON activity.reports FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: user_interests set_user_interests_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_user_interests_timestamp BEFORE UPDATE ON activity.user_interests FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: user_settings set_user_settings_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_user_settings_timestamp BEFORE UPDATE ON activity.user_settings FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: users set_users_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_users_timestamp BEFORE UPDATE ON activity.users FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: waitlist_entries set_waitlist_entries_timestamp; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER set_waitlist_entries_timestamp BEFORE UPDATE ON activity.waitlist_entries FOR EACH ROW EXECUTE FUNCTION activity.update_timestamp();


--
-- Name: organizations trigger_organizations_updated_at; Type: TRIGGER; Schema: activity; Owner: postgres
--

CREATE TRIGGER trigger_organizations_updated_at BEFORE UPDATE ON activity.organizations FOR EACH ROW EXECUTE FUNCTION activity.update_organizations_updated_at();


--
-- Name: activities activities_category_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activities
    ADD CONSTRAINT activities_category_id_fkey FOREIGN KEY (category_id) REFERENCES activity.categories(category_id);


--
-- Name: activities activities_organizer_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activities
    ADD CONSTRAINT activities_organizer_user_id_fkey FOREIGN KEY (organizer_user_id) REFERENCES activity.users(user_id);


--
-- Name: activity_invitations activity_invitations_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_invitations
    ADD CONSTRAINT activity_invitations_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id) ON DELETE CASCADE;


--
-- Name: activity_invitations activity_invitations_invited_by_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_invitations
    ADD CONSTRAINT activity_invitations_invited_by_user_id_fkey FOREIGN KEY (invited_by_user_id) REFERENCES activity.users(user_id);


--
-- Name: activity_invitations activity_invitations_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_invitations
    ADD CONSTRAINT activity_invitations_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: activity_locations activity_locations_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_locations
    ADD CONSTRAINT activity_locations_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id) ON DELETE CASCADE;


--
-- Name: activity_reviews activity_reviews_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_reviews
    ADD CONSTRAINT activity_reviews_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id);


--
-- Name: activity_reviews activity_reviews_reviewer_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_reviews
    ADD CONSTRAINT activity_reviews_reviewer_user_id_fkey FOREIGN KEY (reviewer_user_id) REFERENCES activity.users(user_id);


--
-- Name: activity_tags activity_tags_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.activity_tags
    ADD CONSTRAINT activity_tags_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id) ON DELETE CASCADE;


--
-- Name: attendance_confirmations attendance_confirmations_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.attendance_confirmations
    ADD CONSTRAINT attendance_confirmations_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id) ON DELETE CASCADE;


--
-- Name: attendance_confirmations attendance_confirmations_confirmed_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.attendance_confirmations
    ADD CONSTRAINT attendance_confirmations_confirmed_user_id_fkey FOREIGN KEY (confirmed_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: attendance_confirmations attendance_confirmations_confirmer_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.attendance_confirmations
    ADD CONSTRAINT attendance_confirmations_confirmer_user_id_fkey FOREIGN KEY (confirmer_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: comments comments_author_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.comments
    ADD CONSTRAINT comments_author_user_id_fkey FOREIGN KEY (author_user_id) REFERENCES activity.users(user_id);


--
-- Name: comments comments_parent_comment_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.comments
    ADD CONSTRAINT comments_parent_comment_id_fkey FOREIGN KEY (parent_comment_id) REFERENCES activity.comments(comment_id) ON DELETE CASCADE;


--
-- Name: comments comments_post_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.comments
    ADD CONSTRAINT comments_post_id_fkey FOREIGN KEY (post_id) REFERENCES activity.posts(post_id) ON DELETE CASCADE;


--
-- Name: communities communities_creator_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.communities
    ADD CONSTRAINT communities_creator_user_id_fkey FOREIGN KEY (creator_user_id) REFERENCES activity.users(user_id);


--
-- Name: communities communities_organization_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.communities
    ADD CONSTRAINT communities_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES activity.organizations(organization_id) ON DELETE CASCADE;


--
-- Name: community_activities community_activities_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_activities
    ADD CONSTRAINT community_activities_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id) ON DELETE CASCADE;


--
-- Name: community_activities community_activities_community_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_activities
    ADD CONSTRAINT community_activities_community_id_fkey FOREIGN KEY (community_id) REFERENCES activity.communities(community_id) ON DELETE CASCADE;


--
-- Name: community_members community_members_community_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_members
    ADD CONSTRAINT community_members_community_id_fkey FOREIGN KEY (community_id) REFERENCES activity.communities(community_id) ON DELETE CASCADE;


--
-- Name: community_members community_members_invited_by_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_members
    ADD CONSTRAINT community_members_invited_by_user_id_fkey FOREIGN KEY (invited_by_user_id) REFERENCES activity.users(user_id);


--
-- Name: community_members community_members_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_members
    ADD CONSTRAINT community_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: community_tags community_tags_community_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.community_tags
    ADD CONSTRAINT community_tags_community_id_fkey FOREIGN KEY (community_id) REFERENCES activity.communities(community_id) ON DELETE CASCADE;


--
-- Name: friendships friendships_initiated_by_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.friendships
    ADD CONSTRAINT friendships_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES activity.users(user_id);


--
-- Name: friendships friendships_user_id_1_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.friendships
    ADD CONSTRAINT friendships_user_id_1_fkey FOREIGN KEY (user_id_1) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: friendships friendships_user_id_2_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.friendships
    ADD CONSTRAINT friendships_user_id_2_fkey FOREIGN KEY (user_id_2) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: media_assets media_assets_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.media_assets
    ADD CONSTRAINT media_assets_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id);


--
-- Name: notification_preferences notification_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.notification_preferences
    ADD CONSTRAINT notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: notifications notifications_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.notifications
    ADD CONSTRAINT notifications_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES activity.users(user_id);


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: organization_members organization_members_organization_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.organization_members
    ADD CONSTRAINT organization_members_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES activity.organizations(organization_id) ON DELETE CASCADE;


--
-- Name: organization_members organization_members_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.organization_members
    ADD CONSTRAINT organization_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: participants participants_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.participants
    ADD CONSTRAINT participants_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id) ON DELETE CASCADE;


--
-- Name: participants participants_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.participants
    ADD CONSTRAINT participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: posts posts_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.posts
    ADD CONSTRAINT posts_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id);


--
-- Name: posts posts_author_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.posts
    ADD CONSTRAINT posts_author_user_id_fkey FOREIGN KEY (author_user_id) REFERENCES activity.users(user_id);


--
-- Name: posts posts_community_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.posts
    ADD CONSTRAINT posts_community_id_fkey FOREIGN KEY (community_id) REFERENCES activity.communities(community_id) ON DELETE CASCADE;


--
-- Name: private_chats private_chats_user_id_1_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.private_chats
    ADD CONSTRAINT private_chats_user_id_1_fkey FOREIGN KEY (user_id_1) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: private_chats private_chats_user_id_2_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.private_chats
    ADD CONSTRAINT private_chats_user_id_2_fkey FOREIGN KEY (user_id_2) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: profile_views profile_views_viewed_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.profile_views
    ADD CONSTRAINT profile_views_viewed_user_id_fkey FOREIGN KEY (viewed_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: profile_views profile_views_viewer_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.profile_views
    ADD CONSTRAINT profile_views_viewer_user_id_fkey FOREIGN KEY (viewer_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: reactions reactions_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.reactions
    ADD CONSTRAINT reactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: refresh_tokens refresh_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: reports reports_reported_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.reports
    ADD CONSTRAINT reports_reported_user_id_fkey FOREIGN KEY (reported_user_id) REFERENCES activity.users(user_id);


--
-- Name: reports reports_reporter_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.reports
    ADD CONSTRAINT reports_reporter_user_id_fkey FOREIGN KEY (reporter_user_id) REFERENCES activity.users(user_id);


--
-- Name: reports reports_reviewed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.reports
    ADD CONSTRAINT reports_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES activity.users(user_id);


--
-- Name: user_badges user_badges_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_badges
    ADD CONSTRAINT user_badges_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: user_blocks user_blocks_blocked_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_blocks
    ADD CONSTRAINT user_blocks_blocked_user_id_fkey FOREIGN KEY (blocked_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: user_blocks user_blocks_blocker_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_blocks
    ADD CONSTRAINT user_blocks_blocker_user_id_fkey FOREIGN KEY (blocker_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: user_favorites user_favorites_favorited_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_favorites
    ADD CONSTRAINT user_favorites_favorited_user_id_fkey FOREIGN KEY (favorited_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: user_favorites user_favorites_favoriting_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_favorites
    ADD CONSTRAINT user_favorites_favoriting_user_id_fkey FOREIGN KEY (favoriting_user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: user_interests user_interests_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_interests
    ADD CONSTRAINT user_interests_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: waitlist_entries waitlist_entries_activity_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.waitlist_entries
    ADD CONSTRAINT waitlist_entries_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES activity.activities(activity_id) ON DELETE CASCADE;


--
-- Name: waitlist_entries waitlist_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: activity; Owner: postgres
--

ALTER TABLE ONLY activity.waitlist_entries
    ADD CONSTRAINT waitlist_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES activity.users(user_id) ON DELETE CASCADE;


--
-- Name: SCHEMA activity; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA activity TO auth_api_user;


--
-- Name: FUNCTION sp_cleanup_unverified_users(p_days_old integer); Type: ACL; Schema: activity; Owner: postgres
--

GRANT ALL ON FUNCTION activity.sp_cleanup_unverified_users(p_days_old integer) TO auth_api_user;


--
-- Name: FUNCTION sp_get_valid_refresh_token(p_token character varying); Type: ACL; Schema: activity; Owner: postgres
--

GRANT ALL ON FUNCTION activity.sp_get_valid_refresh_token(p_token character varying) TO auth_api_user;


--
-- Name: FUNCTION sp_revoke_refresh_token(p_user_id uuid, p_token character varying); Type: ACL; Schema: activity; Owner: postgres
--

GRANT ALL ON FUNCTION activity.sp_revoke_refresh_token(p_user_id uuid, p_token character varying) TO auth_api_user;


--
-- Name: FUNCTION sp_save_refresh_token(p_user_id uuid, p_token character varying, p_jti character varying, p_expires_at timestamp without time zone); Type: ACL; Schema: activity; Owner: postgres
--

GRANT ALL ON FUNCTION activity.sp_save_refresh_token(p_user_id uuid, p_token character varying, p_jti character varying, p_expires_at timestamp without time zone) TO auth_api_user;


--
-- Name: TABLE activities; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.activities TO auth_api_user;


--
-- Name: TABLE activity_invitations; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.activity_invitations TO auth_api_user;


--
-- Name: TABLE activity_locations; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.activity_locations TO auth_api_user;


--
-- Name: TABLE activity_reviews; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.activity_reviews TO auth_api_user;


--
-- Name: TABLE activity_tags; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.activity_tags TO auth_api_user;


--
-- Name: TABLE attendance_confirmations; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.attendance_confirmations TO auth_api_user;


--
-- Name: TABLE categories; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.categories TO auth_api_user;


--
-- Name: TABLE comments; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.comments TO auth_api_user;


--
-- Name: TABLE communities; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.communities TO auth_api_user;


--
-- Name: TABLE community_activities; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.community_activities TO auth_api_user;


--
-- Name: TABLE community_members; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.community_members TO auth_api_user;


--
-- Name: TABLE community_tags; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.community_tags TO auth_api_user;


--
-- Name: TABLE friendships; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.friendships TO auth_api_user;


--
-- Name: TABLE media_assets; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.media_assets TO auth_api_user;


--
-- Name: TABLE notification_preferences; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.notification_preferences TO auth_api_user;


--
-- Name: TABLE notifications; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.notifications TO auth_api_user;


--
-- Name: TABLE organization_members; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.organization_members TO auth_api_user;


--
-- Name: TABLE organizations; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.organizations TO auth_api_user;


--
-- Name: TABLE participants; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.participants TO auth_api_user;


--
-- Name: TABLE posts; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.posts TO auth_api_user;


--
-- Name: TABLE private_chats; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.private_chats TO auth_api_user;


--
-- Name: TABLE profile_views; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.profile_views TO auth_api_user;


--
-- Name: TABLE reactions; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.reactions TO auth_api_user;


--
-- Name: TABLE refresh_tokens; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.refresh_tokens TO auth_api_user;


--
-- Name: TABLE reports; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.reports TO auth_api_user;


--
-- Name: TABLE user_badges; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.user_badges TO auth_api_user;


--
-- Name: TABLE user_blocks; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.user_blocks TO auth_api_user;


--
-- Name: TABLE user_favorites; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.user_favorites TO auth_api_user;


--
-- Name: TABLE user_interests; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.user_interests TO auth_api_user;


--
-- Name: TABLE user_settings; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.user_settings TO auth_api_user;


--
-- Name: TABLE users; Type: ACL; Schema: activity; Owner: postgres
--

GRANT ALL ON TABLE activity.users TO auth_api_user;


--
-- Name: TABLE waitlist_entries; Type: ACL; Schema: activity; Owner: postgres
--

GRANT SELECT ON TABLE activity.waitlist_entries TO auth_api_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: activity; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA activity GRANT SELECT ON TABLES TO auth_api_user;


--
-- PostgreSQL database dump complete
--

\unrestrict nobbgSzeAg1RfFrkJ3bvM7wA2HcL8mycUEbd4ZBzmgf23F6dDK1jR2mT9fomim5

