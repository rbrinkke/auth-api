-- ============================================================================
-- Image Permissions: RBAC Capabilities Model
-- ============================================================================
-- Model: r (read) | rw (write) | x (admin)
-- Ownership checks gebeuren in image-api, niet in RBAC
-- ============================================================================

-- Update existing image:upload → image:write
UPDATE activity.permissions 
SET 
    action = 'write', 
    description = 'Upload, update, and delete own images'
WHERE resource = 'image' AND action = 'upload';

-- Add image:read (view/download)
INSERT INTO activity.permissions (resource, action, description)
VALUES ('image', 'read', 'View and download images')
ON CONFLICT (resource, action) DO NOTHING;

-- Add image:admin (full rights on all images)
INSERT INTO activity.permissions (resource, action, description)
VALUES ('image', 'admin', 'Full admin rights on all images in organization')
ON CONFLICT (resource, action) DO NOTHING;

-- Verify result
SELECT resource, action, description 
FROM activity.permissions 
WHERE resource = 'image'
ORDER BY 
    CASE action 
        WHEN 'read' THEN 1 
        WHEN 'write' THEN 2 
        WHEN 'admin' THEN 3 
    END;
