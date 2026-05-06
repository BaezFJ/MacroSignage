from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .app import create_app


def _add_server_options(
    parser: argparse.ArgumentParser,
    *,
    default_host: str,
    default_port: int,
) -> None:
    parser.add_argument("--host", default=default_host, help="Host interface to bind.")
    parser.add_argument("--port", default=default_port, type=int, help="Port to bind.")


def _run_dev(args: argparse.Namespace) -> int:
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def _run_prod(args: argparse.Namespace) -> int:
    from waitress import serve

    app = create_app({"MACROSIGNAGE_PRODUCTION": True})
    for warning in getattr(app, "config", {}).get("MACROSIGNAGE_CONFIG_WARNINGS", []):
        print(f"WARNING: {warning}", file=sys.stderr)
    serve(app, host=args.host, port=args.port, threads=args.threads)
    return 0


def _add_prod_options(parser: argparse.ArgumentParser) -> None:
    _add_server_options(parser, default_host="0.0.0.0", default_port=8080)
    parser.add_argument(
        "--threads",
        default=4,
        type=int,
        help="Number of Waitress worker threads.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="macrosignage",
        description="Run the MacroSignage web application.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dev_parser = subparsers.add_parser("dev", help="Run the Flask development server.")
    _add_server_options(dev_parser, default_host="127.0.0.1", default_port=5000)
    dev_parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable Flask debug mode.",
    )
    dev_parser.set_defaults(func=_run_dev)

    prod_parser = subparsers.add_parser("prod", help="Run with the Waitress WSGI server.")
    _add_prod_options(prod_parser)
    prod_parser.set_defaults(func=_run_prod)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def prod_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="macrosignage-prod",
        description="Run the MacroSignage web application with the Waitress WSGI server.",
    )
    _add_prod_options(parser)
    args = parser.parse_args(argv)
    return _run_prod(args)
