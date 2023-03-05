from datetime import datetime
from enum import Enum
from typing import Optional

import pymongo
from beanie import (
    Document,
    Insert,
    PydanticObjectId,
    SaveChanges,
    before_event,
)
from pydantic import BaseModel, Field

from package.logging import get_logger
from package.models.Message.MediaDetails import AudioDetails, MediaDetails
from package.models.Message.MessageMedia import MessageMedia
from package.models.Message.Peer import Peer

logger = get_logger(__name__)

EXCLUDE_CHARS = '.,!?/\\()"\'-—+-=%^&$#@*_\n<>'
EXCLUDE = str.maketrans({
    char: None for char in list(EXCLUDE_CHARS)
})


class ForwardInfo(BaseModel):
    date: datetime
    imported: bool | None
    from_id: Peer | None
    from_name: str | None
    channel_post: int | None
    post_author: str | None
    saved_from_peer: Peer | None
    saved_from_msg_id: int | None


class ReplyInfo(BaseModel):
    reply_to_msg_id: int
    reply_to_peer_id: Peer | None
    # forum_topic: None
    reply_to_top_id: int | None


class Replies(BaseModel):
    comments: bool | None
    replies: int
    replies_pts: int
    recent_repliers: list[Peer] | None
    channel_id: int | None
    max_id: int | None
    read_max_id: int | None


class Reaction(BaseModel):
    emoticon: str


class ReactionCount(BaseModel):
    count: int
    reaction: Reaction
    chosen_order: int | None


class PeerReaction(BaseModel):
    peer_id: Peer
    reaction: Reaction
    big: bool | None
    unread: bool | None


class Reactions(BaseModel):
    min: bool
    can_see_list: bool
    results: Optional[list[ReactionCount]]
    recent_reactions: Optional[list[PeerReaction]]


class BaseTelegramMessage(BaseModel):
    id: int
    peer_id: Optional[Peer]
    from_id: Optional[Peer]
    reply_to: Optional[ReplyInfo]
    date: datetime | None
    mentioned: bool | None
    out: bool | None
    media_unread: bool | None
    post: bool | None
    legacy: bool | None
    ttl_period: int | None


# TODO: Implement me for effecting messages hashing
# class TelegramServiceMessage(BaseTelegramMessage):
#     action: MessageAction
#     ...


class TelegramMessage(BaseTelegramMessage):
    message: str
    fwd_from: ForwardInfo | None = None
    reactions: Optional[Reactions]
    edit_date: datetime | None
    silent: bool | None
    from_scheduled: bool | None
    edit_hide: bool | None
    pinned: bool | None
    noforwards: bool | None
    via_bot_id: int | None
    media: MessageMedia | None
    # TODO: Implement entities
    # entities: None
    views: int | None
    forwards: int | None
    replies: Replies | None
    post_author: str | None
    grouped_id: int | None
    # restricition_reason: None


class MessageType(str, Enum):
    photo = 'photo'
    audio = 'audio'
    plain_text = 'plain_text'
    other = 'other'


class Message(Document):
    tg_id: int
    chat_id: PydanticObjectId
    from_perspective: int
    raw_data: TelegramMessage

    words: list[str] = Field(default_factory=list)
    message_type: MessageType = MessageType.plain_text
    media_details: MediaDetails | None

    added_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


    # TODO: Check if needed fields where modified and only then run the operation
    @before_event(SaveChanges, Insert)
    def update_words(self):
        self.words = self.parse_words()


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
                [("tg_id", pymongo.ASCENDING)],
                name='tg_id_index_ascending'
            )
        ]


    @property
    def text(self) -> str | None:
        if len(self.raw_data.message) == 0 or (
            self.message_type == MessageType.audio \
                and self.media_details is None
        ):
            return

        if self.message_type == MessageType.plain_text:
            return self.raw_data.message

        if self.media_details is None:
            return

        text_parts = []
        for detail in self.media_details:
            if not isinstance(detail, AudioDetails) \
                or detail.text_contents is None:
                continue

            text_parts.append(detail.text_contents.text)

        return ' '.join(text_parts)


    def parse_words(self) -> list[str]:
        text = self.text
        if text is None:
            return []

        clean = text.lower().translate(EXCLUDE).strip()
        if len(clean) <= 0:
            return []

        stripped = map(str.strip, clean.split(' '))
        return [word for word in stripped if len(word) > 0]
