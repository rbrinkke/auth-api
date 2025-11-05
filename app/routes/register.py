"""
User registration endpoint.

Implements hard verification: user cannot login until email is verified.
"""
import logging

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.redis_client import RedisClient, get_redis
from app.core.security import hash_password
from app.core.tokens import generate_verification_token
from app.db.connection import get_db_connection
from app.db.procedures import sp_create_user
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.email_service import get_email_service, EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user account.
    
    **Important:** Users must verify their email before they can login.
    A verification email will be sent to the provided address.
    
    **Rate limit:** 3 requests per hour per IP
    """
)
@limiter.limit(f"{settings.rate_limit_register_per_hour}/hour")
async def register(
    request: Request,
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(get_email_service)
):
    """
    Register a new user with email verification.
    
    Flow:
    1. Hash password with Argon2id
    2. Create user in database (is_verified=FALSE)
    3. Generate verification token in Redis
    4. Send verification email in background
    5. Return success message (NO tokens)
    """
    try:
        # 1. Hash the password
        hashed_password = hash_password(data.password)
        
        # 2. Create user via stored procedure
        try:
            user = await sp_create_user(conn, data.email, hashed_password)
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 3. Generate verification token
        verification_token = generate_verification_token()
        
        # 4. Store token in Redis (with reverse lookup)
        await redis.set_verification_token(verification_token, user.id)
        
        # 5. Send verification email (async, don't block)
        background_tasks.add_task(
            email_svc.send_verification_email,
            user.email,
            verification_token
        )
        
        logger.info(f"User registered successfully: {user.email} (id: {user.id})")
        
        return RegisterResponse(
            message=f"Verification email sent to {user.email}. Please check your inbox.",
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )
