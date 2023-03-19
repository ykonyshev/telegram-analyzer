import argparse
from pathlib import Path


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'ids',
        nargs='+',
        type=int,
        help="User IDs to generate reports for."
    )

    parser.add_argument(
        '--skip-gather',
        action='store_true',
        default=False,
        help='Skip the data collection process and go off the already present data'
    )

    parser.add_argument(
        '--gather-limit',
        type=int,
        default=None,
        help='A limit to the number of messages, the script will process'
    )

    parser.add_argument(
        '--media-folder',
        default=Path('./media'),
        type=Path,
        help='A derictory where the media data will be stored'
    )

    parser.add_argument(
        '--graphs-output',
        default=Path('./graphs'),
        type=Path,
        help='The derictory where result graphs will be saved'
    )

    parser.add_argument(
        '--generate-individual',
        action='store_true',
        default=False,
        help='Whether a report should be generated for every user or just for all of them'
    )
