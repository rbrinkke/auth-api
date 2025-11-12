"""
OAuth 2.0 Token Revocation Endpoint

POST /oauth/revoke - Revoke access or refresh token

RFC 7009: OAuth 2.0 Token Revocation
"""

from typing import Optional
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse
import asyncpg

from app.db.connection import get_db_connection
from app.services.oauth_client_service import OAuthClientService, get_oauth_client_service
from app.core.logging_config import get_logger
from app.core.exceptions import InvalidCredentialsError

logger = get_logger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth 2.0"])


@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revoke_token(
    # Required parameters (form-encoded per OAuth spec)
    token: str = Form(..., description="Token to revoke"),

    # Optional parameters
    token_type_hint: Optional[str] = Form(None, description="Token type hint (access_token or refresh_token)"),

    # Client authentication
    client_id: str = Form(..., description="Client identifier"),
    client_secret: Optional[str] = Form(None, description="Client secret (for confidential clients)"),

    # Services
    client_service: OAuthClientService = Depends(get_oauth_client_service),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    OAuth 2.0 Token Revocation Endpoint (RFC 7009).

    Revokes access or refresh tokens. Per OAuth spec, this endpoint ALWAYS
    returns 200 OK, even if the token doesn't exist or is already revoked
    (prevents token enumeration attacks).

    Security:
    - Client authentication required
    - Always returns 200 OK (no information leakage)
    - Validates token belongs to client

    Args:
        token: Token to revoke
        token_type_hint: Optional hint (access_token or refresh_token)
        client_id: Client identifier
        client_secret: Client secret (for confidential clients)

    Returns:
        200 OK (always)
    """
    logger.info("oauth_revoke_request",
               client_id=client_id,
               token_type_hint=token_type_hint)

    # ========================================================================
    # STEP 1: AUTHENTICATE CLIENT
    # ========================================================================

    try:
        client = await client_service.authenticate_client(
            client_id=client_id,
            client_secret=client_secret
        )
    except InvalidCredentialsError:
        logger.warning("oauth_revoke_client_auth_failed", client_id=client_id)
        # Per RFC 7009: Return 401 for client auth failure
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "invalid_client",
                "error_description": "Client authentication failed"
            },
            headers={"WWW-Authenticate": 'Basic realm="OAuth 2.0"'}
        )

    logger.debug("oauth_revoke_client_authenticated", client_id=client_id)

    # ========================================================================
    # STEP 2: DECODE AND REVOKE TOKEN
    # ========================================================================

    try:
        from app.services.token_service import TokenService
        from app.config import get_settings
        from app.core.tokens import TokenHelper
        from app.db.procedures import sp_revoke_refresh_token
        from uuid import UUID

        token_service = TokenService(
            settings=get_settings(),
            token_helper=TokenHelper(get_settings()),
            db=db
        )

        # Decode token to extract claims
        payload = token_service.token_helper.decode_token(token)

        token_type = payload.get("type")
        user_id = UUID(payload.get("sub"))
        token_client_id = payload.get("client_id")

        # Validate token belongs to this client
        if token_client_id and token_client_id != client.client_id:
            logger.warning("oauth_revoke_client_mismatch",
                          token_client=token_client_id,
                          request_client=client.client_id)
            # Per RFC 7009: Still return 200 OK
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={}
            )

        # Revoke based on token type
        if token_type == "refresh":
            # Revoke refresh token from database
            await sp_revoke_refresh_token(db, user_id, token)

            logger.info("oauth_token_revoked",
                       token_type="refresh",
                       user_id=str(user_id),
                       client_id=client.client_id)

        elif token_type == "access":
            # For access tokens: Add JTI to blacklist in Redis
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                import time
                from app.core.redis_client import get_redis_client

                redis_client = get_redis_client()

                # Calculate TTL (time until token expires)
                ttl = int(exp - time.time())

                if ttl > 0:
                    # Add to blacklist with TTL
                    redis_client.setex(f"blacklist:jti:{jti}", ttl, "1")

                    logger.info("oauth_token_revoked",
                               token_type="access",
                               user_id=str(user_id),
                               client_id=client.client_id,
                               jti=jti,
                               ttl=ttl)
                else:
                    logger.debug("oauth_token_already_expired",
                                jti=jti,
                                user_id=str(user_id))
            else:
                logger.warning("oauth_token_missing_jti_or_exp",
                              user_id=str(user_id))

        else:
            logger.warning("oauth_revoke_unknown_token_type",
                          token_type=token_type)

    except Exception as e:
        # Per RFC 7009: Log error but still return 200 OK
        logger.warning("oauth_revoke_token_decode_failed",
                      error=str(e),
                      client_id=client.client_id)

    # ========================================================================
    # STEP 3: RETURN 200 OK (ALWAYS)
    # ========================================================================

    # Per RFC 7009 Section 2.2:
    # "The authorization server responds with HTTP status code 200
    # if the token has been revoked successfully or if the client
    # submitted an invalid token."
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={}
    )
