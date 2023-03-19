import argparse

from processing.client.cli import assign_arguments as assign_client_arguments
from processing.server.cli import assign_arguments as assign_server_arguments


def add_arguments(parser: argparse.ArgumentParser) -> None:
    processing_subparsers = parser.add_subparsers(
        dest='processing_action',
        help='Specify whether you want to start a tasks manager server or a processing node'
    )

    sp = processing_subparsers.add_parser(
        'server',
        help='Start tasks manager server'
    )

    cp = processing_subparsers.add_parser(
        'client',
        help='Start tasks processing node'
    )

    assign_server_arguments(sp)
    assign_client_arguments(cp)
