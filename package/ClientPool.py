import asyncio
from itertools import cycle
from pathlib import Path
from typing import Iterator

from package.config import config
from package.logging import get_logger
from package.MyClient import MyClient

logger = get_logger(__name__)


class ClientPool:
    clients_connected: bool
    _iterator: Iterator[MyClient]

    def __init__(
        self,
        clients_number: int
    ) -> None:        
        logger.info(f'Creating a client pool with {clients_number} clients')

        self.clients_count = clients_number
        self._clients: list[MyClient] = []
        self.clients_connected = False

        for index in range(clients_number):
            new_client = MyClient(
                f'anon_{index}',
                config.telegram_api.id,
                config.telegram_api.hash
            )


            self._clients.append(new_client)


    async def setup_clients(self) -> None:
        logger.info('Connecting clients')

        authorized_start_tasks: list[asyncio.Task] = []
        for client in self._clients:
            logger.info(f'Starting client: {client.session = }')
            if client.session is None:
                logger.error('Could not start a client, session object did\'t exist')
                continue

            session_file = Path(client.session.filename)
            if session_file.exists():
                task = asyncio.create_task(client.start())
                authorized_start_tasks.append(task)
                continue

            await client.start()

        await asyncio.gather(*authorized_start_tasks)
        self.clients_connected = True


    async def disconnect_clients(self) -> None:
        for client in self._clients:
            disconnect_future = client.disconnect()

            if isinstance(disconnect_future, asyncio.Future):
                await disconnect_future


    @property
    def iterator(self) -> Iterator[MyClient]:
        if not self.clients_connected:
            raise Exception(
                'You should start the clients before trying to utilize them'
            )

        return self._iterator


    def __iter__(self):
        self._iterator = cycle(self._clients)

        return self.iterator


    def __next__(self):
        return next(self.iterator)


    def get_one(self) -> MyClient:
        return next(self.iterator)
