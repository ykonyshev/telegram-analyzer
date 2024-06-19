import asyncio
from pathlib import Path
from typing import Any, Type

from bson import ObjectId

from analysis.analyzers import BaseAnalyzer
from analysis.ClientPool import ClientPool
from analysis.logging import get_logger
from analysis.models.Chat import Chat
from analysis.Reporter.ChatHandler import ChatHandler
from analysis.utils.LoggerTimer import LoggerTimer

logger = get_logger(__name__)
AnalyzerClasses = list[Type[BaseAnalyzer[Any]]]


class Reporter:
    def __init__(
        self,
        for_chats: list[int],
        graphs_folder: Path,
        media_download_folder: Path,
        analyzer_classes: AnalyzerClasses = [],
        gather_limit: int | None = None,
        skip_gather: bool = False
    ) -> None:
        self.for_chats = for_chats

        self.gather_limit = gather_limit
        self.skip_gather = skip_gather

        self.base_graphs_folder = graphs_folder 

        self.media_folder = media_download_folder
        self.client_pool = ClientPool(len(for_chats))

        self._analyzers: list[BaseAnalyzer[Any]] = []
        self._base_analyzers: AnalyzerClasses = analyzer_classes


    async def setup(self) -> None:
        await self.client_pool.setup_clients()
        self.db_chat_ids = await Chat.by_tg_ids(self.for_chats)

        if len(self._base_analyzers) > 0:
            self.add_analyzer(*self._base_analyzers)
            self._base_analyzers = []


    async def close(self) -> None:
        await self.client_pool.disconnect_clients()


    # TODO: Include the username of some other identification infortaion in the output folder name
    def graphs_folder(self, select_ids: list[ObjectId]) -> Path:
        sub_folder = Path('_'.join(map(str, select_ids)))
        for_graphs = self.base_graphs_folder.joinpath(sub_folder)

        if not for_graphs.exists():
            logger.info(f'Creating graphs output folder at {for_graphs.absolute()}')
            for_graphs.mkdir(parents=True)

        return for_graphs


    def add_analyzer(self, *analyzer_classes: Type[BaseAnalyzer[Any]]) -> None:
        logger.info(f'Added analyzers: {analyzer_classes}')

        for _class, client in zip(analyzer_classes, self.client_pool):
            self._analyzers.append(_class(self.db_chat_ids, client))


    async def _gather(
        self
    ) -> None:
        tasks = []
        for chat_id, client in zip(self.for_chats, self.client_pool):
            participants = await client.get_participants(chat_id)
            task = asyncio.Task(ChatHandler(
                client,
                participants[0],
                self.gather_limit,
                self.media_folder
            ).gather())

            tasks.append(task)

        await asyncio.gather(*tasks)


    async def __aenter__(self) -> 'Reporter':
        await self.setup()
        if not self.skip_gather:
            await self._gather()

        return self


    async def __aexit__(self, *_) -> None:
        await self.close()


    async def chart_all(self, for_ids: list[ObjectId] | None = None) -> None:
        if for_ids is None:
            for_ids = self.db_chat_ids

        for analyzer in self._analyzers:
            with LoggerTimer(
                'Took {:2f} to run {} for {}',
                analyzer.__class__.__name__,
                for_ids
            ):
                await analyzer.chart(self.graphs_folder(for_ids), for_ids)


    async def generate_full_report(self) -> None:
        logger.info(f'Doing a full report for {self.for_chats}')
        await self.chart_all()


    async def generate_individual(self) -> None:
        logger.info('Starting with invidual reports')

        for chat_id in self.db_chat_ids:
            await self.chart_all([chat_id])
