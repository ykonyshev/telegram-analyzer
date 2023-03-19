from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from analysis.config import config
from analysis.logging import get_logger

logger = get_logger(__name__)


async def init_connection() -> None:
    logger.info(f'Creating a mongodb connection, {config.db_connection = }')

    client = AsyncIOMotorClient(config.db_connection)
    await init_beanie(
        database=client.db_name,
        document_models=[
            'analysis.models.Message.Message',
            'analysis.models.Chat.Chat',
            'analysis.models.Task.Task'
        ]
    )
