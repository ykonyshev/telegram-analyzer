from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

import pandas as pd
from bson import ObjectId

from package.MyClient import MyClient

Data = TypeVar('Data')


class BaseAnalyzer(Generic[Data], ABC):
    for_chats: list[ObjectId]


    def __init__(self, for_chats: list[ObjectId], client: MyClient) -> None:
        self.for_chats = for_chats
        self.chat_ids = []
        self.client = client

        super().__init__()


    @abstractmethod
    async def _gather_data(self, selected_ids: list[ObjectId]) -> list[Data]:
        ...


    @abstractmethod
    async def _compile_df(self, selected_ids: list[ObjectId]) -> pd.DataFrame:
        ...


    @abstractmethod
    async def chart(
        self,
        save_to: Path,
        selected_ids: list[ObjectId] | None = None,
        slice_size: int = 250,
    ) -> None:
        ...
