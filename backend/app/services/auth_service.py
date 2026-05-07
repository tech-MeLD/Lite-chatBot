from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def login_with_wechat(self, code: str) -> tuple[str, User]:
        if self.settings.wechat_mock_enabled:
            return await self._mock_login(code)
        return await self._real_wechat_login(code)

    async def _mock_login(self, code: str) -> tuple[str, User]:
        wx_openid = f"mock_openid_{hash(code) % 1000000:06d}"

        result = await self.db.execute(
            select(User).where(User.wx_openid == wx_openid)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                wx_openid=wx_openid,
                nickname=f"用户{wx_openid[-4:]}",
            )
            self.db.add(user)
            await self.db.flush()

        token = self._create_token(user)
        return token, user

    async def _real_wechat_login(self, code: str) -> tuple[str, User]:
        # TODO: Implement real WeChat OAuth flow
        raise NotImplementedError("Real WeChat OAuth not implemented yet")

    async def get_user(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def _create_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.jwt_expire_minutes
        )
        payload = {
            "sub": str(user.id),
            "exp": expire,
        }
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.jwt_algorithm)
