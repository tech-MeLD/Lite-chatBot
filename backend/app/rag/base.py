from abc import ABC, abstractmethod


class AbstractRAGClient(ABC):
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[str]:
        """检索与查询最相关的文档片段"""
        ...

    @abstractmethod
    async def upload_document(self, content: str, metadata: dict | None = None) -> str:
        """上传文档到知识库，返回文档 ID"""
        ...
