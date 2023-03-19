from pathlib import Path
from typing import Literal

from processing.client.cli import ClientNamespace
from processing.server.cli import ServerNamespace


class MyNamespace(ClientNamespace, ServerNamespace):
    action: Literal['report', 'processing']
    processing_action: Literal['server', 'client']

    # * report arguments
    ids: list[int]
    skip_gather: bool
    gather_limit: int
    media_folder: Path
    graphs_output: Path
    generate_individual: bool
