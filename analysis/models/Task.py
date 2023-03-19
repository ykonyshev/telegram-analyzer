from beanie import Document, PydanticObjectId


class Task(Document):
    message_id: PydanticObjectId
