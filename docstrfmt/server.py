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
    manager = Manager(current_file="-", black_config=None, reporter=log)
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
        resp = web.Response(status=400, reason=str(error))
    except Exception as error:  # pragma: no cover
        logging.exception("Error while handling request")
        resp = web.Response(status=500, reason=str(error))

    end_time = time.perf_counter()

    int(1000 * (end_time - start_time))
    return resp


rst_extras.register()


@click.command()
@click.option(
    "-h",
    "--bind-host",
    "bind_host",
    type=str,
    default="localhost",
    show_default=True,
)
@click.option(
    "-p",
    "--bind-port",
    "bind_port",
    type=int,
    default=5219,
    show_default=True,
)
def main(bind_host: str, bind_port: int) -> None:
    """Start the docstrfmt server.

    :param bind_host: Host to bind the server to.
    :param bind_port: Port to bind the server to.

    """
    app = web.Application()
    app.add_routes([web.post("/", handler)])
    web.run_app(app, host=bind_host, port=bind_port)


class ParseError(Exception):  # pragma: no cover
    """An error occurred while parsing the input."""
