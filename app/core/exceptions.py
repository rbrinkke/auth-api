class AuthException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)

class InvalidCredentialsError(AuthException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail)

class UserAlreadyExistsError(AuthException):
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(detail)

class UserNotFoundError(AuthException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail)

class TokenExpiredError(AuthException):
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail)

class InvalidTokenError(AuthException):
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail)

class VerificationError(AuthException):
    pass

class AccountNotVerifiedError(AuthException):
    def __init__(self, detail: str = "Account not verified"):
        super().__init__(detail)

class InvalidPasswordError(AuthException):
    pass

class TwoFactorRequiredError(AuthException):
    def __init__(self, detail: str = "2FA token required"):
        super().__init__(detail)

class TwoFactorSetupError(AuthException):
    pass

class TwoFactorVerificationError(AuthException):
    def __init__(self, detail: str = "Invalid 2FA code"):
        super().__init__(detail)

class RequestEntityTooLargeError(AuthException):
    def __init__(self, detail: str = "Request body too large"):
        super().__init__(detail)

# ============================================================================
# Organization Exceptions
# ============================================================================

class OrganizationError(AuthException):
    """Base exception for organization-related errors"""
    pass

class OrganizationNotFoundError(OrganizationError):
    def __init__(self, detail: str = "Organization not found"):
        super().__init__(detail)

class OrganizationSlugExistsError(OrganizationError):
    def __init__(self, slug: str = None):
        detail = f"Organization with slug '{slug}' already exists" if slug else "Organization slug already exists"
        super().__init__(detail)

class UserNotOrganizationMemberError(OrganizationError):
    def __init__(self, detail: str = "You are not a member of this organization"):
        super().__init__(detail)

class InsufficientOrganizationPermissionError(OrganizationError):
    def __init__(self, detail: str = "Insufficient permissions for this operation"):
        super().__init__(detail)

class OrganizationMemberAlreadyExistsError(OrganizationError):
    def __init__(self, detail: str = "User is already a member of this organization"):
        super().__init__(detail)

class LastOwnerRemovalError(OrganizationError):
    def __init__(self, detail: str = "Cannot remove the last owner from organization"):
        super().__init__(detail)


# ============================================================================
# RBAC Exceptions (Groups & Permissions)
# ============================================================================

class RBACError(AuthException):
    """Base exception for RBAC-related errors (groups and permissions)"""
    pass


# Group Exceptions
class GroupError(RBACError):
    """Base exception for group-related errors"""
    pass


class GroupNotFoundError(GroupError):
    def __init__(self, detail: str = "Group not found"):
        super().__init__(detail)


class DuplicateGroupNameError(GroupError):
    def __init__(self, group_name: str = None):
        detail = f"Group '{group_name}' already exists in this organization" if group_name else "Group name already exists"
        super().__init__(detail)


class NotGroupMemberError(GroupError):
    def __init__(self, detail: str = "User is not a member of this group"):
        super().__init__(detail)


class GroupMemberAlreadyExistsError(GroupError):
    def __init__(self, detail: str = "User is already a member of this group"):
        super().__init__(detail)


# Permission Exceptions
class PermissionError(RBACError):
    """Base exception for permission-related errors"""
    pass


class PermissionNotFoundError(PermissionError):
    def __init__(self, permission: str = None):
        detail = f"Permission '{permission}' not found" if permission else "Permission not found"
        super().__init__(detail)


class DuplicatePermissionError(PermissionError):
    def __init__(self, permission: str = None):
        detail = f"Permission '{permission}' already exists" if permission else "Permission already exists"
        super().__init__(detail)


class GroupPermissionAlreadyGrantedError(PermissionError):
    def __init__(self, detail: str = "Permission already granted to this group"):
        super().__init__(detail)


class GroupPermissionNotGrantedError(PermissionError):
    def __init__(self, detail: str = "Permission not granted to this group"):
        super().__init__(detail)


# Authorization Exceptions
class AuthorizationError(RBACError):
    """Base exception for authorization checks"""
    pass


class InsufficientPermissionError(AuthorizationError):
    """User lacks required permission for this operation"""
    def __init__(self, required_permission: str = None, detail: str = None):
        if detail:
            super().__init__(detail)
        elif required_permission:
            super().__init__(f"Insufficient permissions: '{required_permission}' required")
        else:
            super().__init__("Insufficient permissions for this operation")


class PermissionDeniedError(AuthorizationError):
    """Generic permission denied error"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail)
