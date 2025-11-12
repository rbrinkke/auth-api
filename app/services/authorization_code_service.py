"""
Authorization Code Service

Manages OAuth authorization codes with PKCE validation.
Handles code generation, storage, validation, and consumption (single-use).
"""

from typing import Optional, List
from uuid import UUID
import asyncpg
from fastapi import Depends, Request

from app.db.connection import get_db_connection
from app.models.oauth import (
    AuthorizationCodeRecord,
    sp_create_authorization_code,
    sp_validate_and_consume_authorization_code
)
from app.core.pkce import (
    generate_authorization_code,
    validate_pkce,
    validate_code_verifier_format,
    validate_code_challenge_format
)
from app.core.logging_config import get_logger
from app.core.exceptions import InvalidTokenError

logger = get_logger(__name__)


class AuthorizationCodeService:
    """Authorization code management service"""

    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection)
    ):
        self.db = db

    async def create_authorization_code(
        self,
        client_id: str,
        user_id: UUID,
        organization_id: Optional[UUID],
        redirect_uri: str,
        scopes: List[str],
        code_challenge: str,
        code_challenge_method: str = "S256",
        nonce: Optional[str] = None,
        request: Optional[Request] = None
    ) -> str:
        """
        Generate and store authorization code.

        The authorization code is short-lived (60 seconds) and single-use.
        It binds the authorization request to the token request via PKCE.

        Args:
            client_id: Client identifier
            user_id: User who authorized
            organization_id: Organization context
            redirect_uri: Redirect URI for validation
            scopes: Granted scopes
            code_challenge: SHA256(code_verifier) from authorization request
            code_challenge_method: PKCE method (S256 or plain)
            nonce: Optional nonce for OpenID Connect
            request: FastAPI request (for IP/user agent)

        Returns:
            Authorization code (base64url-encoded random string)

        Raises:
            ValueError: If code_challenge format is invalid
        """
        logger.info("authz_code_create_start",
                   user_id=str(user_id),
                   client_id=client_id,
                   org_id=str(organization_id) if organization_id else None,
                   scopes_count=len(scopes))

        # Validate code_challenge format
        if not validate_code_challenge_format(code_challenge, code_challenge_method):
            logger.error("authz_code_invalid_challenge_format",
                        code_challenge_method=code_challenge_method)
            raise ValueError("Invalid code_challenge format")

        # Generate authorization code
        code = generate_authorization_code()

        logger.debug("authz_code_generated", code_length=len(code))

        # Extract request context
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # Store authorization code
        code_id = await sp_create_authorization_code(
            self.db,
            code=code,
            client_id=client_id,
            user_id=user_id,
            organization_id=organization_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            nonce=nonce,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info("authz_code_created",
                   code_id=str(code_id),
                   user_id=str(user_id),
                   client_id=client_id,
                   expires_seconds=60)

        return code

    async def validate_and_consume_code(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str
    ) -> AuthorizationCodeRecord:
        """
        Validate authorization code, verify PKCE, and mark as used (atomic).

        This is the CRITICAL security function. It:
        1. Validates code exists and not expired
        2. Validates code not already used (prevents replay attacks)
        3. Validates redirect_uri matches authorization request
        4. Validates PKCE: SHA256(code_verifier) == stored code_challenge
        5. Marks code as used (atomic, single-use)

        Args:
            code: Authorization code from authorization response
            client_id: Client identifier
            redirect_uri: Redirect URI (must match authorization request)
            code_verifier: PKCE code_verifier

        Returns:
            AuthorizationCodeRecord with user_id, scopes, etc.

        Raises:
            InvalidTokenError: If validation fails
            ValueError: If code_verifier format is invalid
        """
        logger.info("authz_code_validation_start",
                   client_id=client_id)

        # Validate code_verifier format
        if not validate_code_verifier_format(code_verifier):
            logger.error("authz_code_invalid_verifier_format")
            raise ValueError("Invalid code_verifier format")

        # Validate and consume code (atomic)
        try:
            code_record = await sp_validate_and_consume_authorization_code(
                self.db,
                code=code,
                client_id=client_id,
                redirect_uri=redirect_uri
            )

            if not code_record:
                logger.warning("authz_code_validation_failed_not_found",
                              client_id=client_id)
                raise InvalidTokenError("Invalid or expired authorization code")

            logger.debug("authz_code_db_validation_passed",
                        user_id=str(code_record.user_id))

        except Exception as e:
            logger.error("authz_code_validation_failed",
                        client_id=client_id,
                        error=str(e))
            raise InvalidTokenError(f"Authorization code validation failed: {str(e)}")

        # Validate PKCE
        is_pkce_valid = validate_pkce(
            stored_challenge=code_record.code_challenge,
            received_verifier=code_verifier,
            method=code_record.code_challenge_method
        )

        if not is_pkce_valid:
            logger.error("authz_code_pkce_validation_failed",
                        user_id=str(code_record.user_id),
                        client_id=client_id)
            raise InvalidTokenError("PKCE validation failed")

        logger.info("authz_code_validation_success",
                   user_id=str(code_record.user_id),
                   client_id=client_id,
                   scopes_count=len(code_record.scopes))

        return code_record


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_authorization_code_service(
    db: asyncpg.Connection = Depends(get_db_connection)
) -> AuthorizationCodeService:
    """Get AuthorizationCodeService instance"""
    return AuthorizationCodeService(db)
