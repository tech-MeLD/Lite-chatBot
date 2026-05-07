"""
导出 feedback + messages 数据为训练集。

高质量数据筛选条件：
- rating >= 4（用户评分高）
- 或 is_liked = True（用户点赞）
- 对话轮次完整（有 user message 和 assistant message 配对）

输出格式：
[
  {
    "messages": [
      {"role": "user", "content": "如何退货？"},
      {"role": "assistant", "content": "根据退货政策..."}
    ]
  }
]
"""

import json
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.models.message import Message, MessageRole
from app.models.feedback import Feedback
from app.models.session import Session


async def export_training_data(output_path: str, min_rating: int = 4):
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 查找高质量反馈对应的消息
        query = (
            select(Message, Feedback)
            .join(Feedback, Feedback.message_id == Message.id)
            .where(
                (Feedback.rating >= min_rating) | (Feedback.is_liked == True)
            )
            .where(Message.role == MessageRole.assistant)
        )
        result = await session.execute(query)
        pairs = result.all()

        training_data = []

        for msg, fb in pairs:
            # 获取该消息之前的 user message（对话配对）
            user_msg_result = await session.execute(
                select(Message)
                .where(
                    Message.session_id == msg.session_id,
                    Message.role == MessageRole.user,
                    Message.created_at < msg.created_at,
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            user_msg = user_msg_result.scalar_one_or_none()

            if user_msg and user_msg.content and msg.content:
                training_data.append({
                    "messages": [
                        {"role": "user", "content": user_msg.content},
                        {"role": "assistant", "content": msg.content},
                    ]
                })

    await engine.dispose()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(training_data)} high-quality conversation pairs to {output_path}")
    return len(training_data)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "training_data.json"
    asyncio.run(export_training_data(output))
