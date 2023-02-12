from pathlib import Path
from typing import Type

from package.analyzers import BaseAnalyzer
from package.models.Chat import Chat
from package.MyClient import MyClient


class Reporter:
    def __init__(
        self,
        for_chats: list[int],
        client: MyClient,
        graphs_folder: Path
    ):
        self.for_chats = for_chats
        self.client = client

        self.base_graphs_folder = graphs_folder 
        self._analyzers: list[BaseAnalyzer] = []


    def graphs_folder(self, select_ids: list[int] | None = None) -> Path:
        if select_ids is None:
            select_ids = self.for_chats

        sub_folder = Path('_'.join(map(str, select_ids)))
        for_graphs = self.base_graphs_folder.joinpath(sub_folder)

        if not for_graphs.exists():
            for_graphs.mkdir(parents=True)

        return for_graphs


    def add_analyzer(self, *analyzer_classes: Type[BaseAnalyzer]):
        for _class in analyzer_classes:
            self._analyzers.append(_class(self.for_chats, self.client))


    async def gather_missing_messages(self):
        for chat_id in self.for_chats:
            predicate = await Chat.find_one(
                Chat.with_id == chat_id
            )

            # TODO: Need to check if we have all the messages from the chat over here
            if predicate is not None:
                continue

            await self.client.gather_messages(
                chat_id,
                25000
            )


    async def generate_full_report(self) -> None:
        for analyzer in self._analyzers:
            await analyzer.chart(self.graphs_folder())


    async def generate_individual(self) -> None:
        for chat_id in self.for_chats:
            for analyzer in self._analyzers:
                await analyzer.chart(self.graphs_folder([chat_id]), [chat_id])
