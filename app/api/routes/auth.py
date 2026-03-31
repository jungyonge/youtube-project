from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.request import LoginRequest, RegisterRequest
from app.api.schemas.response import AuthTokenResponse, UserResponse
from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import create_access_token
from app.auth.password import hash_password, verify_password
from app.db.models.user import User
from app.db.repositories.user_repo import UserRepository
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    repo = UserRepository(db)

    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    hashed = hash_password(body.password)
    user = await repo.create(email=body.email, hashed_password=hashed)
    logger.info("User registered: {}", user.email)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthTokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    today_usage = await repo.get_daily_job_count(user.id)
    logger.info("User logged in: {}", user.email)

    return AuthTokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            daily_quota=user.daily_quota,
            today_usage=today_usage,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    repo = UserRepository(db)
    today_usage = await repo.get_daily_job_count(current_user.id)
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role,
        daily_quota=current_user.daily_quota,
        today_usage=today_usage,
        created_at=current_user.created_at,
    )
