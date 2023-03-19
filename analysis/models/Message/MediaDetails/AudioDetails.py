from pathlib import Path

from pydantic import BaseModel
from telethon import types

from analysis.logging import get_logger
from analysis.MyClient import MyClient

logger = get_logger(__name__)


class AudioContents(BaseModel):
    text: str
    language: str
    model_used: str


class FileHandle(BaseModel):
    path: Path
    document_id: int


    @property
    def is_downloaded(self) -> bool:
        return self.path.exists()


    class Settings:
        bson_encodes = {
            "path": str
        }


class AudioDetails(BaseModel):
    duration: int
    voice: bool | None
    text_contents: AudioContents | None = None
    file_handle: FileHandle | None


class AudioFileHandler:
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
        local_path = self.download_folder.joinpath(
            f'{document.id}.ogg'
        ).absolute()

        self.file_handle = FileHandle(
            path=local_path,
            document_id=document.id
        )

        self.audio_details = AudioDetails(
            file_handle=self.file_handle,
            duration=audio_attribute.duration,
            voice=audio_attribute.voice
        )


    @property
    def is_downloaded(self) -> bool:
        return self.file_handle.is_downloaded


    async def download(
        self
    ) -> None:
        logger.debug(f'Downloading document, {self.document.id = } to {self.file_handle.path} ({self.document.size / 1024}kB)')

        if not self.is_downloaded:
            # * Ignoring a type error as the typing is wrong in the function and Document can also be provided.
            # * For more information see TelegramClient.download_media definition

            download_result = await self.client.download_media(
                self.media, # type: ignore
                self.file_handle.path
            )

            if download_result is None:
                logger.error(f'Media for {self.document.id = } doesn\'t seem to be a file')
                return

        logger.debug(f'Finished downloading audio from {self.document.id = } to {self.file_handle.path}')
