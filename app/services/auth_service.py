from fastapi import Depends
import asyncpg
import redis
import secrets
from uuid import UUID

from app.db.connection import get_db_connection
from app.core.utils import generate_verification_code
from app.core.redis_client import get_redis_client
from app.core.logging_config import get_logger
from app.middleware.correlation import trace_id_var
from app.config import get_settings
from app.db import procedures
from app.core.exceptions import (
    InvalidCredentialsError,
    AccountNotVerifiedError,
    TwoFactorRequiredError,
    TwoFactorVerificationError,
    UserNotFoundError,
    InvalidTokenError
)
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.services.two_factor_service import TwoFactorService
from app.services.email_service import EmailService
from app.schemas.auth import (
    TokenResponse,
    TwoFactorLoginRequest,
    OrganizationOption,
    OrganizationSelectionResponse
)
from app.models.organization import sp_get_user_organizations
from app.core.metrics import track_login, track_token_operation

logger = get_logger(__name__)

class AuthService:
    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection),
        redis_client: redis.Redis = Depends(get_redis_client),
        password_service: PasswordService = Depends(PasswordService),
        token_service: TokenService = Depends(TokenService),
        two_factor_service: TwoFactorService = Depends(TwoFactorService),
        email_service: EmailService = Depends(EmailService),
        settings = Depends(get_settings)
    ):
        self.db = db
        self.redis_client = redis_client
        self.password_service = password_service
        self.token_service = token_service
        self.two_factor_service = two_factor_service
        self.email_service = email_service
        self.settings = settings

    async def login_user(self, email: str, password: str, code: str | None = None, org_id: UUID | None = None) -> dict:
        trace_id = trace_id_var.get()

        logger.info("login_attempt_start", email=email, has_code=(code is not None))
        logger.debug("login_fetching_user_from_db", email=email)

        user = await procedures.sp_get_user_by_email(self.db, email)

        if not user:
            logger.warning("login_failed_user_not_found", email=email)
            track_login("failed_credentials")
            raise InvalidCredentialsError()

        logger.debug("login_user_found", user_id=str(user.id), email=email)
        logger.debug("login_verifying_password", user_id=str(user.id))
        password_ok = await self.password_service.verify_password(password, user.hashed_password)

        if not password_ok:
            logger.warning("login_failed_invalid_password", user_id=str(user.id), email=email)
            track_login("failed_credentials")
            raise InvalidCredentialsError()

        logger.debug("login_password_verified", user_id=str(user.id))
        logger.debug("login_checking_verification_status", user_id=str(user.id), is_verified=user.is_verified)

        if not user.is_verified:
            logger.warning("login_failed_account_not_verified", user_id=str(user.id), email=email)
            track_login("failed_not_verified")
            raise AccountNotVerifiedError()

        # Step 1: If no code provided, generate and send login code
        if code is None:
            login_code = generate_verification_code()
            redis_key = f"2FA:{user.id}:login"
            self.redis_client.setex(redis_key, 600, login_code)

            await self.email_service.send_2fa_code(
                user.email,
                login_code,
                purpose="login verification"
            )

            logger.info("login_code_sent", user_id=str(user.id), email=user.email)
            return {
                "message": "Login code sent to your email",
                "email": user.email,
                "user_id": str(user.id),
                "requires_code": True,
                "expires_in": 600
            }

        # Step 2: Verify provided code
        redis_key = f"2FA:{user.id}:login"
        stored_code = self.redis_client.get(redis_key)

        if not stored_code:
            logger.warning("login_failed_code_expired", user_id=str(user.id), email=email)
            raise InvalidTokenError("Login code expired or not found")

        # Use constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(stored_code, code):
            logger.warning("login_failed_invalid_code", user_id=str(user.id), email=email)
            raise InvalidTokenError("Invalid login code")

        # Delete used code
        self.redis_client.delete(redis_key)
        logger.info("login_code_verified", user_id=str(user.id), email=email)

        # Step 3: Check 2FA (existing logic)
        if self.settings.TWO_FACTOR_ENABLED:
            user_totp_enabled = self.redis_client.get(f"2FA:{user.id}:totp_enabled")
            if user_totp_enabled == "true":
                pre_auth_token = self.token_service.create_2fa_token(user.id)
                logger.info("login_requires_2fa", user_id=str(user.id), email=email)
                track_login("failed_2fa_required")
                raise TwoFactorRequiredError(detail=pre_auth_token)

        # Step 4: Handle organization selection
        result = await self._handle_organization_selection(user.id, email, org_id)
        logger.info("login_success", user_id=str(user.id), email=email)
        track_login("success")

        return result

    async def login_2fa_challenge(self, request: TwoFactorLoginRequest) -> TokenResponse:
        user_id = self.token_service.get_user_id_from_token(
            request.pre_auth_token,
            "2fa_pre_auth"
        )

        await self.two_factor_service.validate_2fa_challenge(user_id, request.code)

        return await self._grant_full_tokens(user_id)

    async def logout_user(self, refresh_token: str) -> dict:
        try:
            payload = self.token_service.token_helper.decode_token(refresh_token)
            if payload.get("type") == "refresh":
                user_id = UUID(payload.get("sub"))
                await procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)
                logger.info("logout_success", user_id=str(user_id))
        except Exception as e:
            logger.warning("logout_token_revocation_failed", error=str(e))

        return {"message": "Logged out successfully"}

    async def _handle_organization_selection(
        self,
        user_id: UUID,
        email: str,
        org_id: UUID | None
    ) -> dict:
        """
        Handle organization selection during login.

        Flow:
        1. Get user's organizations
        2. If no orgs → return user-level token
        3. If 1 org → auto-select, return org token
        4. If multiple orgs + org_id provided → validate & return org token
        5. If multiple orgs + no org_id → return org list + user token

        Args:
            user_id: User ID
            email: User email (for logging)
            org_id: Optional organization ID from login request

        Returns:
            TokenResponse or OrganizationSelectionResponse
        """
        logger.info("organization_selection_start",
                   user_id=str(user_id),
                   org_id_provided=org_id is not None)

        # Get user's organizations
        user_orgs = await sp_get_user_organizations(self.db, user_id)
        org_count = len(user_orgs)

        logger.info("user_organizations_retrieved",
                   user_id=str(user_id),
                   org_count=org_count)

        # Case 1: No organizations → user-level token
        if org_count == 0:
            logger.info("login_no_organizations",
                       user_id=str(user_id))
            return await self._grant_tokens(user_id, None)

        # Case 2: Single organization → auto-select
        if org_count == 1:
            selected_org_id = user_orgs[0].id
            logger.info("login_auto_select_organization",
                       user_id=str(user_id),
                       org_id=str(selected_org_id))
            return await self._grant_tokens(user_id, selected_org_id)

        # Case 3: Multiple organizations + org_id provided → validate & use
        if org_id:
            # Validate user is member of requested org
            is_member = any(org.id == org_id for org in user_orgs)
            if not is_member:
                logger.warning("login_invalid_org_selection",
                              user_id=str(user_id),
                              org_id=str(org_id))
                from app.core.exceptions import InvalidCredentialsError
                raise InvalidCredentialsError("Invalid organization selection")

            logger.info("login_explicit_org_selection",
                       user_id=str(user_id),
                       org_id=str(org_id))
            return await self._grant_tokens(user_id, org_id)

        # Case 4: Multiple organizations + no org_id → return selection prompt
        logger.info("login_org_selection_required",
                   user_id=str(user_id),
                   org_count=org_count)

        # Generate user-level token for org selection
        user_token = self.token_service.create_access_token(user_id, None)

        # Convert to org options
        org_options = [
            OrganizationOption(
                id=org.id,
                name=org.name,
                slug=org.slug,
                role=org.role,
                member_count=org.member_count
            )
            for org in user_orgs
        ]

        return OrganizationSelectionResponse(
            message="Please select an organization to continue",
            organizations=org_options,
            user_token=user_token,
            expires_in=900  # 15 minutes to select
        )

    async def _grant_tokens(self, user_id: UUID, org_id: UUID | None) -> TokenResponse:
        """
        Generate access and refresh tokens.

        Args:
            user_id: User ID
            org_id: Optional organization ID for org-scoped tokens

        Returns:
            TokenResponse with tokens
        """
        logger.info("token_grant_start",
                   user_id=str(user_id),
                   org_id=str(org_id) if org_id else None)

        access_token = self.token_service.create_access_token(user_id, org_id)
        logger.info("access_token_created", user_id=str(user_id), token_length=len(access_token))
        track_token_operation("create_access", "success")

        refresh_token = await self.token_service.create_refresh_token(user_id, org_id)
        logger.info("refresh_token_created", user_id=str(user_id), token_length=len(refresh_token))
        track_token_operation("create_refresh", "success")

        response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            org_id=org_id
        )

        logger.info("token_grant_complete",
                   user_id=str(user_id),
                   org_id=str(org_id) if org_id else None)
        return response

