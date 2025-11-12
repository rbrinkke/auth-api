"""
OAuth 2.0 Schemas

Pydantic models for OAuth 2.0 Authorization Server endpoints.
Follows RFC 6749, RFC 7636 (PKCE), RFC 7009 (Revocation).
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, HttpUrl
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ClientType(str, Enum):
    """OAuth client type"""
    PUBLIC = "public"  # SPA, mobile app (no client_secret)
    CONFIDENTIAL = "confidential"  # Backend service (has client_secret)


class GrantType(str, Enum):
    """OAuth grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"
    CLIENT_CREDENTIALS = "client_credentials"  # Future


class ResponseType(str, Enum):
    """OAuth response types"""
    CODE = "code"  # Authorization Code flow
    TOKEN = "token"  # Implicit flow (deprecated, not implemented)


class CodeChallengeMethod(str, Enum):
    """PKCE code challenge methods"""
    S256 = "S256"  # SHA256 (recommended)
    PLAIN = "plain"  # Plain text (not recommended, only for debugging)


class TokenType(str, Enum):
    """OAuth token types"""
    BEARER = "bearer"


# ============================================================================
# OAUTH CLIENT SCHEMAS
# ============================================================================

class OAuthClientCreate(BaseModel):
    """Request to register a new OAuth client"""
    client_id: str = Field(..., min_length=3, max_length=255, description="Client identifier (e.g., 'image-api-v1')")
    client_name: str = Field(..., min_length=1, max_length=255, description="Human-readable client name")
    client_type: ClientType = Field(..., description="Client type (public or confidential)")
    redirect_uris: List[str] = Field(..., min_items=1, description="Allowed redirect URIs (exact match)")
    allowed_scopes: List[str] = Field(..., min_items=1, description="Scopes this client can request")

    client_secret: Optional[str] = Field(None, description="Client secret (required for confidential clients)")
    is_first_party: bool = Field(False, description="First-party clients skip consent")
    description: Optional[str] = Field(None, max_length=1000)
    logo_uri: Optional[str] = Field(None)
    homepage_uri: Optional[str] = Field(None)

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate client_id format (alphanumeric, hyphens, underscores)"""
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError("client_id must contain only alphanumeric characters, hyphens, and underscores")
        return v

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, v: List[str]) -> List[str]:
        """Validate redirect URIs (must be HTTPS except localhost)"""
        for uri in v:
            if not uri.startswith(('https://', 'http://localhost', 'http://127.0.0.1')):
                # Allow custom schemes for mobile apps
                if not '://' in uri:
                    raise ValueError(f"Invalid redirect URI: {uri}")
        return v

    @field_validator("allowed_scopes")
    @classmethod
    def validate_scopes(cls, v: List[str]) -> List[str]:
        """Validate scope format (resource:action)"""
        for scope in v:
            if ':' not in scope:
                raise ValueError(f"Invalid scope format: {scope} (expected 'resource:action')")
        return v


class OAuthClientResponse(BaseModel):
    """OAuth client details (public information)"""
    id: UUID
    client_id: str
    client_name: str
    client_type: ClientType
    redirect_uris: List[str]
    allowed_scopes: List[str]
    is_first_party: bool
    require_pkce: bool
    require_consent: bool
    description: Optional[str]
    logo_uri: Optional[str]
    created_at: str


class OAuthClientSecret(BaseModel):
    """Response with client secret (only returned once at creation)"""
    client_id: str
    client_secret: str
    client_secret_expires_at: Optional[int] = Field(None, description="Unix timestamp (0 = never expires)")


# ============================================================================
# AUTHORIZATION REQUEST SCHEMAS
# ============================================================================

class AuthorizationRequest(BaseModel):
    """OAuth authorization request (query parameters)"""
    response_type: ResponseType = Field(..., description="Response type (must be 'code')")
    client_id: str = Field(..., min_length=1, description="Client identifier")
    redirect_uri: str = Field(..., description="Redirect URI (must match registered URI)")
    scope: str = Field(..., description="Space-separated list of scopes")
    state: str = Field(..., min_length=8, description="CSRF protection token")

    # PKCE (mandatory for public clients)
    code_challenge: str = Field(..., min_length=43, max_length=128, description="SHA256(code_verifier)")
    code_challenge_method: CodeChallengeMethod = Field(CodeChallengeMethod.S256, description="PKCE method (S256 recommended)")

    # Optional
    nonce: Optional[str] = Field(None, description="OpenID Connect nonce")

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        """Validate scope is space-separated"""
        if not v.strip():
            raise ValueError("scope cannot be empty")
        return v


class AuthorizationResponse(BaseModel):
    """OAuth authorization response (redirect parameters)"""
    code: str = Field(..., description="Authorization code")
    state: str = Field(..., description="CSRF protection token (echoed back)")


class AuthorizationErrorResponse(BaseModel):
    """OAuth authorization error response"""
    error: str = Field(..., description="Error code (e.g., 'invalid_request', 'unauthorized_client')")
    error_description: Optional[str] = Field(None, description="Human-readable error description")
    error_uri: Optional[str] = Field(None, description="URI with error details")
    state: Optional[str] = Field(None, description="CSRF protection token (if provided)")


# ============================================================================
# TOKEN REQUEST SCHEMAS
# ============================================================================

class TokenRequest(BaseModel):
    """OAuth token request (POST body, form-encoded)"""
    grant_type: GrantType = Field(..., description="Grant type (authorization_code or refresh_token)")

    # For authorization_code grant
    code: Optional[str] = Field(None, description="Authorization code (required for authorization_code grant)")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI (must match authorization request)")
    code_verifier: Optional[str] = Field(None, min_length=43, max_length=128, description="PKCE code verifier")

    # For refresh_token grant
    refresh_token: Optional[str] = Field(None, description="Refresh token (required for refresh_token grant)")

    # Client authentication
    client_id: str = Field(..., description="Client identifier")
    client_secret: Optional[str] = Field(None, description="Client secret (required for confidential clients)")

    # Optional
    scope: Optional[str] = Field(None, description="Requested scopes (for refresh, can downscope)")


class TokenResponse(BaseModel):
    """OAuth token response (successful)"""
    access_token: str = Field(..., description="Access token (JWT)")
    token_type: TokenType = Field(TokenType.BEARER, description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token lifetime in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token (if requested)")
    scope: str = Field(..., description="Granted scopes (space-separated)")

    # Custom claims
    org_id: Optional[UUID] = Field(None, description="Organization ID (if org-scoped token)")


class TokenErrorResponse(BaseModel):
    """OAuth token error response"""
    error: str = Field(..., description="Error code")
    error_description: Optional[str] = Field(None, description="Human-readable error description")
    error_uri: Optional[str] = Field(None, description="URI with error details")


# ============================================================================
# CONSENT SCHEMAS
# ============================================================================

class ConsentRequest(BaseModel):
    """User consent decision"""
    client_id: str = Field(..., description="Client requesting consent")
    scopes: List[str] = Field(..., min_items=1, description="Scopes to grant")
    organization_id: Optional[UUID] = Field(None, description="Organization context")
    approved: bool = Field(..., description="User approval decision")


class ConsentResponse(BaseModel):
    """Consent screen data"""
    client_name: str
    client_description: Optional[str]
    client_logo_uri: Optional[str]
    requested_scopes: List[str]
    scope_descriptions: dict[str, str]
    user_email: str
    organization_name: Optional[str]


class ConsentStatus(BaseModel):
    """Check if user has previously consented"""
    has_consent: bool
    granted_scopes: Optional[List[str]]
    needs_new_consent: bool


# ============================================================================
# REVOCATION SCHEMAS
# ============================================================================

class RevocationRequest(BaseModel):
    """OAuth token revocation request (RFC 7009)"""
    token: str = Field(..., description="Token to revoke (access or refresh)")
    token_type_hint: Optional[str] = Field(None, description="Token type hint (access_token or refresh_token)")
    client_id: str = Field(..., description="Client identifier")
    client_secret: Optional[str] = Field(None, description="Client secret (for confidential clients)")


# ============================================================================
# INTROSPECTION SCHEMAS
# ============================================================================

class IntrospectionRequest(BaseModel):
    """OAuth token introspection request (RFC 7662)"""
    token: str = Field(..., description="Token to introspect")
    token_type_hint: Optional[str] = Field(None, description="Token type hint")
    client_id: str = Field(..., description="Client identifier")
    client_secret: Optional[str] = Field(None, description="Client secret")


class IntrospectionResponse(BaseModel):
    """OAuth token introspection response"""
    active: bool = Field(..., description="Token is active")

    # Optional claims (if active)
    scope: Optional[str] = Field(None, description="Space-separated scopes")
    client_id: Optional[str] = Field(None, description="Client identifier")
    username: Optional[str] = Field(None, description="User email")
    token_type: Optional[str] = Field(None, description="Token type (Bearer)")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    sub: Optional[str] = Field(None, description="Subject (user_id)")
    aud: Optional[List[str]] = Field(None, description="Audience")
    iss: Optional[str] = Field(None, description="Issuer")
    jti: Optional[str] = Field(None, description="JWT ID")


# ============================================================================
# DISCOVERY SCHEMAS
# ============================================================================

class OAuthDiscoveryResponse(BaseModel):
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)"""
    issuer: str = Field(..., description="Authorization server identifier")
    authorization_endpoint: str = Field(..., description="Authorization endpoint URL")
    token_endpoint: str = Field(..., description="Token endpoint URL")
    revocation_endpoint: Optional[str] = Field(None, description="Token revocation endpoint URL")
    introspection_endpoint: Optional[str] = Field(None, description="Token introspection endpoint URL")

    response_types_supported: List[str] = Field(..., description="Supported response types")
    grant_types_supported: List[str] = Field(..., description="Supported grant types")
    token_endpoint_auth_methods_supported: List[str] = Field(..., description="Supported client auth methods")

    scopes_supported: Optional[List[str]] = Field(None, description="Available scopes")
    code_challenge_methods_supported: List[str] = Field(..., description="Supported PKCE methods")

    service_documentation: Optional[str] = Field(None, description="Documentation URL")


# ============================================================================
# SCOPE SCHEMAS
# ============================================================================

class ScopeDescription(BaseModel):
    """Scope metadata for consent screen"""
    scope: str = Field(..., description="Scope identifier (resource:action)")
    description: str = Field(..., description="Human-readable description")
    resource: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action on resource")


class ScopeValidationRequest(BaseModel):
    """Request to validate scopes"""
    requested_scopes: List[str]
    client_allowed_scopes: List[str]
    user_permissions: List[str]
    organization_id: Optional[UUID] = None


class ScopeValidationResponse(BaseModel):
    """Scope validation result"""
    granted_scopes: List[str]
    denied_scopes: List[str]
    reason: Optional[str] = None
