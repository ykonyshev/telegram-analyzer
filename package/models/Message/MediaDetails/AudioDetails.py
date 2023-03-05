from pathlib import Path

from pydantic import BaseModel
from telethon import types

from package.logging import get_logger
from package.MyClient import MyClient

logger = get_logger(__name__)


class AudioContents(BaseModel):
    text: str
    language: str


class AudioDetails(BaseModel):
    duration: int
    document_id: int | None
    voice: bool | None
    text_contents: AudioContents | None = None


class AudioHandler:
    audio_details: AudioDetails
    client: MyClient
    download_folder: Path
    document: types.Document


    def __init__(
        self,
        client: MyClient,
        audio_download_folder: Path,
        media: types.MessageMediaDocument,
        audio_attribute: types.DocumentAttributeAudio,
    ) -> None:
        self.client = client
        self.media = media
        self.download_folder = audio_download_folder

        document = media.document
        if not isinstance(document, types.Document):
            logger.error('There seems like a wrong document was passed to create AudioDetails')
            return

        self.document = document
        self.local_path = self.download_folder.joinpath(
            f'{document.id}'
        ).absolute()

        self.audio_details = AudioDetails(
            duration=audio_attribute.duration,
            document_id=document.id,
            voice=audio_attribute.voice
        )


    @property
    def is_downloaded(self) -> bool:
        return self.local_path.exists()


    async def download(
        self
    ):
        logger.debug(f'Downloading document, {self.document.id = } to {self.local_path} ({self.document.size / 1024}kB)')

        if not self.is_downloaded:
            # * Ignoring a type error as the typing is wrong in the function and Document can also be provided.
            # * For more information see TelegramClient.download_media definition

            download_result = await self.client.download_media(
                self.media, # type: ignore
                self.local_path
            )

            if download_result is None:
                logger.error(f'Media for {self.document.id = } doesn\'t seem to be a file')
                return

        logger.debug(f'Finished downloading audio from {self.document.id = } to {self.local_path}')
