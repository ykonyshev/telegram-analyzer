from collections import defaultdict
from pathlib import Path
from textwrap import wrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from beanie.operators import In

from package.analyzers import BaseAnalyzer
from package.models.Message import Message, TelegramMessage
from package.MyClient import MyClient

EXCLUDE_CHARS = '.,!?/\\()"\'-—+-=%^&$#@*_\n<>'
EXCLUDE = str.maketrans({
    char: None for char in list(EXCLUDE_CHARS)
})


def word_aggregator(words: pd.Series):
    return "\n".join(wrap(' '.join(words), max_lines=2))


# TODO: Also by person data in terms of words usage
class WordCountAnalyzer(BaseAnalyzer[Message]):
    def __init__(
        self,
        for_chats: list[int],
        client: MyClient
    ) -> None:
        super().__init__(for_chats, client)

        self._accumulator = defaultdict(lambda: 0)


    async def _fetch_data(self, selected_ids: list[int]):
        return await Message.find(
            In(Message.raw_data.peer_id.user_id, selected_ids),
            lazy_parse=True
        ).to_list()


    def parse_text(self, text: str) -> None:
        clean = text.lower().translate(EXCLUDE).strip()
        if len(clean) <= 0:
            return

        for word in clean.split(' '):
            if len(word.strip()) <= 0:
                continue

            self._accumulator[word] += 1


    async def _compile_df(self, selected_ids: list[int]) -> pd.DataFrame:
        messages = await self._fetch_data(selected_ids)

        for message in messages:
            if not isinstance(message.raw_data, TelegramMessage):
                continue

            self.parse_text(message.raw_data.message)

        # TODO: Cache dataframe data in the filesystem
        df = pd.DataFrame(
            {
                "word": list(self._accumulator.keys()),
                "count": list(self._accumulator.values())
            },
            index=np.arange(len(self._accumulator)),
        )

        aggregators = {
            'word': word_aggregator
        }

        return df.groupby(df['count']) \
            .aggregate(aggregators) \
            .sort_values('count', ascending=False) \
            .reset_index()


    def total_words(self) -> int:
        return sum(self._accumulator.values())


    def _complete_plot(self, save_to: Path):
        plt.tight_layout()
        sns.despine(left=True)
        plt.savefig(save_to)
        plt.close()


    def bar_chart_horizontal(self, save_to: Path) -> None:
        plt.subplots(figsize=(50, 16))
        ax = sns.barplot(
            self._df,
            x='word', y='count',
            errorbar="sd", palette="dark",
            alpha=.6,
        )

        ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="center", fontsize=9)

        for container in ax.containers:
            ax.bar_label(container, rotation=90, size=8, padding=5)

        self._complete_plot(save_to.joinpath('./h_bar_words.png'))
        plt.close(ax.get_figure())


    def bar_chart_vertical(self, save_to: Path) -> None:
        plt.subplots(figsize=(16, 50))
        ax: plt.Axes = sns.barplot(
            self._df,
            x='count', y='word',
            errorbar="sd", palette="dark",
            alpha=.6,
        )

        ax.set_yticklabels(ax.get_yticklabels(), ha="right", fontsize=9)

        for container in ax.containers: # type: ignore
            ax.bar_label(container, size=8, padding=5)

        self._complete_plot(save_to.joinpath('./v_bar_words.png'))
        plt.close(ax.get_figure())


    async def chart(self, save_to: Path, selected_ids: list[int] | None = None) -> None:
        if selected_ids is None:
            selected_ids = self.for_chats

        self._df = await self._compile_df(selected_ids)

        if not save_to.exists():
            save_to.mkdir()

        self.bar_chart_vertical(save_to)
        self.bar_chart_horizontal(save_to)
