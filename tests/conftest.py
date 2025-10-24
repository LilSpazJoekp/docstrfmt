"""Prepare py.test."""

import os
import shutil

import black
import pytest
import logging
from aiohttp import web
from click.testing import CliRunner

from docstrfmt import Manager
from docstrfmt.server import handler

log = logging.getLogger(__name__)


@pytest.fixture
async def client(aiohttp_client):
    app = web.Application()
    app.router.add_post("/", handler)
    return await aiohttp_client(app)


@pytest.fixture
def manager():
    yield Manager(current_file="<test_file>", black_config=black.Mode(), reporter=log)


@pytest.fixture
def runner():
    runner = CliRunner()
    files_to_copy = os.path.abspath("tests/test_files")
    with runner.isolated_filesystem() as temp_dir:
        shutil.copytree(files_to_copy, f"{temp_dir}/tests/test_files")
        yield runner
