from langgraph.checkpoint.postgres import AsyncPostgresSaver

from app.config import get_settings


async def create_checkpointer() -> AsyncPostgresSaver:
    settings = get_settings()
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.database_url)
    await checkpointer.setup()
    return checkpointer
