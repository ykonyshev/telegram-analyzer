from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.figure
import matplotlib.patches
import matplotlib.pylab as plt
import pandas as pd
import seaborn as sns
from bson import ObjectId

from analysis.analyzers import BaseAnalyzer
from analysis.models.Message import Message, MessageType
from analysis.MyClient import MyClient


class TotalCountAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        for_chats: list[ObjectId],
        client: MyClient
    ) -> None:
        super().__init__(for_chats, client)


    async def _gather_data(
        self,
        selected_ids: list[ObjectId]
    ) -> list[dict[str, Any]]:
        await super()._gather_data(selected_ids)

        return await Message.aggregate([
            {
                "$match": {
                    "chat_id": { "$in": selected_ids },
                    "message_type": {
                        "$in": [MessageType.audio, MessageType.plain_text]
                    }
                }
            },
            {
                "$project": {
                    "words_count": { "$size": "$words" },
                    "raw_data": 1
                }
            },
            {
                "$group": {
                    "_id": {
                        "day_string": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$raw_data.date"
                            },
                        },
                        "message_author": { 
                            "$ifNull": [
                                "$raw_data.from_id.user_id",
                                "$raw_data.peer_id.user_id"
                            ]
                        }
                    },
                    "day_messages": {
                        "$count": {}
                    },
                    "day_words": {
                        "$sum": "$words_count"
                    }
                }
            },
            {
                "$setWindowFields": {
                    "partitionBy": "_id",
                    "sortBy": {
                        "_id": 1
                    },
                    "output": {
                        "total_messages": {
                            "$sum": "$day_messages",
                            "window": {
                                "documents": [ "unbounded", "current" ]
                            }
                        },
                        "total_words": {
                            "$sum": "$day_words",
                            "window": {
                                "documents": [ "unbounded", "current" ]
                            }
                        }
                    },
                }
            },
            {
                "$project": {
                    "message_author": "$_id.message_author",
                    "date": "$_id.day_string",
                    "total_messages": 1,
                    "total_words": 1
                }
            }
        ]
        ).to_list()


    async def _compile_df(self, selected_ids: list[ObjectId]) -> pd.DataFrame:
        data = await self._gather_data(selected_ids)
        df = pd.DataFrame.from_records(data)

        df['date'] = pd.to_datetime(df['date'])

        return df


    async def chart(
        self,
        save_to: Path,
        selected_ids: list[ObjectId] | None = None
    ) -> None:
        if selected_ids is None:
            selected_ids = self.for_chats

        df = await self._compile_df(selected_ids)

        sns.set_palette(sns.color_palette())
        sns.set_style("darkgrid", {"axes.facecolor": ".9"})

        grid = sns.FacetGrid(
            df,
            col='message_author',
            height=6, aspect=1,
            palette='deep'
        )


        grid.map(sns.lineplot, 'date', 'total_messages', color='green')
        grid.map(sns.lineplot, 'date', 'total_words', color='red')
        name_to_color = {
            'messages': 'green',
            'words': 'red',
        }

        patches = {
            k: matplotlib.patches.Patch(color=v, label=k)
            for k,v in name_to_color.items()
        }

        grid.add_legend(patches)

        # * Ignoring as there is a property
        for ax in grid.axes.flat: # type: ignore
            for label in ax.get_xticklabels():
                label.set_rotation(45)

        sns.despine(left=True)
        plt.savefig(
            save_to.joinpath('total_messages.png'),
            bbox_inches='tight'
        )

        plt.close()
