import argparse

from analysis.cli import add_arguments as add_report_arguments
from cli.MyNamespace import MyNamespace
from processing.cli import add_arguments as add_processing_arguments


def get_args() -> MyNamespace:
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = ap.add_subparsers(
        help='Chose whether to form a report or do additional data processing in a \
            dirtributed manner',
        dest='action'
    )

    pp = subparsers.add_parser(
        'processing',
        help='Start a server or a client to additionally run computationly taxing \
            tasks in a distributed manner'
    )

    rp = subparsers.add_parser(
        'report',
        help='Get information from telegram and form a report'
    )

    add_processing_arguments(pp)
    add_report_arguments(rp)

    nsp = MyNamespace()
    args = ap.parse_args(namespace=nsp)

    return args
