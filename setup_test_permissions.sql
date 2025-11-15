-- Setup test permissions for L2 cache testing
-- User: c0a61eba-5805-494c-bc1b-563d3ca49126
-- Org:  1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e

-- 1. Create permissions (if not exist)
INSERT INTO activity.permissions (resource, action, description)
VALUES 
  ('activity', 'create', 'Create activities'),
  ('activity', 'read', 'Read activities'),
  ('activity', 'update', 'Update activities'),
  ('activity', 'delete', 'Delete activities')
ON CONFLICT (resource, action) DO NOTHING;

-- 2. Create a test group
DO $$
DECLARE
  v_group_id UUID;
  v_perm_id UUID;
BEGIN
  -- Create group
  INSERT INTO activity.groups (organization_id, name, description, created_by)
  VALUES (
    '1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e',
    'L2 Cache Test Group',
    'Test group for L2 cache performance testing',
    'c0a61eba-5805-494c-bc1b-563d3ca49126'
  )
  ON CONFLICT DO NOTHING
  RETURNING id INTO v_group_id;

  -- If already exists, get the ID
  IF v_group_id IS NULL THEN
    SELECT id INTO v_group_id 
    FROM activity.groups 
    WHERE name = 'L2 Cache Test Group' 
    AND organization_id = '1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e';
  END IF;

  -- Grant all activity permissions to group
  FOR v_perm_id IN 
    SELECT id FROM activity.permissions 
    WHERE resource = 'activity'
  LOOP
    INSERT INTO activity.group_permissions (group_id, permission_id, granted_by)
    VALUES (v_group_id, v_perm_id, 'c0a61eba-5805-494c-bc1b-563d3ca49126')
    ON CONFLICT (group_id, permission_id) DO NOTHING;
  END LOOP;

  -- Add user to group
  INSERT INTO activity.user_groups (user_id, group_id, added_by)
  VALUES (
    'c0a61eba-5805-494c-bc1b-563d3ca49126',
    v_group_id,
    'c0a61eba-5805-494c-bc1b-563d3ca49126'
  )
  ON CONFLICT (user_id, group_id) DO NOTHING;

  RAISE NOTICE 'Setup complete! Group ID: %, User added with 4 activity permissions', v_group_id;
END $$;

-- Verify setup
SELECT 
  p.resource || ':' || p.action as permission,
  g.name as group_name
FROM activity.permissions p
JOIN activity.group_permissions gp ON p.id = gp.permission_id
JOIN activity.groups g ON gp.group_id = g.id
JOIN activity.user_groups ug ON g.id = ug.group_id
WHERE ug.user_id = 'c0a61eba-5805-494c-bc1b-563d3ca49126'
AND g.organization_id = '1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e';
