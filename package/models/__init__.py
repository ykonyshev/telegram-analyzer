from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from package.config import config


async def init_connection():
    client = AsyncIOMotorClient(config.db_connection)
    await init_beanie(
        database=client.db_name,
        document_models=[
            'package.models.Message.Message',
            'package.models.Chat.Chat'
        ]
    )
