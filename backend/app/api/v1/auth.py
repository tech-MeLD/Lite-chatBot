from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    token, user = await auth_service.login_with_wechat(request.code)
    return LoginResponse(
        access_token=token,
        user=UserInfo(
            id=str(user.id),
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
        ),
    )


@router.get("/me", response_model=UserInfo)
async def get_me(user: User = Depends(get_current_user)):
    return UserInfo(
        id=str(user.id),
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
    )
