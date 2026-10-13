"""The docstrfmt server."""

import logging
import time

import click
from aiohttp import web
from docutils import utils

from . import DEFAULT_LINE_LENGTH, Manager, rst_extras

log = logging.getLogger(__name__)


async def handler(request: web.Request) -> web.Response:
    """Handle the incoming request.

    :param request: The incoming HTTP request.

    :returns: HTTP response with formatted content.

    """
    width = int(request.headers.get("X-Line-Length", DEFAULT_LINE_LENGTH))
    body = await request.text()

    start_time = time.perf_counter()
    manager = Manager(current_file="-", reporter=log)
    try:
        try:
            text = manager.format_node(
                width, manager.parse_string(body, file="<server_input>")
            )
            resp = web.Response(text=text)
        except utils.SystemMessage as error:  # pragma: no cover
            raise ParseError(str(error)) from None
    except ParseError as error:  # pragma: no cover
        logging.warning(f"Failed to parse input: {error}")
        resp = web.Response(reason=str(error), status=400)
    except Exception as error:  # pragma: no cover
        logging.exception("Error while handling request")
        resp = web.Response(reason=str(error), status=500)

    end_time = time.perf_counter()

    int(1000 * (end_time - start_time))
    return resp


rst_extras.register()


class ParseError(Exception):  # pragma: no cover
    """An error occurred while parsing the input."""


@click.command()
@click.option(
    "-h",
    "--bind-host",
    "bind_host",
    default="localhost",
    show_default=True,
    type=str,
)
@click.option(
    "-p",
    "--bind-port",
    "bind_port",
    default=5219,
    show_default=True,
    type=int,
)
def main(bind_host: str, bind_port: int) -> None:
    """Start the docstrfmt server.

    :param bind_host: Host to bind the server to.
    :param bind_port: Port to bind the server to.

    """
    app = web.Application()
    app.add_routes([web.post("/", handler)])
    web.run_app(app, host=bind_host, port=bind_port)
