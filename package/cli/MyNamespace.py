import argparse
from pathlib import Path


class MyNamespace(argparse.Namespace):
    ids: list[int]
    graphs_output: Path
    generate_individual: bool
