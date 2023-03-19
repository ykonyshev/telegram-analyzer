import itertools
from pathlib import Path

import grpc.aio as grpc
import torch
from bson import ObjectId
from google.protobuf.empty_pb2 import Empty

from analysis.logging import get_logger
from processing.client.initialise_model import (
    DeviceType,
    initialise_appropriate_model,
)
from processing.client.TaskHandler import TaskHandler
from processing.proto.tasks_pb2 import Task
from processing.proto.tasks_pb2_grpc import TasksManagerStub

# TODO: https://github.com/aarnphm/whispercpp implement these models as well
# TODO: Implement providing a custom path to the model weights and not only the directory
# TODO: Handle possible errors, most notable the case when there are no tasks left
# TODO: Finish the current task on interrupt

logger = get_logger(__name__)


# TODO: More flexible API and custom options object.
async def run(
    server_address: str,
    preferred_model_name: str,
    device_type: DeviceType,
    threads_num: int,
    model_root: Path | None,
    tasks_limit: int | None
) -> None:
    if threads_num > 0:
        torch.set_num_threads(threads_num)

    init_result = initialise_appropriate_model(
        preferred_model_name,
        device_type,
        model_root
    )

    if init_result is None:
        logger.error('Was not able to initialise the model. Aborting.')
        return

    general_model_name, model = init_result

    if model is None:
        logger.error(f'Could not load model {preferred_model_name}')
        return

    async with grpc.insecure_channel(server_address) as channel:
        logger.info(f'Established connection with {server_address}')
        stub = TasksManagerStub(channel)

        number_iter = itertools.count() if tasks_limit is None else range(tasks_limit)
        for _ in number_iter:
            task: Task = await stub.GetTask(Empty())
            task_id = ObjectId(task.id)
            logger.info(f'Recieved a task {task_id = }, {task.remaining_count} more remaining')

            handler = TaskHandler(
                general_model_name,
                model,
                task
            )

            submit_request = await handler.handle()

            submit_response = await stub.SubmitTask(submit_request)
            logger.info(f'Submitted task {task_id = } with status {submit_response.ok = }')
