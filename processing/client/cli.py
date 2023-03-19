import argparse
import typing
from pathlib import Path

from whisper import available_models

from processing.client.initialise_model import (
    DEFAULT_DEVICE_TYPE,
    DeviceType,
)
from processing.server import DEFAULT_SERVER_ADDRESS


class ClientNamespace(argparse.Namespace):
    model_name: str
    device_type: DeviceType
    threads: int
    tasks_limit: int | None
    model_root: Path | None


def assign_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--model-name',
        help='Model type which fill be used to extract text from audio',
        choices=available_models()
    )

    device_type_choices: list[DeviceType] = list(typing.get_args(DeviceType))
    parser.add_argument(
        '--tasks-limit',
        help='Limit to the number of tasks to process',
        type=int,
        default=None
    )

    parser.add_argument(
        '--device-type',
        help='Which device to use for iference',
        default=DEFAULT_DEVICE_TYPE,
        choices=device_type_choices
    )

    parser.add_argument(
        '--threads',
        help='Number of threads to let pytorch during inference',
        type=int,
        default=0
    )

    parser.add_argument(
        '--model-root',
        help='A folder where models will be downloaded',
        type=Path,
        default=None
    )

    parser.add_argument(
        '--server-address',
        help='Address of tasks server the client will connect to',
        default=DEFAULT_SERVER_ADDRESS
    )
