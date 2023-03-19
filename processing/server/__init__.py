import grpc.aio as grpc

from analysis.logging import get_logger
from processing.proto.tasks_pb2_grpc import (
    add_TasksManagerServicer_to_server,
)
from processing.server.servicers.TasksManager import TasksManagerServicer

logger = get_logger(__name__)
DEFAULT_SERVER_ADDRESS = '[::]:50051'


# TODO: Account for cases where the client has disconnected before completing the task
# TODO: Send remaining task count and approximate duration
# TODO: Processing nodes authentication
# TODO: Implement __main__.py so the module can be run a standalone

# & Later
# TODO: Redis backend for storing tasks, maybe there are some additional advantages to using redis apart from low latancy, which is not that much of a consideration as if right now. Purely for fun, but it may compilcate the overall stack and increase time needed, which is not really preferred.


async def serve(
    address: str = DEFAULT_SERVER_ADDRESS
) -> grpc.Server:
    server = grpc.server()

    instance = TasksManagerServicer()
    add_TasksManagerServicer_to_server(instance, server)

    # TODO: An option for secure and insecure ports.. Look into it
    server.add_insecure_port(address)
    await server.start()

    logger.info(f'Started server on {address}')

    return server
