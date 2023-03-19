import json
from pathlib import Path

from pydantic import BaseModel

from analysis.logging import get_logger

logger = get_logger(__name__)


class Telegram(BaseModel):
    id: int
    hash: str
    phone: str
    mfa_password: str


class Config(BaseModel):
    telegram_api: Telegram
    db_connection: str

    @classmethod
    def from_file(cls, config_file_path: Path) -> "Config":
        logger.info(f'Loading config file at {config_file_path}')

        with open(config_file_path, 'r') as handle:
            contents = json.loads(handle.read())

            logger.debug(f'Loaded config values: {contents = }')

        return cls.parse_obj(contents)


config = Config.from_file(Path('./config/dev.json'))
