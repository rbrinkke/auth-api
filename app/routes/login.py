# app/routes/login.py
"""User login endpoint."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService, get_auth_service, AuthServiceError

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access tokens",
    description="Authenticate with email/password. Returns tokens or 2FA requirement."
)
@limiter.limit(f"{settings.rate_limit_login_per_minute}/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return JWT tokens.
    
    Flow:
    1. Validate credentials
    2. Check 2FA status
    3. Return tokens or 2FA requirement
    """
    try:
        result = await auth_service.authenticate_user(
            email=credentials.username,
            password=credentials.password
        )
        
        # Handle 2FA requirement
        if result.two_factor_required:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "message": "Two-factor authentication required. Check your email for code.",
                    "two_factor_required": True,
                    "user_id": result.user_id
                }
            )
        
        # Return tokens
        return TokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type="bearer"
        )
        
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )
