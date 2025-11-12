"""
OAuth 2.0 Authorization Endpoint

GET /oauth/authorize - Authorization request (user approval flow)
POST /oauth/authorize - Consent submission

RFC 6749 Section 3.1: Authorization Endpoint
RFC 7636: PKCE for OAuth 2.0
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncpg

from app.db.connection import get_db_connection
from app.services.oauth_client_service import OAuthClientService, get_oauth_client_service
from app.services.scope_service import ScopeService, get_scope_service
from app.services.consent_service import ConsentService, get_consent_service
from app.services.authorization_code_service import AuthorizationCodeService, get_authorization_code_service
from app.services.auth_service import AuthService
from app.core.pkce import validate_code_challenge_format
from app.core.logging_config import get_logger
from app.core.exceptions import InvalidCredentialsError
from app.schemas.oauth import AuthorizationRequest, ResponseType, CodeChallengeMethod

logger = get_logger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth 2.0"])

# Jinja2 templates for consent screen
templates = Jinja2Templates(directory="app/templates")


@router.get("/authorize", response_class=HTMLResponse)
async def authorize_get(
    request: Request,
    # Required OAuth parameters
    response_type: str = Query(..., description="Response type (must be 'code')"),
    client_id: str = Query(..., description="Client identifier"),
    redirect_uri: str = Query(..., description="Redirect URI"),
    scope: str = Query(..., description="Space-separated scopes"),
    state: str = Query(..., description="CSRF token"),

    # PKCE parameters
    code_challenge: str = Query(..., description="SHA256(code_verifier)"),
    code_challenge_method: str = Query("S256", description="PKCE method"),

    # Optional parameters
    nonce: Optional[str] = Query(None, description="OpenID Connect nonce"),

    # Services
    client_service: OAuthClientService = Depends(get_oauth_client_service),
    scope_service: ScopeService = Depends(get_scope_service),
    consent_service: ConsentService = Depends(get_consent_service),
    authz_code_service: AuthorizationCodeService = Depends(get_authorization_code_service),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    OAuth 2.0 Authorization Endpoint (GET).

    Flow:
    1. Validate OAuth parameters
    2. Validate client and redirect_uri
    3. Check if user is logged in (session/token)
    4. Check consent status
    5. If consent needed: Show consent screen
    6. If consent given: Generate authorization code
    7. Redirect to redirect_uri with code

    Security:
    - PKCE challenge validation
    - Redirect URI exact matching
    - State parameter for CSRF protection
    """
    logger.info("oauth_authorize_start",
               client_id=client_id,
               scopes=scope,
               has_pkce=bool(code_challenge))

    # ========================================================================
    # STEP 1: VALIDATE CLIENT AND REDIRECT_URI FIRST (SECURITY CRITICAL!)
    # ========================================================================
    # RFC 6749 Section 3.1.2.4: Client MUST be validated BEFORE redirecting
    # to prevent open redirect vulnerabilities

    client = await client_service.get_client(client_id)

    if not client:
        logger.warning("oauth_authorize_invalid_client", client_id=client_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )

    # Validate redirect_uri - MUST happen before any redirects!
    if not client_service.validate_redirect_uri(client, redirect_uri):
        logger.error("oauth_authorize_redirect_uri_mismatch",
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    allowed_uris=client.redirect_uris)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri - must match registered redirect_uri exactly"
        )

    logger.debug("oauth_client_and_redirect_validated", client_id=client_id)

    # ========================================================================
    # STEP 2: VALIDATE REQUEST PARAMETERS (safe to redirect now)
    # ========================================================================

    # Validate response_type
    if response_type != "code":
        error_uri = _build_error_redirect(
            redirect_uri,
            error="unsupported_response_type",
            error_description=f"Unsupported response_type: {response_type}",
            state=state
        )
        return RedirectResponse(url=error_uri, status_code=302)

    # Validate code_challenge_method
    if code_challenge_method not in ["S256", "plain"]:
        error_uri = _build_error_redirect(
            redirect_uri,
            error="invalid_request",
            error_description=f"Invalid code_challenge_method: {code_challenge_method}",
            state=state
        )
        return RedirectResponse(url=error_uri, status_code=302)

    # Validate code_challenge format
    if not validate_code_challenge_format(code_challenge, code_challenge_method):
        error_uri = _build_error_redirect(
            redirect_uri,
            error="invalid_request",
            error_description="Invalid code_challenge format",
            state=state
        )
        return RedirectResponse(url=error_uri, status_code=302)

    # Parse scopes
    requested_scopes = scope_service.parse_scope_string(scope)

    if not requested_scopes:
        error_uri = _build_error_redirect(
            redirect_uri,
            error="invalid_scope",
            error_description="No scopes requested",
            state=state
        )
        return RedirectResponse(url=error_uri, status_code=302)

    # Validate PKCE requirement
    if client.require_pkce and not code_challenge:
        error_uri = _build_error_redirect(
            redirect_uri,
            error="invalid_request",
            error_description="PKCE required for this client",
            state=state
        )
        return RedirectResponse(url=error_uri, status_code=302)

    logger.debug("oauth_client_validated", client_id=client_id)

    # ========================================================================
    # STEP 3: CHECK IF USER IS LOGGED IN
    # ========================================================================

    # Get user from session/cookie
    # For now, we'll use a temporary approach - check for Authorization header
    # In production, this should use session cookies

    auth_header = request.headers.get("Authorization")
    user_id = None
    org_id = None

    if auth_header and auth_header.startswith("Bearer "):
        # Extract user_id from token (temporary approach)
        # In production: use proper session management
        try:
            from app.services.token_service import TokenService
            from app.config import get_settings
            from app.core.tokens import TokenHelper

            token = auth_header.replace("Bearer ", "")
            token_service = TokenService(
                settings=get_settings(),
                token_helper=TokenHelper(get_settings()),
                db=db
            )

            payload = token_service.token_helper.decode_token(token)
            user_id = UUID(payload.get("sub"))
            org_id = UUID(payload.get("org_id")) if payload.get("org_id") else None

            logger.debug("oauth_user_authenticated",
                        user_id=str(user_id),
                        org_id=str(org_id) if org_id else None)

        except Exception as e:
            logger.warning("oauth_token_validation_failed", error=str(e))
            user_id = None

    # If not logged in, redirect to login
    if not user_id:
        logger.info("oauth_user_not_authenticated_redirect_login")

        # Build login redirect with return URL
        # TODO: Implement proper session-based flow
        # For now, return error
        return HTMLResponse(
            content="""
            <html>
            <head><title>Login Required</title></head>
            <body style="font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2>🔐 Login Required</h2>
                <p>You need to log in to authorize this application.</p>
                <p><strong>Client:</strong> {client_name}</p>
                <p><strong>Scopes:</strong> {scopes}</p>
                <hr>
                <p><strong>Implementation Note:</strong> In production, this would redirect to login page with return URL.</p>
                <p>For testing: Include <code>Authorization: Bearer &lt;token&gt;</code> header.</p>
            </body>
            </html>
            """.format(client_name=client.client_name, scopes=", ".join(requested_scopes)),
            status_code=200
        )

    # ========================================================================
    # STEP 4: VALIDATE SCOPES
    # ========================================================================

    # Validate and grant scopes
    granted_scopes = await scope_service.validate_and_grant_scopes(
        requested_scopes=requested_scopes,
        client_allowed_scopes=client.allowed_scopes,
        user_id=user_id,
        organization_id=org_id
    )

    if not granted_scopes:
        logger.warning("oauth_authorize_no_scopes_granted",
                      client_id=client_id,
                      user_id=str(user_id))
        error_uri = _build_error_redirect(
            redirect_uri,
            error="insufficient_scope",
            error_description="User does not have requested permissions",
            state=state
        )
        return RedirectResponse(url=error_uri, status_code=302)

    logger.debug("oauth_scopes_validated",
                granted_count=len(granted_scopes))

    # ========================================================================
    # STEP 5: CHECK CONSENT
    # ========================================================================

    # Check if consent screen should be skipped
    skip_consent = consent_service.should_skip_consent(
        is_first_party=client.is_first_party,
        require_consent=client.require_consent
    )

    if not skip_consent:
        # Check if user has previously consented
        consent = await consent_service.check_consent(
            user_id=user_id,
            client_id=client_id,
            organization_id=org_id,
            requested_scopes=granted_scopes
        )

        if consent.needs_new_consent:
            logger.info("oauth_consent_required",
                       client_id=client_id,
                       user_id=str(user_id))

            # Show consent screen
            scope_descriptions = scope_service.get_scope_descriptions(granted_scopes)

            # Get user email from database
            from app.db.procedures import sp_get_user_by_id
            user = await sp_get_user_by_id(db, user_id)

            # Get organization name if org_id present
            org_name = None
            if org_id:
                from app.models.organization import sp_get_organization_by_id
                org = await sp_get_organization_by_id(db, org_id)
                org_name = org.name if org else None

            return templates.TemplateResponse(
                "consent.html",
                {
                    "request": request,
                    "client": client,
                    "client_name": client.client_name,
                    "client_description": client.description,
                    "client_logo_uri": client.logo_uri,
                    "requested_scopes": granted_scopes,
                    "scope_descriptions": scope_descriptions,
                    "user_email": user.email,
                    "organization_name": org_name,
                    # Hidden form fields
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "scope": " ".join(granted_scopes),
                    "code_challenge": code_challenge,
                    "code_challenge_method": code_challenge_method,
                    "state": state,
                    "nonce": nonce,
                    "org_id": str(org_id) if org_id else None,
                }
            )

    logger.info("oauth_consent_skipped_or_granted",
               client_id=client_id,
               skip_consent=skip_consent)

    # ========================================================================
    # STEP 6: GENERATE AUTHORIZATION CODE
    # ========================================================================

    # Save consent if new
    if not skip_consent:
        await consent_service.save_consent(
            user_id=user_id,
            client_id=client_id,
            organization_id=org_id,
            granted_scopes=granted_scopes,
            request=request
        )

    # Generate authorization code
    code = await authz_code_service.create_authorization_code(
        client_id=client_id,
        user_id=user_id,
        organization_id=org_id,
        redirect_uri=redirect_uri,
        scopes=granted_scopes,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        nonce=nonce,
        request=request
    )

    logger.info("oauth_authorization_code_generated",
               client_id=client_id,
               user_id=str(user_id))

    # ========================================================================
    # STEP 7: REDIRECT WITH CODE
    # ========================================================================

    # Build redirect URI with code and state
    separator = "&" if "?" in redirect_uri else "?"
    redirect_url = f"{redirect_uri}{separator}code={code}&state={state}"

    logger.info("oauth_authorize_success",
               client_id=client_id,
               user_id=str(user_id),
               redirect_uri=redirect_uri)

    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/authorize", response_class=HTMLResponse)
async def authorize_post(
    request: Request,
    # Form data from consent screen
    action: str = Form(..., description="User action (approve or deny)"),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(...),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form(...),
    state: str = Form(...),
    nonce: Optional[str] = Form(None),
    org_id: Optional[str] = Form(None),

    # Services
    client_service: OAuthClientService = Depends(get_oauth_client_service),
    consent_service: ConsentService = Depends(get_consent_service),
    authz_code_service: AuthorizationCodeService = Depends(get_authorization_code_service),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    OAuth 2.0 Authorization Endpoint (POST) - Consent submission.

    Handles user consent decision (approve or deny).
    """
    logger.info("oauth_consent_submission",
               client_id=client_id,
               action=action)

    # Get user from session (same as GET)
    auth_header = request.headers.get("Authorization")
    user_id = None
    organization_id = None

    if auth_header and auth_header.startswith("Bearer "):
        try:
            from app.services.token_service import TokenService
            from app.config import get_settings
            from app.core.tokens import TokenHelper

            token = auth_header.replace("Bearer ", "")
            token_service = TokenService(
                settings=get_settings(),
                token_helper=TokenHelper(get_settings()),
                db=db
            )

            payload = token_service.token_helper.decode_token(token)
            user_id = UUID(payload.get("sub"))

            if org_id:
                organization_id = UUID(org_id)
            elif payload.get("org_id"):
                organization_id = UUID(payload.get("org_id"))

        except Exception as e:
            logger.error("oauth_consent_token_validation_failed", error=str(e))

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # User denied consent
    if action == "deny":
        logger.info("oauth_consent_denied",
                   client_id=client_id,
                   user_id=str(user_id))

        error_uri = _build_error_redirect(
            redirect_uri,
            error="access_denied",
            error_description="User denied authorization",
            state=state
        )
        return RedirectResponse(url=error_uri, status_code=302)

    # User approved consent
    if action == "approve":
        scopes = scope.split()

        # Save consent
        await consent_service.save_consent(
            user_id=user_id,
            client_id=client_id,
            organization_id=organization_id,
            granted_scopes=scopes,
            request=request
        )

        # Generate authorization code
        code = await authz_code_service.create_authorization_code(
            client_id=client_id,
            user_id=user_id,
            organization_id=organization_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            nonce=nonce,
            request=request
        )

        logger.info("oauth_consent_approved_code_generated",
                   client_id=client_id,
                   user_id=str(user_id))

        # Redirect with code
        separator = "&" if "?" in redirect_uri else "?"
        redirect_url = f"{redirect_uri}{separator}code={code}&state={state}"

        return RedirectResponse(url=redirect_url, status_code=302)

    # Invalid action
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid action"
    )


def _build_error_redirect(
    redirect_uri: str,
    error: str,
    error_description: Optional[str] = None,
    state: Optional[str] = None
) -> str:
    """Build OAuth error redirect URI"""
    separator = "&" if "?" in redirect_uri else "?"
    error_uri = f"{redirect_uri}{separator}error={error}"

    if error_description:
        error_uri += f"&error_description={error_description}"

    if state:
        error_uri += f"&state={state}"

    return error_uri
