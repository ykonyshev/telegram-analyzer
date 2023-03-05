import asyncio
import typing
from pathlib import Path
from typing import AsyncIterator, cast

from telethon import TelegramClient, functions, types

from package.config import config

CHUNK_SIZE = 100


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

    async def start(self) -> None:
        # * The function returns a coro, but the types are wrong
        await cast(
            typing.Coroutine[None, None, MyClient],
            super().start(
                phone=lambda: config.telegram_api.phone,
                password=lambda: config.telegram_api.mfa_password
            )
        )


    async def get_history(
        self,
        peer: types.TypeInputPeer,
        total: int,
        messages_hash=0
    ) -> AsyncIterator[types.messages.MessagesSlice]:
        wait_time = 0 if total < CHUNK_SIZE * 15 else 1
        for offset in range(0, total // CHUNK_SIZE + 1):
            response = await self(
                functions.messages.GetHistoryRequest(
                    peer=peer,
                    limit=CHUNK_SIZE,
                    add_offset=offset * CHUNK_SIZE,
                    hash=messages_hash,
                    offset_date=None, offset_id=0,
                    max_id=0, min_id=0
                )
            )

            await asyncio.sleep(wait_time)

            response = cast(
                types.messages.MessagesSlice,
                response
            )

            yield response


    async def total_messages_count(
        self,
        peer: types.TypeInputPeer
    ):
        history = await anext(self.get_history(
            peer,
            1
        ))

        return history.count


    async def download_media(
        self,
        media: types.MessageMediaDocument,
        to: Path
    ) -> Path | None:
        download_result = await super().download_media(
            media, # type: ignore
            str(to),
        )

        if isinstance(download_result, str):
            return Path(download_result)

        return None
