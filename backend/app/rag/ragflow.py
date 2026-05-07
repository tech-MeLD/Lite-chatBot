import httpx
from app.config import get_settings
from app.rag.base import AbstractRAGClient


class RAGFlowClient(AbstractRAGClient):
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.ragflow_base_url
        self.api_key = api_key or settings.ragflow_api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
        return self._client

    async def search(self, query: str, top_k: int = 5) -> list[str]:
        client = await self._get_client()
        try:
            response = await client.post(
                "/api/v1/retrieval",
                json={"question": query, "top_k": top_k},
            )
            response.raise_for_status()
            data = response.json()
            chunks = data.get("data", {}).get("chunks", [])
            return [c.get("content", "") for c in chunks[:top_k]]
        except Exception:
            return []

    async def upload_document(self, content: str, metadata: dict | None = None) -> str:
        client = await self._get_client()
        response = await client.post(
            "/api/v1/documents",
            json={"content": content, "metadata": metadata or {}},
        )
        response.raise_for_status()
        return response.json().get("data", {}).get("id", "")
