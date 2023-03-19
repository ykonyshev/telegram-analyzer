from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SubmitTaskRequest(_message.Message):
    __slots__ = ["details", "model_used", "task_id"]
    class AudioContents(_message.Message):
        __slots__ = ["document_id", "language", "text"]
        DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
        LANGUAGE_FIELD_NUMBER: _ClassVar[int]
        TEXT_FIELD_NUMBER: _ClassVar[int]
        document_id: int
        language: str
        text: str
        def __init__(self, document_id: _Optional[int] = ..., language: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    MODEL_USED_FIELD_NUMBER: _ClassVar[int]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    details: _containers.RepeatedCompositeFieldContainer[SubmitTaskRequest.AudioContents]
    model_used: str
    task_id: bytes
    def __init__(self, task_id: _Optional[bytes] = ..., model_used: _Optional[str] = ..., details: _Optional[_Iterable[_Union[SubmitTaskRequest.AudioContents, _Mapping]]] = ...) -> None: ...

class SubmitTaskResponse(_message.Message):
    __slots__ = ["ok"]
    OK_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    def __init__(self, ok: bool = ...) -> None: ...

class Task(_message.Message):
    __slots__ = ["audio_files", "audio_language", "id", "remaining_count"]
    class AudioDetails(_message.Message):
        __slots__ = ["document_id", "duration", "file_contents"]
        DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
        DURATION_FIELD_NUMBER: _ClassVar[int]
        FILE_CONTENTS_FIELD_NUMBER: _ClassVar[int]
        document_id: int
        duration: int
        file_contents: bytes
        def __init__(self, file_contents: _Optional[bytes] = ..., document_id: _Optional[int] = ..., duration: _Optional[int] = ...) -> None: ...
    AUDIO_FILES_FIELD_NUMBER: _ClassVar[int]
    AUDIO_LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    REMAINING_COUNT_FIELD_NUMBER: _ClassVar[int]
    audio_files: _containers.RepeatedCompositeFieldContainer[Task.AudioDetails]
    audio_language: str
    id: bytes
    remaining_count: int
    def __init__(self, id: _Optional[bytes] = ..., audio_language: _Optional[str] = ..., audio_files: _Optional[_Iterable[_Union[Task.AudioDetails, _Mapping]]] = ..., remaining_count: _Optional[int] = ...) -> None: ...
