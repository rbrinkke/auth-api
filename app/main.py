import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.logging_config import setup_logging
from app.core.rate_limiting import init_limiter
from app.middleware.correlation import correlation_id_middleware
from app.middleware.security import add_security_headers
from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.db import db
from app.config import get_settings
from app.core.exceptions import (
    AuthException,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    AccountNotVerifiedError,
    TokenExpiredError,
    InvalidTokenError,
    TwoFactorRequiredError,
    TwoFactorVerificationError,
    RequestEntityTooLargeError
)
from app.services.password_validation_service import PasswordValidationError

from app.routes import (
    login, register, logout, refresh,
    verify, password_reset, twofa, dashboard
)

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth API")

# Rate limiting setup
limiter = init_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    logger.info("Connecting to database...")
    await db.connect()
    logger.info("Database connected successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Disconnecting from database...")
    await db.disconnect()
    logger.info("Database disconnected")

settings = get_settings()

# Add request size limit middleware (must be first to protect all routes)
app.add_middleware(RequestSizeLimitMiddleware, settings=settings)

cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    return await add_security_headers(request, call_next)

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    return await correlation_id_middleware(request, call_next)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(TwoFactorRequiredError)
async def two_factor_required_handler(request: Request, exc: TwoFactorRequiredError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": "2FA verification required",
            "pre_auth_token": exc.detail,
            "challenge_type": "2fa"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(TwoFactorVerificationError)
async def two_factor_verification_handler(request: Request, exc: TwoFactorVerificationError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail},
    )

@app.exception_handler(AccountNotVerifiedError)
async def account_not_verified_handler(request: Request, exc: AccountNotVerifiedError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail},
    )

@app.exception_handler(UserAlreadyExistsError)
async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail},
    )

@app.exception_handler(PasswordValidationError)
async def password_validation_handler(request: Request, exc: PasswordValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )

@app.exception_handler(RequestEntityTooLargeError)
async def request_entity_too_large_handler(request: Request, exc: RequestEntityTooLargeError):
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"detail": exc.detail},
    )

@app.exception_handler(TokenExpiredError)
async def token_expired_handler(request: Request, exc: TokenExpiredError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
    )

@app.exception_handler(InvalidTokenError)
async def invalid_token_handler(request: Request, exc: InvalidTokenError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
    )

@app.exception_handler(AuthException)
async def generic_auth_handler(request: Request, exc: AuthException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )

app.include_router(login.router, prefix="/api/auth", tags=["Auth"])
app.include_router(register.router, prefix="/api/auth", tags=["Auth"])
app.include_router(logout.router, prefix="/api/auth", tags=["Auth"])
app.include_router(refresh.router, prefix="/api/auth", tags=["Auth"])
app.include_router(verify.router, prefix="/api/auth", tags=["Auth"])
app.include_router(password_reset.router, prefix="/api/auth", tags=["Auth"])
app.include_router(twofa.router, prefix="/api/auth/2fa", tags=["2FA"])
app.include_router(dashboard.router, tags=["Dashboard"])

@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "ok"}

# Initialize Prometheus metrics
# Exposes metrics at /metrics endpoint
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=False,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="auth_api_requests_inprogress",
    inprogress_labels=True,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
