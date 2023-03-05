from collections import defaultdict
from pathlib import Path
from textwrap import wrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from beanie.operators import In
from bson import ObjectId

from package.analyzers import BaseAnalyzer
from package.models.Message import Message, MessageType, TelegramMessage
from package.MyClient import MyClient

TEXT_MESSAGE_TYPES = [MessageType.audio, MessageType.plain_text]
EXCLUDE_CHARS = '.,!?/\\()"\'-—+-=%^&$#@*_\n<>'
EXCLUDE = str.maketrans({
    char: None for char in list(EXCLUDE_CHARS)
})


def word_aggregator(words: pd.Series):
    return "\n".join(wrap(' '.join(words), max_lines=2))


class WordCountAnalyzer(BaseAnalyzer[Message]):
    def __init__(
        self,
        for_chats: list[ObjectId],
        client: MyClient
    ) -> None:
        super().__init__(for_chats, client)

        self._accumulator = defaultdict(lambda: 0)
        self._base_df = pd.DataFrame()


    def parse_text(self, message: Message) -> None:
        for word in message.parse_words():
            self._accumulator[tuple([word, message.message_type])] += 1


    async def _gather_data(self, selected_ids: list[ObjectId]):
        await super()._gather_data(selected_ids)

        return await Message.find(
            In(Message.chat_id, selected_ids),
            In(Message.message_type, TEXT_MESSAGE_TYPES)
        ).to_list()


    async def _compile_df(
        self,
        selected_ids: list[ObjectId],
        slice_size: int = 250
    ) -> pd.DataFrame:
        messages = await self._gather_data(selected_ids)
        for message in messages:
            if not isinstance(message.raw_data, TelegramMessage):
                continue

            self.parse_text(message)

        words, message_types = list(zip(*self._accumulator.keys()))
        base_df = pd.DataFrame(
            {
                "word": words,
                "message_type": message_types,
                "count": list(self._accumulator.values())
            },
            index=np.arange(len(self._accumulator)),
        ).sort_values('count', ascending=False) \
            .reset_index(drop=True)

        aggregated = base_df.groupby(
            ['word'],
            as_index=False,
            sort=False
        ).aggregate({
            'count': list,
        })

        aggregated['summed_from_types'] = aggregated['count'].apply(np.sum)
        merged = pd.merge(base_df, aggregated.drop('count', axis=1), on='word')

        return merged.head(slice_size).groupby(
            ['summed_from_types', 'message_type'],
            as_index=False,
            sort=False
        ).aggregate({
            'word': word_aggregator,
            'count': np.min
        })


    def _complete_plot(self, save_to: Path):
        plt.tight_layout()
        sns.despine(left=True)
        plt.savefig(save_to)
        plt.close()


    def bar_chart_horizontal(
        self,
        data: pd.DataFrame,
        save_to: Path
    ) -> None:
        plt.subplots(figsize=(50, 16))
        ax = sns.barplot(
            data,
            hue='message_type',
            x='word', y='count',
            errorbar="sd", palette="dark",
            alpha=.6,
        )

        ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="center", fontsize=9)

        for container in ax.containers:
            ax.bar_label(container, rotation=90, size=8, padding=5)

        self._complete_plot(save_to.joinpath('./h_bar_words.png'))
        plt.close(ax.get_figure())


    def bar_chart_vertical(
        self,
        data: pd.DataFrame,
        save_to: Path
    ) -> None:
        plt.subplots(figsize=(16, 50))
        ax: plt.Axes = sns.barplot(
            data,
            hue='message_type',
            x='count', y='word',
            errorbar="sd", palette="dark",
            alpha=.6,
        )

        ax.set_yticklabels(ax.get_yticklabels(), ha="right", fontsize=9)

        for container in ax.containers: # type: ignore
            ax.bar_label(container, size=8, padding=5)

        self._complete_plot(save_to.joinpath('./v_bar_words.png'))
        plt.close(ax.get_figure())


    async def chart(
        self,
        save_to: Path,
        selected_ids: list[ObjectId] | None = None,
        data_slice_size: int = 250
    ) -> None:
        if selected_ids is None:
            selected_ids = self.for_chats

        if not save_to.exists():
            save_to.mkdir()

        df = await self._compile_df(
            selected_ids,
            data_slice_size
        )

        self.bar_chart_vertical(df, save_to)
        self.bar_chart_horizontal(df, save_to)
