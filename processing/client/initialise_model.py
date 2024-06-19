import os
from collections import OrderedDict
from pathlib import Path
from typing import Literal

import torch
import whisper

from analysis.logging import get_logger

logger = get_logger(__name__)

DeviceType = Literal['cuda', 'cpu'] 
DEFAULT_DEVICE_TYPE: DeviceType = 'cuda'
REQUIRED_MEMORY = OrderedDict({
    'medium': 6.5,
    'small': 3.5,
    'base': 3,
    'tiny': 3
})



def get_appropriate_params(
    preferred_model: str,
    explicit_device_type: DeviceType = DEFAULT_DEVICE_TYPE
) -> tuple[str, torch.device]:
    if not torch.cuda.is_available() or explicit_device_type == 'cpu':
        if explicit_device_type == 'gpu':
            logger.warn('You do not have any gpu devices, using cpu for inference')

        device = torch.device('cpu')
    else:
        # TODO: Maybe implement for multiple devices
        if torch.cuda.device_count() != 1:
            logger.warn('You have more than 1 cuda device. Mutiple devices have not yet been implemented')

        device = torch.device('cuda')

    available_memory = torch.cuda.mem_get_info(0)[0]
    available_gb = available_memory / 1024 ** 3

    model_name = preferred_model
    if preferred_model in REQUIRED_MEMORY and device.type == 'cuda':
        preferred_index = list(REQUIRED_MEMORY.keys()).index(preferred_model)
        for index, (name, required_mem) in enumerate(REQUIRED_MEMORY.items()):
            if required_mem < available_gb and preferred_index < index:
                model_name = name

                # TODO: More detailed reason as to which hardware exactly is not sufficient
                logger.warn(f'Model you specified {preferred_model = } can not be loaded due to hardware limitations. We are stepping down your model to {model_name = }')

                break

    return model_name, device


def setup_model(
    model_name: str,
    device: torch.device,
    model_root: Path | None = None,
) -> whisper.Whisper:
    if model_root is None:
        download_folder = os.path.join(os.path.expanduser("~"), ".cache")
    else:
        download_folder = str(model_root)

    logger.info(f'Loading {model_name = }')
    model = whisper.load_model(
        model_name,
        device=device,
        download_root=download_folder,
        in_memory=True
    )

    logger.info(f'Loaded and sent to {device = }!')
    return model


def initialise_appropriate_model(
    preferred_model_name: str,
    device_type: DeviceType,
    model_root: Path | None = None,
) -> tuple[str, whisper.Whisper] | None:
    if preferred_model_name not in whisper.available_models():
        logger.error(
            f'{preferred_model_name = } model is not available. Try a different one. \
                Available: {" ".join(whisper.available_models())}'
        )

        return

    model_name, device = get_appropriate_params(
        preferred_model_name,
        device_type
    )

    model = setup_model(
        model_name,
        device,
        model_root
    )

    general_model_name = f'whisper:{model_name}'
    return general_model_name, model
