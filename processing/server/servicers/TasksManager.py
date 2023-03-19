import asyncio

import aiofiles
import grpc.aio as grpc
from beanie import PydanticObjectId
from beanie.operators import ElemMatch, NotIn
from bson import ObjectId
from google.protobuf.empty_pb2 import Empty
from grpc import StatusCode

from analysis.models.Chat import Chat
from analysis.models.Message import Message, MessageType
from analysis.models.Message.MediaDetails.AudioDetails import (
    AudioContents,
    AudioDetails,
    FileHandle,
)
from analysis.models.Task import Task
from processing.proto.tasks_pb2 import (
    SubmitTaskRequest,
    SubmitTaskResponse,
)
from processing.proto.tasks_pb2 import Task as ResponseTask
from processing.proto.tasks_pb2_grpc import (
    TasksManagerServicer as BaseTasksManagerServicer,
)


async def open_file(
    details: ResponseTask.AudioDetails,
    file_handle: FileHandle
) -> ResponseTask.AudioDetails:
    async with aiofiles.open(file_handle.path, 'rb') as handle:
        details.file_contents = await handle.read()

    return details


class TasksManagerServicer(BaseTasksManagerServicer):
    async def GetTask(
        self,
        _: Empty,
        context: grpc.ServicerContext[Empty, ResponseTask]
    ) -> ResponseTask | None:
        present_tasks_message_ids: list[ObjectId] = await Task.distinct(
            'message_id'
        )

        try:
            chats_with_no_languages: list[ObjectId] = await Chat.distinct(
                'id',
                {
                    'spoken_languages': {
                        "$ne": { '$size': 0 } 
                    },
                    'spoken_languages': { # noqa: F601
                        '$ne': None,
                    }
                }
            )
        except Exception as error:
            print(error)
            return

        find_query = Message.find(
            Message.message_type == MessageType.audio,
            NotIn(Message.id, present_tasks_message_ids),
            NotIn(Message.chat_id, chats_with_no_languages),

            # TODO: A better way to check if this message has already been processed
            ElemMatch(Message.media_details, {
                'text_contents': {
                    "$exists": True,
                    "$eq": None
                }
            })
        )

        found_count = await find_query.count()
        message = await find_query.first_or_none()

        if message is None or message.id is None or message.media_details is None:
            return await context.abort(
                StatusCode.NOT_FOUND,
                "No more messages to process."
            )

        chat = await Chat.find_one(
            Chat.id == message.chat_id
        )

        if chat is None:
            return await context.abort(
                StatusCode.NOT_FOUND,
                'Was not able to find chat associated with the task message.'
            )

        open_tasks: list[asyncio.Task[ResponseTask.AudioDetails]] = []
        for detail in message.media_details:
            if not isinstance(detail, AudioDetails) \
                or detail.file_handle is None \
                or not detail.file_handle.is_downloaded:
                continue

            open_task = asyncio.Task(
                open_file(
                    ResponseTask.AudioDetails(
                        document_id=detail.file_handle.document_id,
                        # TODO: Provide more percise audio duration
                        duration=detail.duration
                    ),
                    detail.file_handle
                )
            )

            open_tasks.append(open_task)

        if chat.spoken_languages is None or len(chat.spoken_languages) <= 0:
            return await context.abort(
                StatusCode.INTERNAL,
                'Chat associated with the task message is invalid, \
                    no spoken languages were found'
            )

        task = await Task(
            message_id=message.id
        ).save()

        if task.id is None:
            await Task.delete(task)
            return await context.abort(
                StatusCode.INTERNAL,
                "An error creating a task occured"
            )

        await asyncio.wait(open_tasks)
        response_task = ResponseTask(
            id=task.id.binary,
            audio_files=await asyncio.gather(*open_tasks),
            
            # TODO: Handle this a little bit differently, maybe the audio spoken not in the most common language
            audio_language=chat.spoken_languages[0],
            remaining_count=found_count - 1
        )

        return response_task


    async def SubmitTask(
        self,
        request: SubmitTaskRequest,
        context: grpc.ServicerContext
    ) -> SubmitTaskResponse | None:
        predicate = await Task.find_one(
            Task.id == PydanticObjectId(request.task_id)
        )

        if predicate is None:
            return await context.abort(
                StatusCode.NOT_FOUND,
                'Task with this id was not found'
            )

        message_predicate = await Message.find_one(
            Message.id == predicate.message_id
        )

        if message_predicate is None \
            or message_predicate.media_details is None:
            return await context.abort(
                StatusCode.NOT_FOUND,
                'Message associated with the tasks was not found'
            )

        document_id_mapping = {item.document_id: item for item in request.details}
        for detail in message_predicate.media_details:
            if not isinstance(detail, AudioDetails) or detail.file_handle is None:
                continue

            needed = document_id_mapping.get(detail.file_handle.document_id)
            if needed is None:
                return await context.abort(
                    StatusCode.NOT_FOUND,
                    'document ids associated with audio files provided do not align with local data'
                )

            detail.text_contents = AudioContents(
                text=needed.text,
                language=needed.language,
                model_used=request.model_used
            )

        await message_predicate.save()
        await Task.delete(predicate)

        return SubmitTaskResponse(
            ok=True
        )
