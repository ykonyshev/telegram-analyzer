from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

import pandas as pd

from package.MyClient import MyClient

Data = TypeVar('Data')

# TODO: Utilize the for_chats property.
# Should make it more efficient, by performing one query and then selecting the needed
class BaseAnalyzer(Generic[Data], ABC):
    for_chats: list[int]


    def __init__(self, for_chats: list[int], client: MyClient) -> None:
        self.for_chats = for_chats
        self.client = client

        super().__init__()


    @abstractmethod
    def _fetch_data(self, selected_ids: list[int]) -> list[Data]:
        ...


    @abstractmethod
    async def _compile_df(self, selected_ids: list[int]) -> pd.DataFrame:
        ...


    @abstractmethod
    async def chart(self, save_to: Path, selected_ids: list[int] | None = None) -> None:
        ...
