from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.main import get_db
from app.models.user import User
from app.llm.ollama_client import OllamaClient
from app.rag.base import AbstractRAGClient
from app.rag.mock import MockRAGClient
from app.rag.ragflow import RAGFlowClient
from app.services.chat_service import ChatService

security = HTTPBearer()

_rag_client: AbstractRAGClient | None = None
_chat_service: ChatService | None = None


def get_rag_client() -> AbstractRAGClient:
    global _rag_client
    if _rag_client is None:
        settings = get_settings()
        if settings.rag_mode == "ragflow":
            _rag_client = RAGFlowClient()
        else:
            _rag_client = MockRAGClient()
    return _rag_client


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        llm = OllamaClient()
        rag = get_rag_client()
        _chat_service = ChatService(llm, rag)
    return _chat_service


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    settings = get_settings()
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
