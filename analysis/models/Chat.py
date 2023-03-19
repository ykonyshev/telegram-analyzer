from beanie import Document
from beanie.operators import In
from bson import ObjectId

# TODO: Implement
# class TelegramChat(BaseModel):


class Chat(Document):
    from_perspective: int
    tg_id: int
    spoken_languages: list[str] | None = None


    @classmethod
    async def by_tg_ids(cls, tg_ids: list[int]) -> list[ObjectId]:
        chat_ids = await Chat.distinct(
            '_id',
            In(Chat.tg_id, tg_ids)
        )

        return chat_ids
