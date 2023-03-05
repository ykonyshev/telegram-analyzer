from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from package.config import config
from package.logging import get_logger

logger = get_logger(__name__)


async def init_connection():
    logger.info(f'Creating a mongodb connection, {config.db_connection = }')

    client = AsyncIOMotorClient(config.db_connection)
    await init_beanie(
        database=client.db_name,
        document_models=[
            'package.models.Message.Message',
            'package.models.Chat.Chat'
        ]
    )
