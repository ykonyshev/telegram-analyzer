import argparse
from pathlib import Path


class MyNamespace(argparse.Namespace):
    ids: list[int]
    skip_gather: bool
    gather_limit: int
    media_folder: Path
    graphs_output: Path
    generate_individual: bool
