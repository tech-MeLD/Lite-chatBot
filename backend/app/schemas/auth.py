from pydantic import BaseModel


class LoginRequest(BaseModel):
    code: str


class UserInfo(BaseModel):
    id: str
    nickname: str
    avatar_url: str | None = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo
