"""
Consent Service

Manages user consent for OAuth clients.
Implements consent storage, retrieval, and incremental consent.
"""

from typing import Optional, List
from uuid import UUID
import asyncpg
from fastapi import Depends, Request

from app.db.connection import get_db_connection
from app.models.oauth import (
    ConsentRecord,
    sp_save_user_consent,
    sp_get_user_consent,
    sp_revoke_user_consent
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ConsentService:
    """User consent management service"""

    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection)
    ):
        self.db = db

    async def check_consent(
        self,
        user_id: UUID,
        client_id: str,
        organization_id: Optional[UUID],
        requested_scopes: List[str]
    ) -> ConsentRecord:
        """
        Check if user has previously consented to requested scopes.

        Returns:
            ConsentRecord with:
            - has_consent: True if user has consented to ALL requested scopes
            - granted_scopes: Previously granted scopes (if any)
            - needs_new_consent: True if consent prompt is needed

        Logic:
            - If no previous consent: needs_new_consent = True
            - If previous consent exists BUT requested scopes > granted scopes:
              needs_new_consent = True (incremental consent)
            - If previous consent covers all requested scopes:
              has_consent = True, needs_new_consent = False
        """
        logger.info("consent_check_start",
                   user_id=str(user_id),
                   client_id=client_id,
                   org_id=str(organization_id) if organization_id else None,
                   requested_scopes_count=len(requested_scopes))

        consent = await sp_get_user_consent(
            self.db,
            user_id=user_id,
            client_id=client_id,
            organization_id=organization_id,
            requested_scopes=requested_scopes
        )

        logger.info("consent_check_complete",
                   user_id=str(user_id),
                   client_id=client_id,
                   has_consent=consent.has_consent,
                   needs_new_consent=consent.needs_new_consent)

        return consent

    async def save_consent(
        self,
        user_id: UUID,
        client_id: str,
        organization_id: Optional[UUID],
        granted_scopes: List[str],
        request: Optional[Request] = None
    ) -> UUID:
        """
        Save user consent decision.

        This is called after user approves consent screen.
        Supports incremental consent (upserts existing consent).

        Args:
            user_id: User ID
            client_id: Client ID
            organization_id: Organization context
            granted_scopes: Scopes user consented to
            request: FastAPI request (for IP/user agent)

        Returns:
            Consent record UUID
        """
        logger.info("consent_save_start",
                   user_id=str(user_id),
                   client_id=client_id,
                   org_id=str(organization_id) if organization_id else None,
                   granted_scopes_count=len(granted_scopes))

        # Extract request context
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # Save consent
        consent_id = await sp_save_user_consent(
            self.db,
            user_id=user_id,
            client_id=client_id,
            organization_id=organization_id,
            granted_scopes=granted_scopes,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info("consent_saved",
                   user_id=str(user_id),
                   client_id=client_id,
                   consent_id=str(consent_id))

        return consent_id

    async def revoke_consent(
        self,
        user_id: UUID,
        client_id: str,
        organization_id: Optional[UUID]
    ) -> bool:
        """
        Revoke user consent for a client.

        This is called when user explicitly revokes consent from settings.

        Returns:
            True if consent was revoked, False if no consent existed
        """
        logger.info("consent_revoke_start",
                   user_id=str(user_id),
                   client_id=client_id,
                   org_id=str(organization_id) if organization_id else None)

        revoked = await sp_revoke_user_consent(
            self.db,
            user_id=user_id,
            client_id=client_id,
            organization_id=organization_id
        )

        if revoked:
            logger.info("consent_revoked",
                       user_id=str(user_id),
                       client_id=client_id)
        else:
            logger.warning("consent_revoke_failed_not_found",
                          user_id=str(user_id),
                          client_id=client_id)

        return revoked

    def should_skip_consent(
        self,
        is_first_party: bool,
        require_consent: bool
    ) -> bool:
        """
        Determine if consent screen should be skipped.

        Rules:
        - First-party clients with require_consent=False: SKIP
        - All other cases: SHOW

        Args:
            is_first_party: Client is first-party (internal app)
            require_consent: Client requires explicit consent

        Returns:
            True if consent should be skipped, False otherwise
        """
        skip = is_first_party and not require_consent

        if skip:
            logger.info("consent_skipped_first_party")
        else:
            logger.debug("consent_required",
                        is_first_party=is_first_party,
                        require_consent=require_consent)

        return skip


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_consent_service(
    db: asyncpg.Connection = Depends(get_db_connection)
) -> ConsentService:
    """Get ConsentService instance"""
    return ConsentService(db)
