from datetime import datetime

import telethon.types as tg_types
from pydantic import BaseModel

from analysis.models.Message.DocumentAttribute import DocumentAttribute

SupportedMedia = tg_types.MessageMediaPhoto | tg_types.MessageMediaDocument

class BasePhotoSize(BaseModel):
    type: str

class BaseMediaSizeWithDims(BasePhotoSize):
    w: int
    h: int


PhotoSizeEmpty = BasePhotoSize

class PhotoSize(BaseMediaSizeWithDims):
    size: int


class PhotoCachedSize(BaseMediaSizeWithDims):
    bytes: bytes


class PhotoStrippedSize(BasePhotoSize):
    bytes: str


class PhotoSizeProgressive(BaseMediaSizeWithDims):
    sizes: list[int]


class PhotoPathSize(BasePhotoSize):
    bytes: bytes


SupportedPhotoSizes = \
    PhotoSize | \
    PhotoSizeEmpty | \
    PhotoCachedSize | \
    PhotoStrippedSize | \
    PhotoSizeProgressive | \
    PhotoPathSize \


class VideoSize(BaseMediaSizeWithDims):
    size: int
    video_start_ts: int | None


class Photo(BaseModel):
    id: int
    dc_id: int
    has_stickers: bool | None
    access_hash: int
    file_reference: bytes
    date: datetime
    sizes: list[SupportedPhotoSizes]
    video_sizes: list[VideoSize] | None


class MessageMediaPhoto(BaseModel):
    photo: Photo | None
    ttl_seconds: int | None


class Document(BaseModel):
    id: int
    dc_id: int
    access_hash: int
    file_reference: bytes
    date: datetime
    mime_type: str
    size: int
    attributes: list[DocumentAttribute]
    thumbs: list[PhotoSize] | None
    video_thubs: list[VideoSize] | None


class MessageMediaDocument(BaseModel):
    nopremiun: bool | None
    document: Document | None
    ttl_seconds: float | None

MessageMedia = MessageMediaDocument | MessageMediaPhoto
