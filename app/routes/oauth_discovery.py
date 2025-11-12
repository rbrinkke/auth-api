"""
OAuth 2.0 Authorization Server Metadata (Discovery)

GET /.well-known/oauth-authorization-server - Server metadata

RFC 8414: OAuth 2.0 Authorization Server Metadata
"""

from fastapi import APIRouter, Depends
from app.config import Settings, get_settings
from app.schemas.oauth import OAuthDiscoveryResponse
from app.services.scope_service import ScopeService, get_scope_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["OAuth 2.0 Discovery"])


@router.get(
    "/.well-known/oauth-authorization-server",
    response_model=OAuthDiscoveryResponse,
    summary="OAuth 2.0 Authorization Server Metadata",
    description="RFC 8414: OAuth 2.0 Authorization Server Metadata"
)
async def oauth_discovery(
    settings: Settings = Depends(get_settings),
    scope_service: ScopeService = Depends(get_scope_service)
):
    """
    OAuth 2.0 Authorization Server Metadata (RFC 8414).

    This endpoint provides machine-readable metadata about the OAuth
    authorization server's capabilities and configuration.

    Clients can use this endpoint for automatic configuration.

    Returns:
        OAuthDiscoveryResponse with server metadata
    """
    logger.info("oauth_discovery_request")

    # Base URL for endpoints
    base_url = settings.FRONTEND_URL.rstrip('/')

    # Get all available scopes
    available_scopes = scope_service.get_all_available_scopes()

    metadata = OAuthDiscoveryResponse(
        # Issuer identifier
        issuer=base_url,

        # Endpoints
        authorization_endpoint=f"{base_url}/oauth/authorize",
        token_endpoint=f"{base_url}/oauth/token",
        revocation_endpoint=f"{base_url}/oauth/revoke",

        # Supported features
        response_types_supported=["code"],
        grant_types_supported=["authorization_code", "refresh_token"],
        token_endpoint_auth_methods_supported=[
            "client_secret_post",  # client_secret in POST body
            "client_secret_basic",  # client_secret in Basic Auth header
            "none"  # Public clients (PKCE only)
        ],

        # PKCE support
        code_challenge_methods_supported=["S256", "plain"],

        # Available scopes
        scopes_supported=available_scopes,

        # Documentation
        service_documentation=f"{base_url}/docs"
    )

    logger.info("oauth_discovery_response",
               scopes_count=len(available_scopes))

    return metadata
