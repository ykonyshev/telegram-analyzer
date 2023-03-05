from pydantic import BaseModel


class PeerChannel(BaseModel):
    channel_id: int


class PeerUser(BaseModel):
    user_id: int


class PeerChat(BaseModel):
    chat_id: int


Peer = PeerUser | PeerChat | PeerChannel
