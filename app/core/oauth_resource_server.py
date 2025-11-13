"""
OAuth 2.0 Resource Server Helper

This module provides token validation and scope checking for OAuth resource servers.
Use this in your resource servers (image-api, activity-api, etc.) to validate
access tokens and enforce scope-based authorization.

Example Usage (in image-api):

    from oauth_resource_server import OAuth2ResourceServer, require_scope

    # Initialize
    oauth = OAuth2ResourceServer(
        jwt_secret_key=settings.JWT_SECRET_KEY,
        jwt_algorithm="HS256",
        redis_client=redis_client  # Optional, for revocation checking
    )

    # Protect endpoint with scope
    @app.post("/images", dependencies=[Depends(oauth.require_scope("image:upload"))])
    async def upload_image(
        data: ImageCreate,
        token_data: dict = Depends(oauth.require_scope("image:upload"))
    ):
        user_id = token_data["sub"]
        org_id = token_data.get("org_id")
        client_id = token_data.get("client_id")

        # Your business logic here
        image = await create_image(user_id, org_id, data)

        return image
"""

from typing import Optional, List, Callable
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError
import redis

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Security scheme for Bearer tokens
security = HTTPBearer()


class OAuth2ResourceServer:
    """
    OAuth 2.0 Resource Server token validator.

    Validates OAuth access tokens and enforces scope-based authorization.
    """

    def __init__(
        self,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        issuer: Optional[str] = None,
        audience: Optional[List[str]] = None,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize OAuth 2.0 Resource Server.

        Args:
            jwt_secret_key: JWT secret key for validation
            jwt_algorithm: JWT algorithm (default: HS256)
            issuer: Expected issuer (iss claim)
            audience: Expected audience (aud claim)
            redis_client: Redis client for revocation checking (optional)
        """
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.issuer = issuer
        self.audience = audience or ["https://api.activity.com"]
        self.redis_client = redis_client

    def require_scope(self, required_scope: str) -> Callable:
        """
        Create dependency for scope-based authorization.

        This is a dependency factory that returns an async function.
        Use it with FastAPI's Depends() to protect endpoints.

        Args:
            required_scope: Required scope (e.g., "activity:create")

        Returns:
            Async dependency function

        Example:
            @app.post("/activities", dependencies=[Depends(oauth.require_scope("activity:create"))])
            async def create_activity(token: dict = Depends(oauth.require_scope("activity:create"))):
                user_id = token["sub"]
                # ...
        """
        async def validate_token(
            credentials: HTTPAuthorizationCredentials = Security(security)
        ) -> dict:
            """Validate token and check scope"""
            token = credentials.credentials

            try:
                # Decode and validate JWT
                payload = self._decode_token(token)

                # Validate token type
                if payload.get("type") != "access":
                    logger.warning("oauth_invalid_token_type",
                                  expected="access",
                                  got=payload.get("type"))
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token type",
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # Validate scope
                token_scopes = self._extract_scopes(payload)

                if required_scope not in token_scopes:
                    logger.warning("oauth_insufficient_scope",
                                  required=required_scope,
                                  available=token_scopes,
                                  user_id=payload.get("sub"))
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient scope: {required_scope}",
                        headers={
                            "WWW-Authenticate": f'Bearer scope="{required_scope}"'
                        }
                    )

                # Check revocation (if Redis available)
                if self.redis_client:
                    jti = payload.get("jti")
                    if jti and self._is_revoked(jti):
                        logger.warning("oauth_token_revoked",
                                      jti=jti,
                                      user_id=payload.get("sub"))
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has been revoked",
                            headers={"WWW-Authenticate": "Bearer"}
                        )

                logger.debug("oauth_token_validated",
                           user_id=payload.get("sub"),
                           client_id=payload.get("client_id"),
                           scope=required_scope)

                return payload

            except PyJWTError as e:
                logger.warning("oauth_token_validation_failed",
                              error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"}
                )

        return validate_token

    def require_any_scope(self, *required_scopes: str) -> Callable:
        """
        Create dependency for OR-based scope authorization.

        User must have at least ONE of the specified scopes.

        Args:
            *required_scopes: Required scopes (user needs at least one)

        Returns:
            Async dependency function

        Example:
            # User needs either activity:read OR activity:update
            @app.get("/activities/{id}", dependencies=[
                Depends(oauth.require_any_scope("activity:read", "activity:update"))
            ])
        """
        async def validate_token(
            credentials: HTTPAuthorizationCredentials = Security(security)
        ) -> dict:
            token = credentials.credentials

            try:
                payload = self._decode_token(token)

                if payload.get("type") != "access":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token type",
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                token_scopes = self._extract_scopes(payload)

                # Check if user has ANY of the required scopes
                has_scope = any(scope in token_scopes for scope in required_scopes)

                if not has_scope:
                    logger.warning("oauth_insufficient_scope_any",
                                  required_any=list(required_scopes),
                                  available=token_scopes)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient scope (need one of: {', '.join(required_scopes)})",
                        headers={
                            "WWW-Authenticate": f'Bearer scope="{" ".join(required_scopes)}"'
                        }
                    )

                # Check revocation
                if self.redis_client:
                    jti = payload.get("jti")
                    if jti and self._is_revoked(jti):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has been revoked",
                            headers={"WWW-Authenticate": "Bearer"}
                        )

                return payload

            except PyJWTError as e:
                logger.warning("oauth_token_validation_failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"}
                )

        return validate_token

    def _decode_token(self, token: str) -> dict:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload

        Raises:
            PyJWTError: If token is invalid
        """
        # JWT decode options
        options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "require": ["sub", "exp", "iat"]
        }

        # Decode token
        payload = jwt.decode(
            token,
            self.jwt_secret_key,
            algorithms=[self.jwt_algorithm],
            options=options,
            issuer=self.issuer,
            audience=self.audience
        )

        return payload

    def _extract_scopes(self, payload: dict) -> List[str]:
        """
        Extract scopes from token payload.

        Args:
            payload: Decoded JWT payload

        Returns:
            List of scopes
        """
        scope_string = payload.get("scope", "")
        scopes = scope_string.split() if scope_string else []
        return scopes

    def _is_revoked(self, jti: str) -> bool:
        """
        Check if token is revoked.

        Args:
            jti: JWT ID

        Returns:
            True if revoked, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            return self.redis_client.exists(f"blacklist:jti:{jti}")
        except Exception as e:
            logger.error("oauth_revocation_check_failed",
                        jti=jti,
                        error=str(e))
            # Fail open (assume not revoked) to avoid DoS
            return False


# ============================================================================
# DEPENDENCY FOR AUTH-API GROUP ENDPOINTS
# ============================================================================

async def get_current_principal(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> dict:
    """
    OAuth Bearer token validator for Auth-API internal use.

    Used by group endpoints to accept OAuth Bearer tokens from services like Chat-API.

    Returns:
        dict: {
            "type": "service" | "user",
            "client_id": str | None,
            "user_id": str | None,
            "scopes": List[str],
            "org_id": str | None
        }

    Raises:
        HTTPException 401: Invalid/missing token
    """
    if not credentials:
        logger.warning("oauth_no_bearer_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    from app.config import get_settings
    from app.core.tokens import TokenHelper

    settings = get_settings()
    token_helper = TokenHelper(settings)

    try:
        # Decode and validate JWT
        payload = token_helper.decode_token(credentials.credentials)

        # Verify token type
        if payload.get("type") != "access":
            logger.warning("oauth_invalid_token_type",
                          expected="access",
                          got=payload.get("type"))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Extract claims
        from uuid import UUID
        sub = payload.get("sub")
        scope_str = payload.get("scope", "")
        scopes = scope_str.split() if scope_str else []
        org_id = payload.get("org_id")

        # Determine principal type by trying to parse sub as UUID
        # - If sub is a UUID → USER token (user authentication)
        # - If sub is NOT a UUID → SERVICE token (client_credentials with sub=client_id)
        try:
            user_uuid = UUID(sub)
            # This is a USER token
            principal = {
                "type": "user",
                "user_id": str(user_uuid),
                "client_id": None,
                "org_id": org_id,
                "scopes": scopes
            }
            logger.info("oauth_user_authenticated",
                       user_id=str(user_uuid),
                       org_id=org_id,
                       scopes=scopes)
        except (ValueError, TypeError):
            # sub is NOT a UUID → SERVICE token (OAuth2 Client Credentials)
            # In Client Credentials flow, sub = client_id
            client_id = sub
            principal = {
                "type": "service",
                "client_id": client_id,
                "user_id": None,
                "org_id": None,
                "scopes": scopes
            }
            logger.info("oauth_service_authenticated",
                       client_id=client_id,
                       scopes=scopes)

        return principal

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("oauth_token_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_user_id(token_data: dict) -> str:
    """Extract user_id from validated token data"""
    return token_data.get("sub")


def extract_organization_id(token_data: dict) -> Optional[str]:
    """Extract organization_id from validated token data"""
    return token_data.get("org_id")


def extract_client_id(token_data: dict) -> Optional[str]:
    """Extract client_id from validated token data"""
    return token_data.get("client_id")


def extract_scopes(token_data: dict) -> List[str]:
    """Extract scopes from validated token data"""
    scope_string = token_data.get("scope", "")
    return scope_string.split() if scope_string else []


# ============================================================================
# EXAMPLE USAGE (Copy to your resource server)
# ============================================================================

"""
Example: image-api using OAuth2ResourceServer

# app/main.py

from fastapi import FastAPI, Depends
from oauth_resource_server import OAuth2ResourceServer, extract_user_id, extract_organization_id
from app.config import get_settings
from app.core.redis_client import get_redis_client

app = FastAPI()
settings = get_settings()

# Initialize OAuth validator
oauth = OAuth2ResourceServer(
    jwt_secret_key=settings.JWT_SECRET_KEY,
    jwt_algorithm="HS256",
    issuer="https://auth.activity.com",
    audience=["https://api.activity.com"],
    redis_client=get_redis_client()
)

# Protect endpoints with scopes
@app.post("/images")
async def upload_image(
    data: ImageCreate,
    token_data: dict = Depends(oauth.require_scope("image:upload"))
):
    user_id = extract_user_id(token_data)
    org_id = extract_organization_id(token_data)
    client_id = extract_client_id(token_data)

    logger.info("image_upload_start",
               user_id=user_id,
               org_id=org_id,
               client_id=client_id)

    image = await image_service.create(
        user_id=user_id,
        org_id=org_id,
        data=data
    )

    return image


@app.get("/images/{image_id}")
async def get_image(
    image_id: UUID,
    token_data: dict = Depends(oauth.require_scope("image:read"))
):
    user_id = extract_user_id(token_data)
    org_id = extract_organization_id(token_data)

    image = await image_service.get(image_id, user_id, org_id)
    return image


@app.delete("/images/{image_id}")
async def delete_image(
    image_id: UUID,
    token_data: dict = Depends(oauth.require_scope("image:delete"))
):
    user_id = extract_user_id(token_data)
    org_id = extract_organization_id(token_data)

    await image_service.delete(image_id, user_id, org_id)
    return {"status": "deleted"}


# Multiple scopes example (user needs at least ONE)
@app.get("/activities/{id}")
async def get_activity(
    id: UUID,
    token_data: dict = Depends(oauth.require_any_scope("activity:read", "activity:update"))
):
    # User has either activity:read OR activity:update
    return await activity_service.get(id)
"""
