from datetime import datetime
from typing import Optional, Union

import pymongo
from beanie import Document, PydanticObjectId, SaveChanges, before_event
from pydantic import BaseModel, Field

from package.models.Message.MessageMedia import MessageMediaDocument, MessageMediaPhoto


class PeerUser(BaseModel):
    # FIXME: In some cases the is an error, I suppose it occures when there is nothing to do with PerrUser, in the fwd_from, but we are still trying to use PeerUser
    user_id: int | None


class PeerChat(BaseModel):
    chat_id: int


class ForwardInfo(BaseModel):
    date: datetime
    imported: Union[bool, None]
    from_id: Union[PeerUser, None]
    from_name: Union[str, None]
    channel_post: Union[int, None]
    post_author: Union[str, None]
    saved_from_peer: Union[PeerUser, None]
    saved_from_msg_id: Union[int, None]


class ReplyInfo(BaseModel):
    reply_to_msg_id: int
    reply_to_peer_id: Union[PeerChat, None]
    # forum_topic: None
    reply_to_top_id: Union[int, None]


class Replies(BaseModel):
    comments: Union[bool, None]
    replies: int
    replies_pts: int
    recent_repliers: Union[list[PeerUser], None]
    channel_id: Union[int, None]
    max_id: Union[int, None]
    read_max_id: Union[int, None]


class Reaction(BaseModel):
    emoticon: str

class ReactionCount(BaseModel):
    count: int
    reaction: Reaction
    chosen_order: Union[int, None]

class PeerReaction(BaseModel):
    peer_id: PeerUser
    reaction: Reaction
    big: Union[bool, None]
    unread: Union[bool, None]


class Reactions(BaseModel):
    min: Optional[bool]
    can_see_list: bool
    results: Optional[list[ReactionCount]] = None
    recent_reactions: Optional[list[PeerReaction]] = None

class BaseTelegramMessage(BaseModel):
    id: int
    peer_id: PeerUser
    from_id: Optional[PeerUser]
    reply_to: Optional[ReplyInfo]
    date: Union[datetime, None]
    mentioned: Union[bool, None]
    out: Union[bool, None]
    media_unread: Union[bool, None]
    post: Union[bool, None]
    legacy: Union[bool, None]
    ttl_period: Union[int, None]


class TelegramServiceMessage(BaseTelegramMessage):
    # action: MessageAction
    ...


class TelegramMessage(BaseTelegramMessage):
    message: str
    fwd_from: Union[ForwardInfo, None] = None
    reactions: Optional[Reactions]
    edit_date: Union[datetime, None]
    silent: Union[bool, None]
    from_scheduled: Union[bool, None]
    edit_hide: Union[bool, None]
    pinned: Union[bool, None]
    noforwards: Union[bool, None]
    via_bot_id: Union[int, None]
    media: MessageMediaPhoto | MessageMediaDocument | None
    # TODO: Store the entities?
    # entities: None
    views: Union[int, None]
    forwards: Union[int, None]
    replies: Union[Replies, None]
    post_author: Union[str, None]
    grouped_id: Union[int, None]
    # TODO: Do I need it?
    # restricition_reason: None


# TODO: Make both ids properly available on the model, check the quiers
class Message(Document):
    chat_id: PydanticObjectId
    from_perspective: int
    raw_data: TelegramMessage | TelegramServiceMessage

    added_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @before_event(SaveChanges)
    def update_updated_at(self):
        self.updated_at = datetime.now()

    class Settings:
        indexes = [
            pymongo.IndexModel(
                [("chat_id", pymongo.ASCENDING)],
                name="chat_id_index_index_ascending",
            ),
            pymongo.IndexModel(
                [("from_perspective", pymongo.ASCENDING)],
                name="from_perspective_index_index_ascending",
            ),
            pymongo.IndexModel(
                [("raw_data.id", pymongo.ASCENDING)],
                name='raw_data_id_index_ascending'
            )
        ]
