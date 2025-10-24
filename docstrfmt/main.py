"""Main entrypoint for docstrfmt."""

from __future__ import annotations

import asyncio
import glob
import itertools
import logging
import os
import signal
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import nullcontext
from copy import copy
from functools import partial
from multiprocessing import Manager as MultiManager
from multiprocessing import freeze_support
from os.path import abspath
from pathlib import Path
from textwrap import dedent, indent
from typing import TYPE_CHECKING, Any

import click
import libcst as cst

# noinspection PyUnreachableCode
if sys.version_info >= (3, 11):
    import tomllib as toml  # pragma: no cover
else:
    import tomli as toml  # pragma: no cover
from black import (
    DEFAULT_LINE_LENGTH,
    Mode,
    TargetVersion,
    find_pyproject_toml,
    parse_pyproject_toml,
)
from click import Context
from libcst import CSTTransformer, Expr
from libcst.metadata import ParentNodeProvider, PositionProvider

from . import DEFAULT_EXCLUDE, SECTION_CHARS, Manager, __version__
from .debug import dump_node
from .exceptions import InvalidRstErrors
from .util import FileCache, LineResolver, plural

if TYPE_CHECKING:
    from collections.abc import Iterable
    from contextlib import AbstractContextManager
    from threading import Lock

    from libcst import AssignTarget, ClassDef, FunctionDef, Module, SimpleString

echo = partial(click.secho, err=True)


def _format_file(
    check: bool,
    file: Path,
    file_type: str,
    include_txt: bool,
    line_length: int,
    mode: Mode,
    docstring_trailing_line: bool,
    format_python_code_blocks: bool,
    section_adornments: list[tuple[str, bool]] | None,
    raw_output: bool,
    lock: Lock | None,
):
    """Format a single file with the given parameters.

    :param check: Whether to check formatting without modifying files.
    :param file: Path to the file to format.
    :param file_type: Type of file ('py' or 'rst').
    :param include_txt: Whether to include .txt files.
    :param line_length: Maximum line length.
    :param mode: Black formatting mode.
    :param docstring_trailing_line: Whether to add trailing line to docstrings.
    :param format_python_code_blocks: Whether to format Python code blocks.
    :param section_adornments: Section adornment configuration.
    :param raw_output: Whether to output raw formatted text.
    :param lock: Lock for thread safety.

    :returns: A tuple containing a boolean indicating if the file was misformatted and
        the number of errors.

    """
    error_count = 0
    manager = Manager(
        current_file=file.name,
        black_config=mode,
        docstring_trailing_line=docstring_trailing_line,
        format_python_code_blocks=format_python_code_blocks,
        reporter=reporter,
        section_adornments=section_adornments,
    )
    if file.name == "-":
        raw_output = True
    reporter.print(f"Checking {file}", 2)
    misformatted = False
    with (
        nullcontext(sys.stdin) if file.name == "-" else open(file, encoding="utf-8")
    ) as f:
        input_string = f.read()
        newline = getattr(f, "newlines", None)
        # If mixed or unknown newlines, fall back to the platform default
        if not isinstance(newline, str):  # pragma: no cover
            newline = None
    try:
        if file.suffix == ".py" or (file_type == "py" and file.name == "-"):
            misformatted, errors = _process_python(
                check,
                file,
                input_string,
                line_length,
                manager,
                raw_output,
                lock,
                newline,
            )
            error_count += errors
        elif (
            file.suffix in ([".rst", ".txt"] if include_txt else [".rst"])
            or file.name == "-"
        ):
            misformatted, errors = _process_rst(
                check,
                file,
                input_string,
                line_length,
                manager,
                raw_output,
                lock,
                newline,
            )
            error_count += errors
    except InvalidRstErrors as errors:
        reporter.error(str(errors))
        error_count += 1
        reporter.print(f"Failed to format '{str(file)}'")
    except Exception as error:  # noqa: BLE001
        reporter.error(f"{error.__class__.__name__}: {error}")
        error_count += 1
        reporter.print(f"Failed to format '{str(file)}'")
    return misformatted, error_count


def _parse_pyproject_config(
    context: click.Context, _: click.Parameter, value: str | None
) -> Mode:
    """Parse pyproject.toml configuration for docstrfmt and black.

    :param context: Click context containing command parameters.
    :param _: Unused parameter.
    :param value: Path to pyproject.toml file.

    :returns: Black Mode configuration object.

    :raises click.FileError: If the configuration file cannot be read.
    :raises click.BadOptionUsage: If configuration values are invalid.

    """
    if not value:
        pyproject_toml = find_pyproject_toml(tuple(context.params.get("files", (".",))))
        value = pyproject_toml if pyproject_toml else None
    if value:
        try:
            with open(value, "rb") as f:
                pyproject_toml = toml.load(f)
            config = pyproject_toml.get("tool", {}).get("docstrfmt", {})
            config = {
                k.replace("--", "").replace("-", "_"): v for k, v in config.items()
            }
        except (OSError, ValueError) as e:  # pragma: no cover
            raise click.FileError(
                filename=value, hint=f"Error reading configuration file: {e}"
            ) from None

        if config:
            for key in ["exclude", "extend_exclude", "files"]:
                config_value = config.get(key)
                if config_value is not None and not isinstance(config_value, list):
                    raise click.BadOptionUsage(key, f"Config key {key} must be a list")
            params = {}
            if context.default_map is not None:  # pragma: no cover
                params.update(context.default_map)
            if context.params is not None:
                params.update(context.params)
            params.update(config)
            context.params = params
            context.default_map = params

        black_config = parse_pyproject_toml(value)
        black_config.pop("exclude", None)
        black_config.pop("extend_exclude", None)
        target_version = black_config.pop("target_version", ["PY37"])
        if target_version:
            target_version = {
                getattr(TargetVersion, version.upper())
                for version in target_version
                if hasattr(TargetVersion, version.upper())
            }
        black_config["target_versions"] = target_version
        return Mode(**black_config)
    return Mode()


def _parse_sources(context: click.Context, _: click.Parameter, value: list[str] | None):
    """Parse and expand source files from command line arguments.

    :param context: Click context containing command parameters.
    :param _: Unused parameter.
    :param value: List of source files/directories from command line.

    :returns: List of resolved file paths to format.

    """
    sources = value or context.params.get("files", [])
    exclude = list(context.params.get("exclude", DEFAULT_EXCLUDE))
    extend_exclude = list(context.params.get("extend_exclude", []))
    exclude.extend(extend_exclude)
    include_txt = context.params.get("include_txt", False)
    files_to_format = set()
    extensions = [".py", ".rst"] + ([".txt"] if include_txt else [])
    for source in sources:
        if source == "-":
            files_to_format.add(source)
        else:
            for item in map(Path, glob.iglob(source, recursive=True)):
                if item.is_dir():
                    for f in [
                        found
                        for extension in extensions
                        for found in glob.iglob(
                            f"{item}/**/*{extension}", recursive=True
                        )
                    ]:
                        files_to_format.add(abspath(f))
                else:
                    files_to_format.add(abspath(item))
    for file in list(map(Path, files_to_format)):
        for exclusion in exclude:
            if file.parent.match(exclusion) or file.match(exclusion):
                files_to_format.discard(abspath(file))
                break
    sorted_files = sorted(files_to_format)
    if context.params.get("files", []):
        context.params["files"] = sorted_files
    return sorted_files


def _process_python(
    check: bool,
    file: Path | str,
    input_string: str,
    line_length: int,
    manager: Manager,
    raw_output: bool,
    lock: Lock | None = None,
    newline: str | None = None,
):
    """Process a Python file for docstring formatting.

    :param check: Whether to check formatting without modifying files.
    :param file: Path to the file to process.
    :param input_string: Content of the file to process.
    :param line_length: Maximum line length.
    :param manager: Manager instance for formatting.
    :param raw_output: Whether to output raw formatted text.
    :param lock: Lock for thread safety.
    :param newline: Newline character to use.

    :returns: A tuple containing a boolean indicating if the file was misformatted and
        the number of errors.

    """
    if isinstance(file, str):
        file = Path(file)
    filename = file.name
    object_name = filename.split(".")[0]
    visitor = Visitor(file, input_string, line_length, manager, object_name)
    module = cst.parse_module(input_string)
    wrapper = cst.MetadataWrapper(module)
    result = wrapper.visit(visitor)
    error_count = visitor.error_count
    misformatted = False
    if visitor.misformatted:
        misformatted = True
        if check and not raw_output:
            reporter.print(f"File '{str(file)}' could be reformatted.")
        elif file == "-" or raw_output:
            with lock or nullcontext():
                _write_output(file, result.code, nullcontext(sys.stdout), raw_output)
        else:
            _write_output(
                file,
                result.code,
                file.open("w", encoding="utf-8", newline=newline),  # noqa: SIM115
                raw_output,
            )
    elif raw_output:
        with lock or nullcontext():
            _write_output(file, input_string, nullcontext(sys.stdout), raw_output)
    return misformatted, error_count


def _process_rst(
    check: bool,
    file: Path | str,
    input_string: str,
    line_length: int,
    manager: Manager,
    raw_output: bool,
    lock: Lock | None = None,
    newline: str | None = None,
):
    """Process a reStructuredText file for formatting.

    :param check: Whether to check formatting without modifying files.
    :param file: Path to the file to process.
    :param input_string: Content of the file to process.
    :param line_length: Maximum line length.
    :param manager: Manager instance for formatting.
    :param raw_output: Whether to output raw formatted text.
    :param lock: Lock for thread safety.
    :param newline: Newline character to use.

    :returns: A tuple containing a boolean indicating if the file was misformatted and
        the number of errors.

    """
    doc = manager.parse_string(input_string, file=file)
    if reporter.level >= 3:
        reporter.debug("=" * 60)
        reporter.debug(dump_node(doc))
    output = manager.format_node(line_length, doc)
    error_count = manager.error_count
    misformatted = False
    if output == input_string:
        reporter.print(f"File '{str(file)}' is formatted correctly. Nice!", 1)
        if raw_output:
            with lock or nullcontext():
                _write_output(file, input_string, nullcontext(sys.stdout), raw_output)
    else:
        misformatted = True
        if check and not raw_output:
            reporter.print(f"File '{str(file)}' could be reformatted.")
        elif file == "-" or raw_output:
            with lock or nullcontext():
                _write_output(file, output, nullcontext(sys.stdout), raw_output)
        else:
            assert isinstance(file, Path)
            _write_output(
                file,
                output,
                file.open("w", encoding="utf-8", newline=newline),  # noqa: SIM115
                raw_output,
            )
    return misformatted, error_count


def _resolve_length(context: click.Context, _: click.Parameter, value: int | None):
    """Resolve line length from command line or pyproject.toml.

    :param context: Click context containing command parameters.
    :param _: Unused parameter.
    :param value: Line length from command line.

    :returns: Resolved line length value.

    """
    pyproject_line_length = context.params.pop("line_length", None)
    return value or pyproject_line_length


def _validate_adornments(
    context: click.Context, _: click.Parameter, value: str | None
) -> list[tuple[str, bool]] | None:
    """Validate and parse section adornments configuration.

    :param context: Click context containing command parameters.
    :param _: Unused parameter.
    :param value: Section adornments string from command line.

    :returns: List of tuples containing (character, has_overline) for each adornment.

    :raises click.BadParameter: If adornments are not unique.

    """
    actual_value = value or context.params["section_adornments"]

    if len(actual_value) != len(set(actual_value)):
        msg = "Section adornments must be unique"
        raise click.BadParameter(msg)

    if "|" in actual_value:
        with_overline, without_overline = actual_value.split("|", 1)
        return list(zip(with_overline, itertools.repeat(True))) + list(
            zip(without_overline, itertools.repeat(False))
        )

    return list(zip(actual_value, itertools.repeat(False)))


async def _run_formatter(
    check: bool,
    file_type: str,
    files: list[str],
    include_txt: bool,
    docstring_trailing_line: bool,
    format_python_code_blocks: bool,
    section_adornments: list[tuple[str, bool]] | None,
    mode: Mode,
    line_length: int,
    raw_output: bool,
    cache: FileCache,
    loop: asyncio.AbstractEventLoop,
    executor: ProcessPoolExecutor | ThreadPoolExecutor,
):
    """Run the formatter on multiple files asynchronously.

    :param check: Whether to check formatting without modifying files.
    :param file_type: Type of files to process ('py' or 'rst').
    :param files: List of file paths to format.
    :param include_txt: Whether to include .txt files.
    :param docstring_trailing_line: Whether to add trailing line to docstrings.
    :param format_python_code_blocks: Whether to format Python code blocks.
    :param section_adornments: Section adornment configuration.
    :param mode: Black formatting mode.
    :param line_length: Maximum line length.
    :param raw_output: Whether to output raw formatted text.
    :param cache: File cache for tracking changes.
    :param loop: Event loop for async operations.
    :param executor: Process or thread pool executor.

    :returns: Tuple of (misformatted_files, total_error_count).

    """
    # This code is heavily based on that of psf/black
    # see here for license: https://github.com/psf/black/blob/master/LICENSE
    todo, already_done = cache.gen_todo_list(files)
    cancelled = []
    files_to_cache = []
    lock = MultiManager().Lock()
    misformatted_files = set()
    tasks = {
        asyncio.ensure_future(
            loop.run_in_executor(
                executor,
                _format_file,
                check,
                file,
                file_type,
                include_txt,
                line_length,
                mode,
                docstring_trailing_line,
                format_python_code_blocks,
                section_adornments,
                raw_output,
                lock,
            )
        ): file
        for file in sorted(todo)
    }
    in_process = tasks.keys()
    try:  # pragma: no cover
        loop.add_signal_handler(signal.SIGINT, cancel, in_process)
        loop.add_signal_handler(signal.SIGTERM, cancel, in_process)
    except NotImplementedError:  # pragma: no cover
        # There are no good alternatives for these on Windows.
        pass
    error_count = 0
    while in_process:
        done, _ = await asyncio.wait(in_process, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            file = tasks.pop(task)
            if task.cancelled():  # pragma: no cover
                cancelled.append(task)
            elif task.exception():  # pragma: no cover
                reporter.error(str(task.exception()))
                error_count += 1
            else:
                misformatted, errors = task.result()
                sys.stderr.flush()
                error_count += errors
                if misformatted:
                    misformatted_files.add(file)
                if (
                    not (misformatted and raw_output) or (check and not misformatted)
                ) and errors == 0:
                    files_to_cache.append(file)
    if cancelled:  # pragma: no cover
        await asyncio.gather(*cancelled, return_exceptions=True)
    if files_to_cache:
        cache.write_cache(files_to_cache)
    return misformatted_files, error_count


def _write_output(
    file: Path | str,
    output: str,
    output_manager: AbstractContextManager,
    raw: bool,
):
    """Write formatted output to a file or stdout.

    :param file: Path to the file being processed.
    :param output: Formatted content to write.
    :param output_manager: Context manager for output destination.
    :param raw: Whether this is raw output mode.

    """
    with output_manager as f:
        f.write(output)
    if not raw:
        reporter.print(f"Reformatted '{str(file)}'.")


# This code is borrowed from psf/black
# see here for license: https://github.com/psf/black/blob/master/LICENSE
def cancel(tasks: Iterable[asyncio.Future[Any]]) -> None:  # pragma: no cover
    """Asyncio signal handler that cancels all `tasks` and reports to stderr.

    :param tasks: Iterable of asyncio tasks to cancel.

    """
    reporter.error("Aborted!")
    for task in tasks:
        task.cancel()


def shutdown(loop: asyncio.AbstractEventLoop) -> None:  # pragma: no cover
    """Cancel all pending tasks on `loop`, wait for them, and close the loop.

    :param loop: The asyncio event loop to shut down.

    """
    try:
        all_tasks = asyncio.all_tasks
        # This part is borrowed from asyncio/runners.py in Python 3.7b2.
        to_cancel = [task for task in all_tasks(loop) if not task.done()]
        if not to_cancel:
            return

        for task in to_cancel:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))
    finally:
        # `concurrent.futures.Future` objects cannot be cancelled once they
        # are already running. There might be some when the `shutdown()` happened.
        # Silence their logger's spew about the event loop being closed.
        cf_logger = logging.getLogger("concurrent.futures")
        cf_logger.setLevel(logging.CRITICAL)
        loop.close()


class Reporter:
    """A class to report messages."""

    def __init__(self, level: int = 1):
        """Initialize the reporter.

        :param level: Verbosity level for reporting.

        """
        self.level = level
        self.error_count = 0

    def _log_message(self, message: str, level: int, **formatting_kwargs: Any):
        """Log a message if the current level is sufficient.

        :param message: Message to log.
        :param level: Minimum level required to show the message.
        :param formatting_kwargs: Additional formatting options for ``click.secho``.

        """
        if self.level >= level:
            echo(message, **formatting_kwargs)
            sys.stderr.flush()
            sys.stdout.flush()

    def debug(self, message: str, **formatting_kwargs: Any):
        """Log a debug message.

        :param message: Debug message to log.
        :param formatting_kwargs: Additional formatting options for ``click.secho``.

        """
        self._log_message(message, 3, bold=False, fg="blue", **formatting_kwargs)

    def error(self, message: str, **formatting_kwargs: Any):
        """Log an error message.

        :param message: Error message to log.
        :param formatting_kwargs: Additional formatting options for ``click.secho``.

        """
        self._log_message(message, -1, bold=False, fg="red", **formatting_kwargs)

    def print(self, message: str, level: int = 0, **formatting_kwargs: Any):
        """Log a message.

        :param message: Message to log.
        :param level: Minimum level required to show the message.
        :param formatting_kwargs: Additional formatting options for ``click.secho``.

        """
        formatting_kwargs.setdefault("bold", level == 0)
        self._log_message(message, level, **formatting_kwargs)


class Visitor(CSTTransformer):
    """A visitor to format docstrings."""

    METADATA_DEPENDENCIES = (PositionProvider, ParentNodeProvider)

    def __init__(
        self,
        file: Path | str,
        input_string: str,
        line_length: int,
        manager: Manager,
        object_name: str,
    ):
        """Initialize the visitor.

        :param file: Path to the file being processed.
        :param input_string: Content of the file.
        :param line_length: Maximum line length.
        :param manager: Manager instance for formatting.
        :param object_name: Name of the object being processed.

        """
        super().__init__()
        self._last_assign: AssignTarget | None = None
        self._object_names = [object_name]
        self._object_type = None
        self._blank_line = manager.docstring_trailing_line
        self.file = file
        self.line_length = line_length
        self.manager = manager
        self.misformatted = False
        self.error_count = 0
        self.line_resolver = LineResolver(self.file, input_string)

    def _is_docstring(self, node: SimpleString) -> bool:
        """Check if the node is a docstring.

        :param node: The SimpleString node to check.

        :returns: True if the node is a docstring, False otherwise.

        """
        return node.quote.startswith(('"""', "'''")) and isinstance(
            self.get_metadata(ParentNodeProvider, node), Expr
        )

    def leave_ClassDef(
        self,
        original_node: ClassDef,
        updated_node: ClassDef,
    ) -> ClassDef:
        """Remove the class name from the object name stack.

        :param original_node: The original ClassDef node.
        :param updated_node: The updated ClassDef node.

        :returns: The updated ClassDef node.

        """
        self._object_names.pop(-1)
        return updated_node

    def leave_FunctionDef(
        self,
        original_node: FunctionDef,
        updated_node: FunctionDef,
    ) -> FunctionDef:
        """Remove the function name from the object name stack.

        :param original_node: The original FunctionDef node.
        :param updated_node: The updated FunctionDef node.

        :returns: The updated FunctionDef node.

        """
        self._object_names.pop(-1)
        return updated_node

    @staticmethod
    def _escape_quoting(node: SimpleString) -> SimpleString:
        """Escapes quotes in a docstring when necessary.

        :param node: The SimpleString node to escape.

        :returns: The escaped SimpleString node.

        """
        # handles quoting escaping once
        for quote in ('"', "'"):
            quoting = quote * 3
            if node.value.startswith(quoting) and node.value.endswith(quoting):
                inner_value = node.value[len(quoting) : -len(quoting)]
                if quoting in inner_value:
                    node = node.with_changes(
                        value=quoting
                        + inner_value.replace(quoting, f"\\{quoting}").replace(
                            quoting + quote, f"{quoting}\\{quote}"
                        )
                        + quoting
                    )
                break
        return node

    def leave_SimpleString(  # noqa: N802
        self, original_node: SimpleString, updated_node: SimpleString
    ) -> SimpleString:
        """Format the docstring.

        :param original_node: The original SimpleString node.
        :param updated_node: The updated SimpleString node.

        :returns: The formatted SimpleString node.

        """
        if self._is_docstring(original_node):
            position_meta = self.get_metadata(PositionProvider, original_node)
            old_object_type = None
            if self._last_assign:
                self._object_names.append(self._last_assign.target.children[2].value)  # type: ignore[attr]
                old_object_type = copy(self._object_type)
                self._object_type = "attribute"
            indent_level = position_meta.start.column  # type: ignore[attr]
            source = dedent(
                (" " * indent_level) + str(original_node.evaluated_value)
            ).rstrip()
            doc = self.manager.parse_string(
                source, self.line_resolver.offset(original_node.value), file=self.file
            )
            if reporter.level >= 3:
                reporter.debug("=" * 60)
                reporter.debug(dump_node(doc))
            width = self.line_length - indent_level
            if width < 1:
                self.error_count += 1
                msg = f"Invalid starting width {self.line_length}"
                raise ValueError(msg)
            try:
                output = self.manager.format_node(width, doc, True).rstrip()
            except InvalidRstErrors as errors:
                self.error_count += 1
                reporter.error(str(errors))
                return updated_node
            self.error_count += self.manager.error_count
            self.manager.error_count = 0
            object_display_name = (
                f"{self._object_type} {'.'.join(self._object_names)!r}"
            )
            single_line = len(output.splitlines()) == 1
            original_strip = str(original_node.evaluated_value).rstrip(" ")
            end_line_count = len(original_strip) - len(original_strip.rstrip("\n"))
            ending = "" if single_line else "\n\n" if self._blank_line else "\n"
            if single_line:
                correct_ending = end_line_count == 0
            else:
                correct_ending = int(self._blank_line) + 1 == end_line_count
            if source == output and correct_ending:
                reporter.print(
                    f"Docstring for {object_display_name} in file {str(self.file)!r} is"
                    " formatted correctly. Nice!",
                    1,
                )
            else:
                self.misformatted = True
                file_link = f'File "{self.file}"'
                reporter.print(
                    "Found incorrectly formatted docstring. Docstring for"
                    f" {object_display_name} in {file_link}.",
                    1,
                )
                value = indent(
                    f'{original_node.prefix}"""{output}{ending}"""', " " * indent_level
                ).lstrip()
                updated_node = updated_node.with_changes(value=value)
            if self._last_assign:
                self._last_assign = None
                self._object_names.pop(-1)
                self._object_type = old_object_type
        return self._escape_quoting(updated_node)

    def visit_AssignTarget_target(self, node: AssignTarget) -> None:
        """Set the last assign node.

        :param node: The AssignTarget node.

        """
        self._last_assign = node

    def visit_ClassDef(self, node: ClassDef) -> bool | None:
        """Set the object type to class.

        :param node: The ClassDef node.

        :returns: True to continue visiting children.

        """
        self._object_names.append(node.name.value)
        self._object_type = "class"
        self._last_assign = None
        return True

    def visit_FunctionDef(self, node: FunctionDef) -> bool | None:
        """Set the object type to function.

        :param node: The FunctionDef node.

        :returns: True to continue visiting children.

        """
        self._object_names.append(node.name.value)
        self._object_type = "function"
        self._last_assign = None
        return True

    def visit_Module(self, node: Module) -> bool | None:
        """Set the object type to module.

        :param node: The Module node.

        :returns: True to continue visiting children.

        """
        self._object_type = "module"
        return True


# noinspection PyUnusedLocal
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-c",
    "--check",
    is_flag=True,
    help=(
        "Check files and returns a non-zero code if files are not formatted correctly."
        " Useful for linting. Ignored if --raw-input, --raw-output, or stdin is used."
    ),
)
@click.option(
    "--docstring-trailing-line/--no-docstring-trailing-line",
    default=True,
    help="Whether to add a blank line at the end of docstrings.",
)
@click.option(
    "-e",
    "--exclude",
    type=str,
    multiple=True,
    default=DEFAULT_EXCLUDE,
    help=(
        "Path(s) to directories/files to exclude in formatting. Supports glob patterns."
    ),
    show_default=True,
)
@click.option(
    "-x",
    "--extend-exclude",
    help=(
        "Path(s) to directories/files to exclude in addition to the default excludes in"
        " formatting. Supports glob patterns."
    ),
    multiple=True,
    type=str,
)
@click.option(
    "-t",
    "--file-type",
    default="rst",
    help="Specify the raw input file type. Can only be used with --raw-input or stdin.",
    show_default=True,
    type=click.Choice(["py", "rst"], case_sensitive=False),
)
@click.option(
    "--format-python-code-blocks/--no-format-python-code-blocks",
    " /-N",
    default=True,
    help="Whether format Python code blocks.",
)
@click.option(
    "-i",
    "--ignore-cache",
    help="Ignore the cache. Useful for testing.",
    is_flag=True,
)
@click.option(
    "-T",
    "--include-txt",
    help="Interpret *.txt files as reStructuredText and format them.",
    is_flag=True,
)
@click.option(
    "-l",
    "--line-length",
    type=click.IntRange(4),
    help=(
        "Wrap lines to the given line length where possible. Takes precedence over"
        " 'line-length' set in pyproject.toml if set. Defaults to the length provided"
        " to black if not set."
    ),
    callback=_resolve_length,
)
@click.option(
    "-pA",
    "--preserve-adornments",
    help="Preserve existing section adornments.",
    is_flag=True,
)
@click.option(
    "-p",
    "--pyproject-config",
    "mode",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
        path_type=str,
    ),
    is_eager=True,
    callback=_parse_pyproject_config,
    help="Path to pyproject.toml. Used to load settings.",
)
@click.option(
    "-q",
    "--quiet",
    help=(
        "Don't emit non-error messages to stderr. Errors are still emitted; silence"
        " those with 2>/dev/null. Overrides --verbose."
    ),
    is_flag=True,
)
@click.option(
    "-r",
    "--raw-input",
    help=(
        "Format the text passed in as a string. Formatted text will be output to"
        " stdout."
    ),
    type=str,
)
@click.option(
    "-o",
    "--raw-output",
    help="Output the formatted text to stdout.",
    is_flag=True,
)
@click.option(
    "-s",
    "--section-adornments",
    type=str,
    default=SECTION_CHARS,
    show_default=True,
    help=(
        "Define adornments for part/chapter/section headers. It defines a sequence of"
        " adornments to use for each individual section depth. The list must be"
        " composed of at least N **distinct** characters for documents with N section"
        " depths. Provide more if unsure. If the special character `|` (pipe) is"
        " used, then it defines sections (left portion) that will have overlines"
        " besides underlines only (right portion). Overrides --preserve-adornments."
    ),
    callback=_validate_adornments,
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help=(
        "Log debugging information about each node being formatted. Can be specified"
        " multiple times for different levels of verbosity."
    ),
)
@click.version_option(version=__version__)
@click.argument("files", nargs=-1, type=str, callback=_parse_sources)
@click.pass_context
def main(
    context: Context,
    check: bool,
    docstring_trailing_line: bool,
    exclude: list[str],
    extend_exclude: list[str],
    file_type: str,
    format_python_code_blocks: bool,
    ignore_cache: bool,
    include_txt: bool,
    line_length: int,
    preserve_adornments: bool,
    mode: Mode,
    quiet: bool,
    raw_input: str,
    raw_output: bool,
    section_adornments: list[tuple[str, bool]] | None,
    verbose: int,
    files: list[str],
) -> None:
    """Format reStructuredText and Python files.

    :param context: Click context containing command parameters.
    :param check: Whether to check formatting without modifying files.
    :param docstring_trailing_line: Whether to add trailing line to docstrings.
    :param exclude: List of paths to exclude from formatting.
    :param extend_exclude: Additional paths to exclude from formatting.
    :param file_type: Type of files to process ('py' or 'rst').
    :param format_python_code_blocks: Whether to format Python code blocks.
    :param ignore_cache: Whether to ignore the cache.
    :param include_txt: Whether to include .txt files.
    :param line_length: Maximum line length.
    :param preserve_adornments: Whether to preserve existing section adornments.
    :param mode: Black formatting mode.
    :param quiet: Whether to suppress non-error output.
    :param raw_input: Raw input string to format.
    :param raw_output: Whether to output raw formatted text.
    :param section_adornments: Section adornment configuration.
    :param verbose: Verbosity level.
    :param files: List of files to format.

    """
    reporter.level = verbose
    if "-" in files and len(files) > 1:
        reporter.error("ValueError: stdin can not be used with other paths")
        context.exit(2)
    if quiet or raw_output or files == ["-"]:
        reporter.level = -1
    misformatted_files = set()

    if line_length is None:
        if mode.line_length != DEFAULT_LINE_LENGTH:
            line_length = mode.line_length
        else:
            line_length = DEFAULT_LINE_LENGTH
    error_count = 0

    if preserve_adornments:
        section_adornments = None

    if raw_input:
        file = "<raw_input>"
        manager = Manager(
            current_file=file,
            black_config=mode,
            docstring_trailing_line=docstring_trailing_line,
            format_python_code_blocks=format_python_code_blocks,
            reporter=reporter,
            section_adornments=section_adornments,
        )
        check = False
        try:
            misformatted = False
            if file_type == "py":
                misformatted, error_count = _process_python(
                    check, file, raw_input, line_length, manager, True
                )
            elif file_type == "rst":
                misformatted, error_count = _process_rst(
                    check, file, raw_input, line_length, manager, True
                )
            if misformatted:
                misformatted_files.add(file)
        except InvalidRstErrors as errors:
            reporter.error(str(errors))
            context.exit(1)
        if error_count > 0:
            context.exit(1)
        context.exit(0)

    cache = FileCache(context, ignore_cache)
    if len(files) < 2:
        for file in files:
            misformatted, error_count = _format_file(
                check,
                Path(file),
                file_type,
                include_txt,
                line_length,
                mode,
                docstring_trailing_line,
                format_python_code_blocks,
                section_adornments,
                raw_output,
                None,
            )
            if misformatted:
                misformatted_files.add(file)

    else:
        # This code is heavily based on that of psf/black
        # see here for license: https://github.com/psf/black/blob/master/LICENSE
        loop = asyncio.new_event_loop()
        worker_count = os.cpu_count()
        if sys.platform == "win32":  # pragma: no cover
            # Work around https://bugs.python.org/issue26903
            worker_count = min(worker_count or 61, 61)
        try:
            executor = ProcessPoolExecutor(max_workers=worker_count)
        except (ImportError, OSError):  # pragma: no cover
            # we arrive here if the underlying system does not support multiprocessing
            # like in AWS Lambda or Termux, in which case we gracefully fall back to
            # a ThreadPollExecutor with just a single worker (more workers would not do us
            # any good due to the Global Interpreter Lock)
            executor = ThreadPoolExecutor(max_workers=1)
        try:
            misformatted_files, error_count = loop.run_until_complete(
                _run_formatter(
                    check,
                    file_type,
                    files,
                    include_txt,
                    docstring_trailing_line,
                    format_python_code_blocks,
                    section_adornments,
                    mode,
                    line_length,
                    raw_output,
                    cache,
                    loop,
                    executor,
                )
            )
        finally:
            shutdown(loop)
            if executor is not None:
                executor.shutdown()
    if misformatted_files and not raw_output:
        if check:
            reporter.print(
                f"{len(misformatted_files)} out of {plural(len(files)):file} could"
                " be reformatted."
            )
        else:
            reporter.print(
                f"{len(misformatted_files)} out of {plural(len(files)):file} were"
                " reformatted."
            )
    elif not raw_output:
        reporter.print(f"{plural(len(files)):file} was checked.")
    if error_count > 0:
        reporter.print(f"Done, but {plural(error_count):error} occurred ❌💥❌")
    elif not raw_output:
        reporter.print("Done! 🎉")
    if (check and misformatted_files) or error_count:
        context.exit(1)
    context.exit(0)


reporter = Reporter(0)

if __name__ == "__main__":  # pragma: no cover
    freeze_support()
    main()
