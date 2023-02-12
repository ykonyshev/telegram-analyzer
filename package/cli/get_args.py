import argparse
from pathlib import Path

from package.cli.MyNamespace import MyNamespace


def get_args() -> MyNamespace:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        'ids',
        nargs='*',
        type=int,
        help="User IDs to generate reports for."
    )

    ap.add_argument(
        '--graphs-output',
        default=Path('./graphs'),
        type=Path,
        help='The derictory where result graphs will be saved'
    )

    ap.add_argument(
        '--generate-individual',
        action='store_true',
        default=False,
        help='Whether a report should be generated for every user or just for all of them'
    )

    nsp = MyNamespace()
    args = ap.parse_args(namespace=nsp)

    return args
