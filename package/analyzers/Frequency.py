from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from bson import ObjectId
from matplotlib import ticker

from package.analyzers import BaseAnalyzer
from package.models.Message import Message
from package.MyClient import MyClient


class FrequencyAnalyzer(BaseAnalyzer[Any]):
    def __init__(self, for_chats: list[ObjectId], client: MyClient) -> None:
        super().__init__(for_chats, client)


    async def _compile_df(self, selected_ids: list[ObjectId]) -> pd.DataFrame:
        data = await self._gather_data(selected_ids)
        return pd.DataFrame.from_records(
            data
        )


    async def _gather_data(
        self,
        selected_ids: list[ObjectId]
    ):
        await super()._gather_data(selected_ids)

        result = await Message.aggregate(
            [{
                "$match": {
                    "chat_id": {
                        "$in": selected_ids
                    }
                },
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$raw_data.date"
                        }
                    },
                    "count": {
                        "$sum": 1
                    },
                    "raw_date": {
                        "$avg": {
                            "$toLong": "$raw_data.date"
                        }
                    }
                }
            },
            {
                "$sort": {
                    "_id": 1
                }
            },
            {
                "$project": {
                    "date": "$_id",
                    "date_num": {
                        "$toLong": "$raw_date"
                    },
                    "count": "$count"
                }
            }]
        ).to_list()

        return result


    async def chart(
        self,
        save_to: Path,
        selected_ids: list[ObjectId] | None = None
    ) -> None:
        if selected_ids is None:
            selected_ids = self.for_chats

        df = await self._compile_df(selected_ids)

        @ticker.FuncFormatter
        def fake_dates(x, _):
            return datetime.fromtimestamp(x / 1000).strftime('%Y-%m-%d')

        sns.set_theme(style="darkgrid")
        result: sns.JointGrid = sns.jointplot(
            data=df,
            x='date_num', y='count',
            color="g",
            height=7,
            lowess=True,
            kind='reg',
            marginal_ticks=True,
            ratio=3
        )

        result.set_axis_labels('Date (day)','Messages count')
        current_firgure = result.ax_joint.get_figure()
        current_firgure.set_size_inches(16, 8)
        result.ax_joint.xaxis.set_major_formatter(fake_dates)
        sns.despine()

        plt.savefig(save_to.joinpath('./messages_per_day_frequency.png'))
        plt.close(current_firgure)
