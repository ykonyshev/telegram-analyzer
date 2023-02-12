import tqdm
from telethon import TelegramClient, types
from telethon.hints import EntityLike

from package.models import Message
from package.models.Chat import Chat
from package.models.Message.MessageMedia import SupportedMedia


class MyClient(TelegramClient):
    _current_id: int | None = None

    async def current_id(self):
        if self._current_id is not None:
            return self._current_id

        me = await self.get_me()
        if isinstance(me, types.User):
            self._current_id = me.id
        else:
            self._current_id = me.user_id

        return self._current_id

    async def gather_messages(
        self,
        from_entity: EntityLike,
        limit: int
    ) -> list[Message.Message]:
        current_dialog = await self.get_input_entity(from_entity)
        if not isinstance(current_dialog, types.InputPeerUser):
            return []

        chat = await Chat.find_one(
            Chat.with_id == current_dialog.user_id
        )

        if chat is None:
            chat = Chat(
                with_id=current_dialog.user_id
            )

            await chat.create()

        messages = self.iter_messages(
            from_entity,
            limit=limit
        )

        current_id = await self.current_id()
        db_messages = []
        part = []

        # TODO: Maybe it will be faster to load everything in and then create tasks
        # TODO: More optimization may make sense, but after check if everying is there
        message: types.Message
        with tqdm.tqdm(total=limit) as pbar:
            async for message in messages:
                pbar.update(1)
                predicate = await Message.Message.find_one(
                    Message.Message.chat_id == chat.id,
                    Message.Message.raw_data.id == message.id,
                    Message.Message.from_perspective == current_id
                )

                if predicate is not None:
                    db_messages.append(predicate)
                    continue

                raw_api_data = message.to_dict()

                # TODO Implement other media
                if isinstance(message.media, SupportedMedia):
                    media_data = raw_api_data['media']
                else:
                    media_data = None

                raw_api_data['media'] = media_data

                raw_classes = {
                    types.MessageService: Message.TelegramServiceMessage,
                    types.Message: Message.TelegramMessage
                }

                # FIXME
                if chat.id is None:
                    continue

                new_message = Message.Message(
                    chat_id=chat.id,
                    from_perspective=current_id,
                    raw_data=raw_classes[type(message)](**raw_api_data)
                )

                part.append(new_message)
                if len(part) >= 100:
                    await Message.Message.insert_many(part)

                    db_messages.extend(part)
                    part = []

            await Message.Message.insert_many(part)
            db_messages.extend(part)

            return db_messages
