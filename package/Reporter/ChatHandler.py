import asyncio
from pathlib import Path
from typing import AsyncIterable

import tqdm
from telethon import types

from package.logging import get_logger
from package.models import Message
from package.models.Chat import Chat
from package.models.Message.MediaDetails.AudioDetails import AudioHandler
from package.models.Message.MessageMedia import SupportedMedia
from package.MyClient import MyClient
from package.utils.format_user import format_user

logger = get_logger(__name__)
CHUNK_SIZE = 100


# TODO: In order for the hash to work there is also a need to take into account the service messages, as they have ids as well
def compute_hash(ids: list[int]) -> int:
    result = 0
    for _id in ids:
        result = result ^ (_id >> 21)
        result = result ^ (_id << 35)
        result = result ^ (_id >> 4)
        result = result + _id

    return result


class ChatHandler:
    def __init__(
        self,
        tg_client: MyClient,
        user: types.User,
        limit: int | None,
        download_dir: Path
    ) -> None:
        self.client = tg_client
        self.limit = limit
        self.download_dir = download_dir

        self.user = user

        if user.access_hash is None:
            raise ValueError('User access hash can not be None')

        self.download_tasks: set[asyncio.Task] = set()
        self.input_entity = types.InputPeerUser(
            user.id,
            user.access_hash
        )


    async def _get_messages(
        self,
        total: int,
        _hash: int
    ) -> AsyncIterable[list[types.Message]]:
        async for chunk in self.client.get_history(
            self.input_entity,
            total,
            _hash
        ):
            messages = [
                message for message in chunk.messages if isinstance(
                    message,
                    types.Message
                )
            ]

            yield messages


    async def _download_media(
        self,
        media: SupportedMedia,
        audio_folder: Path
    ) -> tuple[Message.MessageType, Message.MediaDetails] | None:
        media_details: Message.MediaDetails = []
        message_type = Message.MessageType.other

        # TODO: Implement gathering inforation for photos
        if isinstance(media, types.MessageMediaPhoto):
            message_type = Message.MessageType.photo

        elif isinstance(media, types.MessageMediaDocument) \
            and not isinstance(media.document, types.DocumentEmpty) \
            and media.document is not None:

            document = media.document
            audio_attributes = [
                attr for attr in document.attributes if isinstance(
                    attr,
                    types.DocumentAttributeAudio
                )
            ]

            if len(audio_attributes) == 0:
                return message_type, media_details

            elif len(audio_attributes) >= 2:
                logger.error(f'Document {document.id = } seems to be having more than one audio attrbute, you should look into it, skipping the document')

                return message_type, media_details

            message_type = Message.MessageType.audio
            handler = AudioHandler(
                self.client,
                audio_folder,
                media,
                audio_attributes[0]
            )

            media_details.append(handler.audio_details)
            self.download_tasks.add(asyncio.create_task(handler.download()))

        return message_type, media_details


    async def gather(
        self
    ) -> list[Message.Message] | None:
        current_id = await self.client.current_id()

        logger.info(f'Gatherting messages for {format_user(self.user)} from perspective of {current_id}')

        if not isinstance(self.user, types.User):
            raise NotImplementedError('We support only types.InputPeerChat')

        audio_folder = self.download_dir.joinpath(
            f'{current_id}_{self.user.id}'
        )

        if not audio_folder.exists():
            audio_folder.mkdir(parents=True)

        chat = await Chat.find_one(
            Chat.tg_id == self.user.id,
            Chat.from_perspective == current_id,
        )

        if chat is None:
            chat = Chat(
                from_perspective=current_id,
                tg_id=self.user.id,
            )

            await chat.create()

        total_count = await self.client.total_messages_count(self.input_entity)
        ids = await Message.Message.distinct('tg_id', {
            'chat_id': chat.id,
            'from_perspective': current_id
        })

        db_messages: list[Message.Message] = []
        ids_set = set(ids)

        logger.info(f'{len(ids)} messages from {self.user.id} are already present in the DB from a total of {total_count} messages')

        if self.limit is None:
            limit = total_count
        else:
            limit = min(self.limit, total_count)

        messages_iter = self._get_messages(
            limit,
            compute_hash(ids)
        )

        logger.info(f'Starting to gather messages from {format_user(self.user)}, {limit = }')
        message: types.Message
        pbar = tqdm.tqdm(
            desc=f'For {format_user(self.user)} in chat {self.user.id}',
            total=limit
        )

        async for chunk in messages_iter:
            for message in chunk:
                pbar.update(1)

                # TODO: Also check for some other fields to get updated data or maybe setup event handlers, so it will help catch-up the lost updates
                if message.id in ids_set:
                    continue

                raw_api_data = message.to_dict()

                media_details: Message.MediaDetails = []
                message_type = Message.MessageType.plain_text

                if isinstance(message.media, SupportedMedia):
                    result = await self._download_media(
                        message.media,
                        audio_folder
                    )

                    if result is not None:
                        message_type, media_details = result
                else:
                    raw_api_data['media'] = None

                if chat.id is None:
                    logger.error(f'{chat.dict() = } is None for some reasons')
                    continue

                result_details = None if len(media_details) == 0 else media_details
                new_message = Message.Message(
                    chat_id=chat.id,
                    tg_id=message.id,
                    message_type=message_type,
                    media_details=result_details,
                    from_perspective=current_id,
                    raw_data=Message.TelegramMessage.parse_obj(raw_api_data)
                )

                db_messages.append(new_message)

        if len(self.download_tasks) > 0:
            await asyncio.wait(self.download_tasks)

        if len(db_messages) > 0:
            logger.debug(f'Inserting {len(db_messages)} messages into the db')

            for db_message in db_messages:
                db_message.words = db_message.parse_words()

            # TODO: Implement saves in slices of 250 items or something like that
            await Message.Message.insert_many(db_messages)

        pbar.close()
        return db_messages
