from beanie import Document
from beanie.operators import In
from bson import ObjectId

# TODO: Implement
# class TelegramChat(BaseModel):
#     id: int


class Chat(Document):
    # raw_data: TelegramChat
    from_perspective: int
    tg_id: int

    @classmethod
    async def by_tg_ids(cls, tg_ids: list[int]) -> list[ObjectId]:
        chat_ids = await Chat.distinct(
            '_id',
            In(Chat.tg_id, tg_ids)
        )

        return chat_ids
