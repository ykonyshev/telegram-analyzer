from beanie import Document

# TODO: Implement
# class TelegramChat(BaseModel):
#     id: int


class Chat(Document):
    # raw_data: TelegramChat
    with_id: int
