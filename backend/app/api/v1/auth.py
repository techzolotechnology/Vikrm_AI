"""
Authentication endpoints.

POST /auth/google          -> exchange a Google ID token for a Vikrm JWT pair
POST /auth/register        -> register with email and password
POST /auth/login           -> login with email and password
POST /auth/verify-email    -> verify email token
POST /auth/forgot-password -> request password reset link
POST /auth/reset-password  -> reset password with token
POST /auth/refresh         -> rotate a refresh token for a new access token
GET  /auth/me               -> current authenticated user's profile
POST /auth/logout          -> revoke a specific refresh token (sign out this session)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.auth import (
    EmailLoginRequest,
    EmailRegisterRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPairResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthError, AuthService

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=TokenPairResponse)
async def sign_in_with_google(
    body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)
) -> TokenPairResponse:
    logger.info("[Auth API] Backend received Google OAuth request (token length=%d)", len(body.id_token))
    service = AuthService(db)
    try:
        user, access_token, refresh_token = await service.authenticate_with_google(
            body.id_token
        )
        logger.info(
            "[Auth API] Google authentication successful for user_id=%s (%s). Returning JWT token pair.",
            user.id,
            user.email,
        )
    except AuthError as exc:
        logger.warning("[Auth API] Google token verification / auth failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("[Auth API] Database or system error during Google auth: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication server error: {exc}",
        ) from exc

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)



@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register_with_email(
    body: EmailRegisterRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    service = AuthService(db)
    try:
        await service.register_with_email(body.full_name, body.email, body.password)
    except AuthError as exc:
        logger.warning("Email registration failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MessageResponse(message="Registration successful. Account created.")


@router.post("/login", response_model=TokenPairResponse)
async def login_with_email(
    body: EmailLoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenPairResponse:
    service = AuthService(db)
    try:
        _user, access_token, refresh_token = await service.login_with_email(
            body.email, body.password
        )
    except AuthError as exc:
        logger.warning("Email login failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    service = AuthService(db)
    try:
        await service.verify_email(body.token)
    except AuthError as exc:
        logger.warning("Email verification failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MessageResponse(message="Email successfully verified.")


@router.post("/forgot-password", response_model=MessageResponse)
async def request_password_reset(
    body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    service = AuthService(db)
    await service.request_password_reset(body.email)
    return MessageResponse(message="If an account exists, a password reset token was created.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    service = AuthService(db)
    try:
        await service.reset_password(body.token, body.new_password)
    except AuthError as exc:
        logger.warning("Password reset failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MessageResponse(message="Password successfully reset.")


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_access_token(
    body: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenPairResponse:
    service = AuthService(db)
    try:
        _user, access_token, refresh_token = await service.refresh(body.refresh_token)
    except AuthError as exc:
        logger.warning("Token refresh failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    from app.core.security import TokenError, decode_token

    repo = RefreshTokenRepository(db)
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except TokenError:
        return None

    record = await repo.get_by_jti(payload["jti"])
    if record is not None and record.user_id == user.id and not record.revoked:
        await repo.revoke(record)
        await db.commit()
    return None

