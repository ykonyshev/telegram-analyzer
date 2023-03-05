from pathlib import Path
from typing import Any

import matplotlib.pylab as plt
import pandas as pd
import seaborn as sns
from bson import ObjectId

from package.analyzers import BaseAnalyzer
from package.models import Message
from package.MyClient import MyClient


class VoiceDurationAnalyzer(BaseAnalyzer):
    def __init__(self, for_chats: list[ObjectId], client: MyClient) -> None:
        super().__init__(for_chats, client)


    async def _gather_data(self, selected_ids: list[ObjectId]) -> list[dict[str, Any]]:
        await super()._gather_data(selected_ids)

        result = await Message.Message.aggregate([  
            { 
                "$match": {
                    "chat_id": { "$in": selected_ids },
                    "message_type": Message.MessageType.audio,
                    "media_details": {
                        "$ne": None
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "chat_id": "$chat_id",
                        "date_string": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$raw_data.date"
                            }
                        }
                    },
                    "max": { "$max": { "$sum": "$media_details.duration" }},
                }
            },
            {
                "$project": {
                    "date": "$_id.date_string",
                    "max": 1
                }
            }
        ]).to_list()

        return result


    async def _compile_df(self, selected_ids: list[ObjectId]) -> pd.DataFrame | None:
        data = await self._gather_data(selected_ids)
        if len(data) == 0:
            return None

        df = pd.DataFrame.from_records(data)
        df['date'] = pd.to_datetime(df['date'])

        return df


    async def chart(self, save_to: Path, selected_ids: list[ObjectId] | None = None):
        if selected_ids is None:
            selected_ids = self.for_chats

        df = await self._compile_df(selected_ids)
        if df is None:
            return

        fig, ax = plt.subplots(figsize=(12, 6))
        ax: plt.Axes = sns.scatterplot(
            df,
            ax=ax,
            x='date',
            y='max'
        )

        plt.savefig(save_to.joinpath('voice_message_duration.png'))
        plt.close(fig)
