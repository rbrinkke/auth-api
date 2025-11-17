from datetime import timedelta
from typing import List, Optional
from fastapi import Depends
import asyncpg
import uuid
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.config import Settings, get_settings
from app.core.tokens import TokenHelper
from app.core.exceptions import UserNotFoundError, InvalidTokenError, TokenExpiredError
from app.schemas.auth import TokenResponse
from app.schemas.oauth import TokenResponse as OAuthTokenResponse
from app.core.logging_config import get_logger
from app.middleware.correlation import trace_id_var

logger = get_logger(__name__)

class TokenService:
    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        token_helper: TokenHelper = Depends(TokenHelper),
        db: asyncpg.Connection = Depends(get_db_connection)
    ):
        self.settings = settings
        self.token_helper = token_helper
        self.db = db

    def create_access_token(self, user_id: UUID, org_id: UUID | None = None) -> str:
        """
        Create access token.

        Args:
            user_id: User ID
            org_id: Optional organization ID for org-scoped token

        Returns:
            JWT access token string
        """
        logger.debug("token_creating_access_token",
                    user_id=str(user_id),
                    org_id=str(org_id) if org_id else None)
        expires_delta = timedelta(minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        logger.debug("token_access_expires_delta_set", expires_minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        data = {"sub": str(user_id), "type": "access"}
        if org_id:
            data["org_id"] = str(org_id)

        token = self.token_helper.create_token(
            data=data,
            expires_delta=expires_delta
        )
        logger.debug("token_access_token_generated", user_id=str(user_id), token_length=len(token))
        logger.info("access_token_created",
                   user_id=str(user_id),
                   org_id=str(org_id) if org_id else None,
                   expires_minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        return token

    async def create_refresh_token(self, user_id: UUID, org_id: UUID | None = None) -> str:
        """
        Create refresh token.

        Args:
            user_id: User ID
            org_id: Optional organization ID for org-scoped token

        Returns:
            JWT refresh token string
        """
        logger.debug("token_creating_refresh_token",
                    user_id=str(user_id),
                    org_id=str(org_id) if org_id else None)
        expires_delta = timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())
        logger.debug("token_refresh_jti_generated", user_id=str(user_id), jti=jti)

        data = {"sub": str(user_id), "type": "refresh", "jti": jti}
        if org_id:
            data["org_id"] = str(org_id)

        token = self.token_helper.create_token(
            data=data,
            expires_delta=expires_delta
        )
        logger.debug("token_refresh_token_generated", user_id=str(user_id), token_length=len(token))
        logger.debug("token_saving_refresh_token_to_db", user_id=str(user_id), jti=jti)
        await procedures.sp_save_refresh_token(self.db, user_id, token, expires_delta)
        logger.debug("token_refresh_token_saved_to_db", user_id=str(user_id), jti=jti)
        logger.info("refresh_token_created",
                   user_id=str(user_id),
                   org_id=str(org_id) if org_id else None,
                   jti=jti,
                   expires_days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        return token

    def create_verification_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(minutes=self.settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "verification"},
            expires_delta=expires_delta
        )
        logger.info("verification_token_created",
                   user_id=str(user_id),
                   expires_minutes=self.settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
        return token

    def create_password_reset_token(self, email: str) -> str:
        expires_delta = timedelta(minutes=self.settings.RESET_TOKEN_EXPIRE_MINUTES)
        token = self.token_helper.create_token(
            data={"sub": email, "type": "reset"},
            expires_delta=expires_delta
        )
        logger.info("password_reset_token_created",
                   email=email,
                   expires_minutes=self.settings.RESET_TOKEN_EXPIRE_MINUTES)
        return token

    def create_2fa_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(minutes=5)
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "2fa_pre_auth"},
            expires_delta=expires_delta
        )
        logger.info("2fa_token_created",
                   user_id=str(user_id),
                   expires_minutes=5)
        return token

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Preserves org_id from original token if present.

        Args:
            refresh_token: Current refresh token

        Returns:
            TokenResponse with new tokens

        Raises:
            InvalidTokenError: If token is invalid or revoked
        """
        logger.info("token_refresh_start")

        payload = self.token_helper.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            logger.warning("token_refresh_failed", reason="invalid_token_type", expected="refresh", got=payload.get("type"))
            raise InvalidTokenError("Invalid token type")

        user_id_str = payload.get("sub")
        user_id = UUID(user_id_str)
        old_jti = payload.get("jti")

        # Preserve org_id if present in original token
        org_id = UUID(payload["org_id"]) if payload.get("org_id") else None

        if not await procedures.sp_validate_refresh_token(self.db, user_id, refresh_token):
            logger.warning("token_refresh_failed", reason="token_not_found_or_revoked", user_id=str(user_id), jti=old_jti)
            raise InvalidTokenError("Token not found or revoked")

        await procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)
        logger.info("old_refresh_token_revoked", user_id=str(user_id), old_jti=old_jti)

        new_access_token = self.create_access_token(user_id, org_id)
        new_refresh_token = await self.create_refresh_token(user_id, org_id)

        logger.info("token_refresh_complete",
                   user_id=str(user_id),
                   org_id=str(org_id) if org_id else None)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user_id=user_id,
            org_id=org_id
        )

    def get_user_id_from_token(self, token: str, expected_type: str) -> UUID:
        logger.info("get_user_id_from_token_start", expected_type=expected_type)

        try:
            payload = self.token_helper.decode_token(token)

            if payload.get("type") != expected_type:
                logger.warning("get_user_id_from_token_failed",
                             reason="invalid_token_type",
                             expected=expected_type,
                             got=payload.get("type"))
                raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")

            user_id = UUID(payload.get("sub"))
            logger.info("get_user_id_from_token_success",
                       user_id=str(user_id),
                       token_type=expected_type)
            return user_id
        except (ValueError, TypeError) as e:
            logger.error("get_user_id_from_token_failed",
                        reason="invalid_subject",
                        error=str(e),
                        exc_info=True)
            raise InvalidTokenError("Invalid subject in token")

    def get_email_from_token(self, token: str, expected_type: str) -> str:
        logger.info("get_email_from_token_start", expected_type=expected_type)

        try:
            payload = self.token_helper.decode_token(token)

            if payload.get("type") != expected_type:
                logger.warning("get_email_from_token_failed",
                             reason="invalid_token_type",
                             expected=expected_type,
                             got=payload.get("type"))
                raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")

            email = payload.get("sub")
            if not email:
                logger.warning("get_email_from_token_failed", reason="missing_subject")
                raise InvalidTokenError("Invalid subject in token")

            logger.info("get_email_from_token_success",
                       email=email,
                       token_type=expected_type)
            return email
        except Exception as e:
            logger.error("get_email_from_token_failed",
                        error=str(e),
                        exc_info=True)
            raise

    # ========================================================================
    # OAUTH 2.0 TOKEN METHODS
    # ========================================================================

    def create_oauth_access_token(
        self,
        user_id: UUID,
        client_id: str,
        scopes: List[str],
        org_id: Optional[UUID] = None,
        audience: Optional[List[str]] = None
    ) -> str:
        """
        Create OAuth 2.0 access token with enhanced claims.

        OAuth claims (RFC 8693, RFC 9068):
        - iss: Issuer (Authorization Server)
        - sub: Subject (User ID)
        - aud: Audience (Resource Servers)
        - exp: Expiration Time
        - iat: Issued At
        - jti: JWT ID (for revocation)
        - scope: Granted scopes (space-separated)
        - client_id: Client identifier
        - azp: Authorized Party (same as client_id)

        Args:
            user_id: User ID
            client_id: OAuth client identifier
            scopes: Granted scopes
            org_id: Optional organization ID
            audience: Optional audience (resource servers)

        Returns:
            JWT access token with OAuth claims
        """
        logger.debug("oauth_access_token_creating",
                    user_id=str(user_id),
                    client_id=client_id,
                    scopes_count=len(scopes))

        expires_delta = timedelta(minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = str(uuid.uuid4())

        # Build OAuth claims
        data = {
            # Standard JWT claims
            "iss": self.settings.FRONTEND_URL.rstrip('/'),  # Issuer
            "sub": str(user_id),  # Subject
            "aud": audience or ["https://api.activity.com"],  # Audience
            "jti": jti,  # JWT ID (for revocation)

            # OAuth 2.0 claims
            "scope": " ".join(scopes),  # Space-separated scopes
            "client_id": client_id,  # Client identifier
            "azp": client_id,  # Authorized Party

            # Custom claims
            "type": "access",
        }

        # Add org_id if present
        if org_id:
            data["org_id"] = str(org_id)

        token = self.token_helper.create_token(
            data=data,
            expires_delta=expires_delta
        )

        logger.info("oauth_access_token_created",
                   user_id=str(user_id),
                   client_id=client_id,
                   org_id=str(org_id) if org_id else None,
                   scopes=scopes,
                   jti=jti,
                   expires_minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        return token

    async def create_oauth_refresh_token(
        self,
        user_id: UUID,
        client_id: str,
        scopes: List[str],
        org_id: Optional[UUID] = None
    ) -> str:
        """
        Create OAuth 2.0 refresh token.

        Stores client_id with refresh token for validation during refresh flow.

        Args:
            user_id: User ID
            client_id: OAuth client identifier
            scopes: Granted scopes
            org_id: Optional organization ID

        Returns:
            JWT refresh token
        """
        logger.debug("oauth_refresh_token_creating",
                    user_id=str(user_id),
                    client_id=client_id)

        expires_delta = timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())

        data = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": jti,
            "client_id": client_id,
            "scope": " ".join(scopes),  # Store scopes for downscoping
        }

        if org_id:
            data["org_id"] = str(org_id)

        token = self.token_helper.create_token(
            data=data,
            expires_delta=expires_delta
        )

        # Save to database
        await procedures.sp_save_refresh_token(self.db, user_id, token, expires_delta)

        logger.info("oauth_refresh_token_created",
                   user_id=str(user_id),
                   client_id=client_id,
                   org_id=str(org_id) if org_id else None,
                   jti=jti,
                   expires_days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        return token

    async def create_oauth_token_response(
        self,
        user_id: UUID,
        client_id: str,
        scopes: List[str],
        org_id: Optional[UUID] = None,
        audience: Optional[List[str]] = None
    ) -> OAuthTokenResponse:
        """
        Create complete OAuth token response (access + refresh).

        Args:
            user_id: User ID
            client_id: OAuth client identifier
            scopes: Granted scopes
            org_id: Optional organization ID
            audience: Optional audience

        Returns:
            OAuthTokenResponse with access_token, refresh_token, scope, etc.
        """
        logger.info("oauth_token_response_creating",
                   user_id=str(user_id),
                   client_id=client_id)

        # Create tokens
        access_token = self.create_oauth_access_token(
            user_id=user_id,
            client_id=client_id,
            scopes=scopes,
            org_id=org_id,
            audience=audience
        )

        refresh_token = await self.create_oauth_refresh_token(
            user_id=user_id,
            client_id=client_id,
            scopes=scopes,
            org_id=org_id
        )

        # Build response
        response = OAuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Seconds
            scope=" ".join(scopes),
            org_id=org_id
        )

        logger.info("oauth_token_response_created",
                   user_id=str(user_id),
                   client_id=client_id)

        return response
