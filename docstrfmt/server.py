"""The docstrfmt server."""

import logging
import time

import click
from aiohttp import web
from docutils import utils

from . import DEFAULT_LINE_LENGTH, Manager, rst_extras
from .exceptions import InvalidRstErrors

log = logging.getLogger(__name__)


async def handler(request: web.Request) -> web.Response:
    """Handle the incoming request.

    :param request: The incoming HTTP request.

    :returns: HTTP response with formatted content, or with the error message when the
        request could not be handled.

    """
    line_length = request.headers.get("X-Line-Length", DEFAULT_LINE_LENGTH)
    try:
        width = int(line_length)
    except ValueError:
        return web.Response(
            status=400,
            text=f"Invalid X-Line-Length header: {line_length!r} is not an integer.",
        )
    body = await request.text()

    start_time = time.perf_counter()
    manager = Manager(black_config=None, current_file="-", reporter=log)
    try:
        text = manager.format_node(
            width, manager.parse_string(body, file="<server_input>")
        )
        resp = web.Response(text=text)
    except (InvalidRstErrors, utils.SystemMessage) as error:
        logging.warning(f"Failed to parse input: {error}")
        resp = web.Response(status=400, text=str(error))
    except Exception as error:
        logging.exception("Error while handling request")
        resp = web.Response(status=500, text=str(error))

    end_time = time.perf_counter()

    int(1000 * (end_time - start_time))
    return resp


@click.command()
@click.option(
    "-h",
    "--bind-host",
    "bind_host",
    default="localhost",
    help="Host interface to bind the daemon to.",
    show_default=True,
    type=str,
)
@click.option(
    "-p",
    "--bind-port",
    "bind_port",
    default=5219,
    help="TCP port to listen on.",
    show_default=True,
    type=int,
)
def main(bind_host: str, bind_port: int) -> None:
    """Start the docstrfmt server."""
    rst_extras.register()
    app = web.Application()
    app.add_routes([web.post("/", handler)])
    web.run_app(app, host=bind_host, port=bind_port)
