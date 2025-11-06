import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import setup_logging
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
    TwoFactorVerificationError
)
from app.services.password_validation_service import PasswordValidationError

from app.routes import (
    login, register, logout, refresh,
    verify, password_reset, twofa
)

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth API")

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
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={"detail": "2FA required", "pre_auth_token": exc.detail},
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

@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "ok"}
