from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from telethon import types as tg_types

from package.analyzers import BaseAnalyzer
from package.models.Message import Message
from package.MyClient import MyClient


# TODO: Adjust for local time
class DayTimeAnalyzer(BaseAnalyzer):
    def __init__(self, for_chats: list[int], client: MyClient) -> None:

        super().__init__(for_chats, client)


    async def _fetch_data(self, selected_ids: list[int]):
        result = await Message.aggregate([
            {
                "$match": {
                    "raw_data.peer_id.user_id": {
                        "$in": selected_ids
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "hour_string": {
                            "$dateToString": {
                                "format": "%H",
                                "date": "$raw_data.date"
                            }
                        },
                        "message_author": { 
                            "$ifNull": [
                                "$raw_data.from_id.user_id",
                                "$raw_data.peer_id.user_id"
                            ]
                        }
                    },
                    "count": {
                        "$sum": 1
                    }
                }
            },
            {
                "$sort": {
                    "_id.hour_string": 1
                }
            },
            {
                "$project": {
                    "hour": "$_id.hour_string",
                    "author_id": "$_id.message_author",
                    "messages_count": "$count"
                }
            }
        ]).to_list()

        return result


    async def _compile_df(self, selected_ids) -> pd.DataFrame:
        data = await self._fetch_data(selected_ids)
        return pd.DataFrame.from_records(
            data
        )


    async def bar_chart(self, save_to: Path):
        # TODO: Map the users onto the db...
        all_participants: list[tg_types.User] = []
        current_id = await self.client.current_id()

        for entity_id in [*self.for_chats, current_id]:
            part = await self.client.iter_participants(
                entity_id
            ).collect()

            all_participants.extend(part)


        def get_label(user_id: int) -> str:
            for participant in all_participants:
                if participant.id != user_id:
                    continue

                part = None
                if participant.username is not None:
                    part = participant.username
                elif participant.first_name is not None:
                    part = participant.first_name

                if part is None:
                    continue

                return f'{part} <{user_id}>'

            return str(user_id)


        _, ax = plt.subplots(figsize=(24, 12))
        sns.barplot(
            self._df,
            ax=ax,
            x='hour', y='messages_count',
            alpha=0.6,
            hue="author_id"
        )

        legend = ax.get_legend()
        if legend is None:
            raise Exception("Legend object is None, when creating a plot")

        legend.set_title(None)
        for text in legend.get_texts():
            text.set_text(get_label(int(text.get_text())))

        sns.despine()
        plt.savefig(save_to.joinpath('./day_time.png'))
        plt.close(ax.get_figure())


    async def chart(self, save_to: Path, selected_ids: list[int] | None = None):
        if selected_ids is None:
            selected_ids = self.for_chats

        self._df = await self._compile_df(selected_ids)
        await self.bar_chart(save_to)
