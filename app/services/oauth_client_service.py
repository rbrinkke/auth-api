"""
OAuth Client Service

Manages OAuth client registration, authentication, and validation.
"""

from typing import Optional, List
from uuid import UUID
import secrets
import asyncpg
from fastapi import Depends

from app.db.connection import get_db_connection
from app.models.oauth import (
    OAuthClientRecord,
    sp_create_oauth_client,
    sp_get_oauth_client,
    sp_list_oauth_clients
)
from app.services.password_service import PasswordService
from app.core.logging_config import get_logger
from app.core.exceptions import InvalidCredentialsError

logger = get_logger(__name__)


class OAuthClientService:
    """OAuth client management service"""

    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection),
        password_service: PasswordService = Depends(PasswordService)
    ):
        self.db = db
        self.password_service = password_service

    async def create_client(
        self,
        client_id: str,
        client_name: str,
        client_type: str,
        redirect_uris: List[str],
        allowed_scopes: List[str],
        client_secret: Optional[str] = None,
        is_first_party: bool = False,
        description: Optional[str] = None,
        logo_uri: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> tuple[UUID, Optional[str]]:
        """
        Create OAuth client.

        Returns:
            Tuple of (client_uuid, plain_text_secret)
            plain_text_secret is None for public clients
        """
        logger.info("oauth_client_create_start",
                   client_id=client_id,
                   client_type=client_type)

        # Hash client_secret if provided
        client_secret_hash = None
        plain_text_secret = None

        if client_type == "confidential":
            if not client_secret:
                # Generate random client_secret
                plain_text_secret = self._generate_client_secret()
            else:
                plain_text_secret = client_secret

            # Hash secret
            client_secret_hash = await self.password_service.hash_password(plain_text_secret)

            logger.debug("oauth_client_secret_hashed", client_id=client_id)

        # Create client
        client_uuid = await sp_create_oauth_client(
            self.db,
            client_id=client_id,
            client_name=client_name,
            client_type=client_type,
            redirect_uris=redirect_uris,
            allowed_scopes=allowed_scopes,
            client_secret_hash=client_secret_hash,
            is_first_party=is_first_party,
            description=description,
            logo_uri=logo_uri,
            created_by=created_by
        )

        logger.info("oauth_client_created",
                   client_id=client_id,
                   client_uuid=str(client_uuid))

        return (client_uuid, plain_text_secret)

    async def get_client(self, client_id: str) -> Optional[OAuthClientRecord]:
        """Get OAuth client by client_id"""
        client = await sp_get_oauth_client(self.db, client_id)

        if client:
            logger.debug("oauth_client_retrieved", client_id=client_id)
        else:
            logger.warning("oauth_client_not_found", client_id=client_id)

        return client

    async def list_clients(self) -> List[OAuthClientRecord]:
        """List all OAuth clients"""
        clients = await sp_list_oauth_clients(self.db)
        logger.debug("oauth_clients_listed", count=len(clients))
        return clients

    async def authenticate_client(
        self,
        client_id: str,
        client_secret: Optional[str] = None
    ) -> OAuthClientRecord:
        """
        Authenticate OAuth client.

        For public clients: Only validates client_id exists
        For confidential clients: Validates client_id + client_secret

        Raises:
            InvalidCredentialsError: If authentication fails
        """
        logger.info("oauth_client_auth_start", client_id=client_id)

        # Get client
        client = await self.get_client(client_id)

        if not client:
            logger.warning("oauth_client_auth_failed_not_found", client_id=client_id)
            raise InvalidCredentialsError("Invalid client credentials")

        # Public client: No secret required
        if client.client_type == "public":
            if client_secret:
                logger.warning("oauth_client_auth_failed_public_with_secret",
                              client_id=client_id)
                raise InvalidCredentialsError("Public clients must not provide client_secret")

            logger.info("oauth_client_auth_success_public", client_id=client_id)
            return client

        # Confidential client: Verify secret
        if client.client_type == "confidential":
            if not client_secret:
                logger.warning("oauth_client_auth_failed_no_secret", client_id=client_id)
                raise InvalidCredentialsError("Confidential clients must provide client_secret")

            # Verify secret
            is_valid = await self.password_service.verify_password(
                client_secret,
                client.client_secret_hash
            )

            if not is_valid:
                logger.warning("oauth_client_auth_failed_invalid_secret",
                              client_id=client_id)
                raise InvalidCredentialsError("Invalid client credentials")

            logger.info("oauth_client_auth_success_confidential", client_id=client_id)
            return client

        logger.error("oauth_client_auth_failed_unknown_type",
                    client_id=client_id,
                    client_type=client.client_type)
        raise InvalidCredentialsError("Invalid client type")

    def validate_redirect_uri(
        self,
        client: OAuthClientRecord,
        redirect_uri: str
    ) -> bool:
        """
        Validate redirect URI against client's registered URIs.

        Security: EXACT MATCH ONLY (no wildcards, no fuzzy matching)

        Args:
            client: OAuth client
            redirect_uri: Redirect URI to validate

        Returns:
            True if valid, False otherwise
        """
        # Exact match only
        is_valid = redirect_uri in client.redirect_uris

        if not is_valid:
            logger.warning("oauth_redirect_uri_mismatch",
                          client_id=client.client_id,
                          requested_uri=redirect_uri,
                          registered_uris=client.redirect_uris)

        return is_valid

    def _generate_client_secret(self) -> str:
        """Generate cryptographically random client secret"""
        # 32 bytes = 256 bits of entropy
        return secrets.token_urlsafe(32)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_oauth_client_service(
    db: asyncpg.Connection = Depends(get_db_connection)
) -> OAuthClientService:
    """Get OAuthClientService instance"""
    password_service = PasswordService()
    return OAuthClientService(db, password_service)
