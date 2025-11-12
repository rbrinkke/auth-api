"""
OAuth 2.0 Token Endpoint

POST /oauth/token - Token request (authorization code → access token)

RFC 6749 Section 3.2: Token Endpoint
RFC 7636: PKCE for OAuth 2.0
RFC 6749 Section 6: Refreshing an Access Token
"""

from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse
import asyncpg

from app.db.connection import get_db_connection
from app.services.oauth_client_service import OAuthClientService, get_oauth_client_service
from app.services.authorization_code_service import AuthorizationCodeService, get_authorization_code_service
from app.services.token_service import TokenService
from app.services.scope_service import ScopeService, get_scope_service
from app.config import get_settings
from app.core.tokens import TokenHelper
from app.core.logging_config import get_logger
from app.core.exceptions import InvalidTokenError, InvalidCredentialsError
from app.schemas.oauth import TokenResponse, TokenErrorResponse, GrantType

logger = get_logger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth 2.0"])


@router.post("/token", response_model=TokenResponse)
async def token_endpoint(
    # Required parameters (form-encoded per OAuth spec)
    grant_type: str = Form(..., description="Grant type (authorization_code or refresh_token)"),

    # For authorization_code grant
    code: Optional[str] = Form(None, description="Authorization code"),
    redirect_uri: Optional[str] = Form(None, description="Redirect URI (must match authorization request)"),
    code_verifier: Optional[str] = Form(None, description="PKCE code verifier"),

    # For refresh_token grant
    refresh_token: Optional[str] = Form(None, description="Refresh token"),

    # Client authentication
    client_id: str = Form(..., description="Client identifier"),
    client_secret: Optional[str] = Form(None, description="Client secret (for confidential clients)"),

    # Optional
    scope: Optional[str] = Form(None, description="Requested scopes (for downscoping during refresh)"),

    # Services
    client_service: OAuthClientService = Depends(get_oauth_client_service),
    authz_code_service: AuthorizationCodeService = Depends(get_authorization_code_service),
    scope_service: ScopeService = Depends(get_scope_service),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    OAuth 2.0 Token Endpoint.

    Supports two grant types:
    1. authorization_code: Exchange authorization code for tokens (with PKCE validation)
    2. refresh_token: Refresh access token using refresh token

    Security:
    - Client authentication (public: PKCE only, confidential: client_secret + PKCE)
    - PKCE validation (prevents code interception)
    - Single-use authorization codes
    - Token rotation (refresh tokens)

    Returns:
        TokenResponse with access_token, refresh_token, expires_in, scope
    """
    logger.info("oauth_token_request",
               grant_type=grant_type,
               client_id=client_id)

    try:
        # ====================================================================
        # STEP 1: AUTHENTICATE CLIENT
        # ====================================================================

        try:
            client = await client_service.authenticate_client(
                client_id=client_id,
                client_secret=client_secret
            )
        except InvalidCredentialsError:
            logger.warning("oauth_token_client_auth_failed", client_id=client_id)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_client",
                    "error_description": "Client authentication failed"
                },
                headers={"WWW-Authenticate": 'Basic realm="OAuth 2.0"'}
            )

        logger.debug("oauth_token_client_authenticated", client_id=client_id)

        # ====================================================================
        # STEP 2: HANDLE GRANT TYPE
        # ====================================================================

        if grant_type == "authorization_code":
            return await _handle_authorization_code_grant(
                code=code,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
                client=client,
                client_service=client_service,
                authz_code_service=authz_code_service,
                db=db
            )

        elif grant_type == "refresh_token":
            return await _handle_refresh_token_grant(
                refresh_token=refresh_token,
                scope=scope,
                client=client,
                scope_service=scope_service,
                db=db
            )

        else:
            logger.warning("oauth_token_unsupported_grant_type",
                          grant_type=grant_type)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "unsupported_grant_type",
                    "error_description": f"Unsupported grant_type: {grant_type}"
                }
            )

    except InvalidTokenError as e:
        logger.warning("oauth_token_invalid_grant",
                      error=str(e),
                      grant_type=grant_type)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_grant",
                "error_description": str(e)
            }
        )

    except Exception as e:
        logger.error("oauth_token_unexpected_error",
                    error=str(e),
                    grant_type=grant_type,
                    exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "server_error",
                "error_description": "An unexpected error occurred"
            }
        )


async def _handle_authorization_code_grant(
    code: Optional[str],
    redirect_uri: Optional[str],
    code_verifier: Optional[str],
    client,
    client_service: OAuthClientService,
    authz_code_service: AuthorizationCodeService,
    db: asyncpg.Connection
) -> JSONResponse:
    """
    Handle authorization_code grant type.

    Flow:
    1. Validate required parameters
    2. Validate and consume authorization code (atomic, single-use)
    3. Validate PKCE challenge
    4. Validate redirect_uri matches
    5. Generate tokens
    """
    logger.info("oauth_token_authz_code_grant", client_id=client.client_id)

    # Validate required parameters
    if not code:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_request",
                "error_description": "Missing parameter: code"
            }
        )

    if not redirect_uri:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_request",
                "error_description": "Missing parameter: redirect_uri"
            }
        )

    if not code_verifier:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_request",
                "error_description": "Missing parameter: code_verifier (PKCE required)"
            }
        )

    # Validate redirect_uri against client's registered URIs
    if not client_service.validate_redirect_uri(client, redirect_uri):
        logger.error("oauth_token_redirect_uri_mismatch",
                    client_id=client.client_id,
                    redirect_uri=redirect_uri)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_grant",
                "error_description": "redirect_uri does not match registered URI"
            }
        )

    # Validate and consume authorization code (includes PKCE validation)
    try:
        code_record = await authz_code_service.validate_and_consume_code(
            code=code,
            client_id=client.client_id,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier
        )
    except InvalidTokenError as e:
        logger.warning("oauth_token_code_validation_failed",
                      client_id=client.client_id,
                      error=str(e))
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_grant",
                "error_description": str(e)
            }
        )

    logger.info("oauth_token_code_validated",
               client_id=client.client_id,
               user_id=str(code_record.user_id))

    # Generate tokens
    from app.services.token_service import TokenService
    from app.config import get_settings
    from app.core.tokens import TokenHelper

    token_service = TokenService(
        settings=get_settings(),
        token_helper=TokenHelper(get_settings()),
        db=db
    )

    token_response = await token_service.create_oauth_token_response(
        user_id=code_record.user_id,
        client_id=client.client_id,
        scopes=code_record.scopes,
        org_id=code_record.organization_id,
        audience=["https://api.activity.com"]
    )

    logger.info("oauth_token_issued",
               client_id=client.client_id,
               user_id=str(code_record.user_id),
               scopes=code_record.scopes)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=token_response.model_dump(mode='json')
    )


async def _handle_refresh_token_grant(
    refresh_token: Optional[str],
    scope: Optional[str],
    client,
    scope_service: ScopeService,
    db: asyncpg.Connection
) -> JSONResponse:
    """
    Handle refresh_token grant type.

    Flow:
    1. Validate required parameters
    2. Decode and validate refresh token
    3. Validate client_id matches
    4. Check if token is revoked
    5. Handle scope downscoping (if requested)
    6. Generate new tokens (token rotation)
    """
    logger.info("oauth_token_refresh_grant", client_id=client.client_id)

    # Validate required parameters
    if not refresh_token:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_request",
                "error_description": "Missing parameter: refresh_token"
            }
        )

    # Decode and validate refresh token
    from app.services.token_service import TokenService
    from app.config import get_settings
    from app.core.tokens import TokenHelper

    token_service = TokenService(
        settings=get_settings(),
        token_helper=TokenHelper(get_settings()),
        db=db
    )

    try:
        payload = token_service.token_helper.decode_token(refresh_token)

        # Validate token type
        if payload.get("type") != "refresh":
            logger.warning("oauth_token_invalid_token_type",
                          expected="refresh",
                          got=payload.get("type"))
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Invalid token type"
                }
            )

        # Extract claims
        user_id = payload.get("sub")
        token_client_id = payload.get("client_id")
        original_scopes = payload.get("scope", "").split()
        org_id = payload.get("org_id")

        # Validate client_id matches
        if token_client_id != client.client_id:
            logger.warning("oauth_token_client_mismatch",
                          token_client_id=token_client_id,
                          request_client_id=client.client_id)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Client mismatch"
                }
            )

        # Check if token is revoked
        from app.db.procedures import sp_validate_refresh_token
        from uuid import UUID

        is_valid = await sp_validate_refresh_token(db, UUID(user_id), refresh_token)

        if not is_valid:
            logger.warning("oauth_token_revoked_or_expired",
                          user_id=user_id,
                          client_id=client.client_id)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Token has been revoked or expired"
                }
            )

        # Handle scope downscoping
        new_scopes = original_scopes

        if scope:
            requested_scopes = scope_service.parse_scope_string(scope)

            # Validate downscoping (new scopes must be subset of original)
            is_valid_downscope = await scope_service.validate_scope_downscoping(
                original_scopes=original_scopes,
                requested_scopes=requested_scopes
            )

            if not is_valid_downscope:
                logger.warning("oauth_token_invalid_downscope",
                              original_scopes=original_scopes,
                              requested_scopes=requested_scopes)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "invalid_scope",
                        "error_description": "Requested scopes exceed original grant"
                    }
                )

            new_scopes = requested_scopes
            logger.info("oauth_token_downscoped",
                       original_count=len(original_scopes),
                       new_count=len(new_scopes))

        # Revoke old refresh token (token rotation)
        from app.db.procedures import sp_revoke_refresh_token

        await sp_revoke_refresh_token(db, UUID(user_id), refresh_token)

        logger.info("oauth_token_old_refresh_revoked",
                   user_id=user_id,
                   client_id=client.client_id)

        # Generate new tokens
        token_response = await token_service.create_oauth_token_response(
            user_id=UUID(user_id),
            client_id=client.client_id,
            scopes=new_scopes,
            org_id=UUID(org_id) if org_id else None,
            audience=["https://api.activity.com"]
        )

        logger.info("oauth_token_refreshed",
                   user_id=user_id,
                   client_id=client.client_id,
                   scopes=new_scopes)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=token_response.model_dump(mode='json')
        )

    except InvalidTokenError as e:
        logger.warning("oauth_token_decode_failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "invalid_grant",
                "error_description": "Invalid refresh token"
            }
        )
