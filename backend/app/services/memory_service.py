import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import LongTermMemory
from app.llm.embedding_client import EmbeddingClient
from app.llm.ollama_client import OllamaClient


MEMORY_EXTRACTION_PROMPT = """从以下对话中提取关于用户的关键信息和偏好。只提取事实性信息，不要推测。

规则:
- 提取用户明确表达的需求、偏好、个人信息
- 每条记忆用简短的一句话概括
- 如果没有值得记住的信息，返回空

对话内容:
{conversation}

请以 JSON 数组格式返回提取的记忆，每条格式: {{"type": "preference|fact|behavior", "content": "记忆内容"}}
如果没有可提取的记忆，返回空数组 [].

只返回 JSON 数组，不要其他文字:"""


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._embedding_client = EmbeddingClient()

    async def store_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "fact",
    ) -> LongTermMemory:
        embedding = await self._embedding_client.embed(content)
        memory = LongTermMemory(
            user_id=uuid.UUID(user_id),
            embedding=embedding,
            memory_type=memory_type,
            content={"text": content, "type": memory_type},
        )
        self.db.add(memory)
        await self.db.flush()
        return memory

    async def retrieve_relevant(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[str]:
        query_embedding = await self._embedding_client.embed(query)

        result = await self.db.execute(
            select(LongTermMemory)
            .where(LongTermMemory.user_id == uuid.UUID(user_id))
            .order_by(
                LongTermMemory.embedding.cosine_distance(query_embedding)
            )
            .limit(top_k)
        )
        memories = result.scalars().all()
        return [m.content.get("text", "") for m in memories if m.content.get("text")]

    async def extract_and_store(
        self,
        user_id: str,
        conversation: str,
        llm: OllamaClient,
    ) -> int:
        prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conversation)
        try:
            response = await llm.chat(prompt)
            import json
            # Strip markdown code block if present
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            memories = json.loads(response.strip())
        except Exception:
            return 0

        if not isinstance(memories, list):
            return 0

        count = 0
        for item in memories:
            if not isinstance(item, dict):
                continue
            content = item.get("content", "")
            mem_type = item.get("type", "fact")
            if content:
                await self.store_memory(user_id, content, mem_type)
                count += 1

        return count
