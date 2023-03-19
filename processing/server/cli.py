import argparse

from processing.server import DEFAULT_SERVER_ADDRESS


class ServerNamespace(argparse.Namespace):
    grace_period: int
    address: str


def assign_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--grace-period',
        help='Server graceful shutdown duration',
        type=int,
        default=5
    )

    parser.add_argument(
        '--address',
        help='Address on which gRPC server will accept connections from processing nodes',
        default=DEFAULT_SERVER_ADDRESS
    )
