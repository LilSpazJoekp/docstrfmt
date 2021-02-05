import asyncio
import contextlib
import glob
import os
import signal
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from copy import copy
from functools import partial
from multiprocessing import Manager as MultiManager
from multiprocessing import freeze_support
from os.path import abspath, basename
from pathlib import Path
from textwrap import dedent, indent
from typing import TYPE_CHECKING, Any, List, Optional

import click
import libcst as cst
from black import (
    PY36_VERSIONS,
    Mode,
    TargetVersion,
    cancel,
    find_pyproject_toml,
    parse_pyproject_toml,
    shutdown,
)
from click import Context
from libcst import CSTTransformer, Expr
from libcst.metadata import ParentNodeProvider, PositionProvider

from docstrfmt.const import __version__
from docstrfmt.debug import dump_node
from docstrfmt.docstrfmt import Manager
from docstrfmt.exceptions import InvalidRstErrors
from docstrfmt.util import FileCache, plural

if TYPE_CHECKING:  # pragma: no cover
    from libcst import AssignTarget, ClassDef, FunctionDef, Module, SimpleString

echo = partial(click.secho, err=True)


# Define this here to support Python <3.7.
class nullcontext(contextlib.AbstractContextManager):  # type: ignore
    def __init__(self, enter_result: Any = None):
        self.enter_result = enter_result

    def __enter__(self) -> Any:
        return self.enter_result

    def __exit__(self, *excinfo: Any) -> Any:
        pass


class Reporter:
    def __init__(self, level=1):
        self.level = level
        self.error_count = 0

    def _log_message(self, message, level, **formatting_kwargs):
        if self.level >= level:
            echo(message, **formatting_kwargs)
            sys.stderr.flush()
            sys.stdout.flush()

    def debug(self, message, **formatting_kwargs):
        self._log_message(message, 3, bold=False, fg="blue", **formatting_kwargs)

    def error(self, message, **formatting_kwargs):
        self._log_message(message, -1, bold=False, fg="red", **formatting_kwargs)

    def print(self, message, level=0, **formatting_kwargs):
        formatting_kwargs.setdefault("bold", level == 0)
        self._log_message(message, level, **formatting_kwargs)


reporter = Reporter(0)


class Visitor(CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider, ParentNodeProvider)

    def __init__(self, object_name, file, line_length, manager):
        super().__init__()
        self._last_assign = None
        self._object_names = [object_name]
        self._object_type = None
        self._blank_line = manager.docstring_trailing_line
        self.file = file
        self.line_length = line_length
        self.manager = manager
        self.misformatted = False
        self.error_count = 0

    def _is_docstring(self, node: "SimpleString") -> bool:
        return node.quote.startswith(('"""', "'''")) and isinstance(
            self.get_metadata(ParentNodeProvider, node), Expr
        )

    def leave_ClassDef(self, original_node: "ClassDef", updated_node: "ClassDef"):
        self._object_names.pop(-1)
        return updated_node

    def leave_FunctionDef(
        self, original_node: "FunctionDef", updated_node: "FunctionDef"
    ):
        self._object_names.pop(-1)
        return updated_node

    def leave_SimpleString(
        self, original_node: "SimpleString", updated_node: "SimpleString"
    ):
        if self._is_docstring(original_node):
            position_meta = self.get_metadata(PositionProvider, original_node)
            if self._last_assign:
                self._object_names.append(self._last_assign.target.children[2].value)
                old_object_type = copy(self._object_type)
                self._object_type = "attribute"
            indent_level = position_meta.start.column
            source = dedent(
                (" " * indent_level) + original_node.evaluated_value
            ).rstrip()
            doc = self.manager.parse_string(self.file, source)
            if reporter.level >= 3:
                reporter.debug("=" * 60)
                reporter.debug(dump_node(doc))
            width = self.line_length - indent_level
            if width < 1:
                self.error_count += 1
                raise ValueError(f"Invalid starting width {self.line_length}")
            output = self.manager.format_node(width, doc, True).rstrip()
            self.error_count += self.manager.error_count
            self.manager.error_count = 0
            object_display_name = (
                f'{self._object_type} {".".join(self._object_names)!r}'
            )
            single_line = len(output.splitlines()) == 1
            original_strip = original_node.evaluated_value.rstrip(" ")
            end_line_count = len(original_strip) - len(original_strip.rstrip("\n"))
            ending = "" if single_line else "\n\n" if self._blank_line else "\n"
            if single_line:
                correct_ending = 0 == end_line_count
            else:
                correct_ending = int(self._blank_line) + 1 == end_line_count
            if source == output and correct_ending:
                reporter.print(
                    f"Docstring for {object_display_name} in file {str(self.file)!r} is formatted correctly. Nice!",
                    1,
                )
            else:
                self.misformatted = True
                file_link = f'File "{self.file}"'
                reporter.print(
                    f"Found incorrectly formatted docstring. Docstring for {object_display_name} in {file_link}.",
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
        return updated_node

    def visit_AssignTarget_target(self, node: "AssignTarget") -> None:
        self._last_assign = node

    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        self._object_names.append(node.name.value)
        self._object_type = "class"
        self._last_assign = None
        return True

    def visit_FunctionDef(self, node: "FunctionDef") -> Optional[bool]:
        self._object_names.append(node.name.value)
        self._object_type = "function"
        self._last_assign = None
        return True

    def visit_Module(self, node: "Module") -> Optional[bool]:
        self._object_type = "module"
        return True


async def _run_formatter(
    check,
    file_type,
    files,
    include_txt,
    docstring_trailing_line,
    mode,
    raw_output,
    cache,
    loop,
    executor,
):
    # This code is heavily based on that of psf/black
    # see here for license: https://github.com/psf/black/blob/master/LICENSE
    todo, already_done = cache.gen_todo_list(files)
    cancelled = []
    files_to_cache = []
    lock = MultiManager().Lock()
    line_length = mode.line_length
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
                raw_output,
                lock,
            )
        ): file
        for file in sorted(todo)
    }
    in_process = tasks.keys()
    try:
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
        await asyncio.gather(*cancelled, loop=loop, return_exceptions=True)
    if files_to_cache:
        cache.write_cache(files_to_cache)
    return misformatted_files, error_count


def _format_file(
    check,
    file,
    file_type,
    include_txt,
    line_length,
    mode,
    docstring_trailing_line,
    raw_output,
    lock,
):
    error_count = 0
    manager = Manager(reporter, mode, docstring_trailing_line)
    if file.name == "-":
        raw_output = True
    reporter.print(f"Checking {file}", 2)
    misformatted = False
    with nullcontext(sys.stdin) if file.name == "-" else open(
        file, encoding="utf-8"
    ) as f:
        input_string = f.read()
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
            )
            error_count += errors
    except InvalidRstErrors as errors:
        reporter.error(str(errors))
        error_count += 1
        reporter.print(f"Failed to format {str(file)!r}")
    except Exception as error:
        reporter.error(f"{error.__class__.__name__}: {error}")
        error_count += 1
        reporter.print(f"Failed to format {str(file)!r}")
    return misformatted, error_count


def _parse_pyproject_config(
    context: click.Context, param: click.Parameter, value: Optional[str]
) -> Mode:
    if not value:
        pyproject_toml = find_pyproject_toml(tuple(context.params.get("files", ())))
        value = pyproject_toml if pyproject_toml else None
    if value:
        config = parse_pyproject_toml(value)
        config.pop("exclude", None)
        target_version = config.pop("target_version", PY36_VERSIONS)
        if target_version != PY36_VERSIONS:
            target_version = set(
                getattr(TargetVersion, version.upper())
                for version in target_version.split(",")
                if hasattr(TargetVersion, version.upper())
            )
        config["target_versions"] = target_version
        return Mode(**config)
    else:
        return Mode(line_length=88, target_versions=PY36_VERSIONS)


def _parse_sources(
    context: click.Context, param: click.Parameter, value: Optional[List[str]]
):
    sources = value
    exclude = context.params.get("exclude", [])
    include_txt = context.params.get("include_txt", False)
    files_to_format = set()
    extensions = [".py", ".rst"] + ([".txt"] if include_txt else [])
    for source in sources:
        if source == "-":
            files_to_format.add(source)
        else:
            for item in glob.iglob(source, recursive=True):
                path = Path(item)
                if path.is_dir():
                    for file in [
                        found
                        for extension in extensions
                        for found in glob.iglob(
                            f"{path}/**/*{extension}", recursive=True
                        )
                    ]:
                        files_to_format.add(abspath(file))
                elif path.is_file():
                    files_to_format.add(abspath(item))
    for file in exclude:
        for f in glob.iglob(file, recursive=True):
            f = abspath(f)
            if f in files_to_format:
                files_to_format.remove(f)
    return sorted(list(files_to_format))


def _process_python(
    check, file, input_string, line_length, manager, raw_output, lock=None
):
    filename = basename(file)
    object_name = filename.split(".")[0]
    visitor = Visitor(object_name, file, line_length, manager)
    module = cst.parse_module(input_string)
    wrapper = cst.MetadataWrapper(module)
    result = wrapper.visit(visitor)
    error_count = visitor.error_count
    misformatted = False
    if visitor.misformatted:
        misformatted = True
        if check and not raw_output:
            reporter.print(f"File {str(file)!r} could be reformatted.")
        else:
            if file == "-" or raw_output:
                with lock or nullcontext():
                    _write_output(
                        file, result.code, nullcontext(sys.stdout), raw_output
                    )
            else:
                _write_output(
                    file, result.code, open(file, "w", encoding="utf-8"), raw_output
                )
    elif raw_output:
        with lock or nullcontext():
            _write_output(file, input_string, nullcontext(sys.stdout), raw_output)
    return misformatted, error_count


def _process_rst(
    check, file, input_string, line_length, manager, raw_output, lock=None
):
    doc = manager.parse_string(file, input_string)
    if reporter.level >= 3:
        reporter.debug("=" * 60)
        reporter.debug(dump_node(doc))
    output = manager.format_node(line_length, doc)
    error_count = manager.error_count
    misformatted = False
    if output == input_string:
        reporter.print(f"File {str(file)!r} is formatted correctly. Nice!", 1)
        if raw_output:
            with lock or nullcontext():
                _write_output(file, input_string, nullcontext(sys.stdout), raw_output)
    else:
        misformatted = True
        if check and not raw_output:
            reporter.print(f"File {str(file)!r} could be reformatted.")
        else:
            if file == "-" or raw_output:
                with lock or nullcontext():
                    _write_output(file, output, nullcontext(sys.stdout), raw_output)
            else:
                _write_output(
                    file, output, open(file, "w", encoding="utf-8"), raw_output
                )
    return misformatted, error_count


def _write_output(file, output, output_manager, raw):
    with output_manager as f:
        f.write(output)
    if not raw:
        reporter.print(f"Reformatted {str(file)!r}.")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-p",
    "--pyproject_config",
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
    help="Path to pyproject.toml. Used to load black settings.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Log debugging information about each node being formatted. Can be specified multiple times for different levels of verbosity.",
)
@click.option(
    "-r",
    "--raw-input",
    type=str,
    help="Format the text passed in as a string. Formatted text will be output to stdout.",
)
@click.option(
    "-o", "--raw_output", is_flag=True, help="Output the formatted text to stdout."
)
@click.option(
    "-l",
    "--line-length",
    type=click.IntRange(4),
    default=88,
    help="Wrap lines to the given line length where possible. Takes precedence over 'line_length' set in pyproject.toml if set.",
    show_default=True,
)
@click.option(
    "-t",
    "--file-type",
    type=click.Choice(["py", "rst"], case_sensitive=False),
    default="rst",
    help="Specify the raw input file type. Can only be used with --raw-input or stdin.",
    show_default=True,
)
@click.option(
    "-c",
    "--check",
    is_flag=True,
    help="Check files and returns a non-zero code if files are not formatted correctly. Useful for linting. Ignored if raw-input, raw-output, stdin is used.",
)
@click.option(
    "-T",
    "--include_txt",
    is_flag=True,
    help="Interpret *.txt files as reStructuredText and format them.",
)
@click.option(
    "-e",
    "--exclude",
    type=str,
    multiple=True,
    default=[
        "**/.direnv/",
        "**/.direnv/",
        "**/.eggs/",
        "**/.git/",
        "**/.hg/",
        "**/.mypy_cache/",
        "**/.nox/",
        "**/.tox/",
        "**/.venv/",
        "**/.svn/",
        "**/_build",
        "**/buck-out",
        "**/build",
        "**/dist",
    ],
    help="Path(s) to directories/files to exclude in formatting. Supports glob patterns.",
    show_default=True,
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Don't emit non-error messages to stderr. Errors are still emitted; silence those with 2>/dev/null. Overrides --verbose.",
)
@click.option(
    "--docstring-trailing-line/--no-docstring-trailing-line",
    default=True,
    help="Whether or not to add a blank line at the end of docstrings.",
)
@click.version_option(version=__version__)
@click.argument(
    "files",
    nargs=-1,
    type=str,
    callback=_parse_sources,
)
@click.pass_context
def main(
    context: Context,
    mode: Mode,
    raw_input: str,
    raw_output: bool,
    verbose: int,
    line_length: int,
    file_type: str,
    check: bool,
    include_txt: bool,
    exclude: List[str],
    quiet: bool,
    docstring_trailing_line: bool,
    files: List[str],
) -> None:
    reporter.level = verbose
    if "-" in files and len(files) > 1:
        reporter.error("ValueError: stdin can not be used with other paths")
        context.exit(2)
    if quiet or raw_output or files == ["-"]:
        reporter.level = -1
    misformatted_files = set()

    if line_length != 88:
        mode.line_length = line_length
    error_count = 0
    if raw_input:
        manager = Manager(reporter, mode, docstring_trailing_line)
        file = "<raw_input>"
        check = False
        try:
            misformatted = False
            if file_type == "py":
                misformatted, _ = _process_python(
                    check, file, raw_input, line_length, manager, True
                )
            elif file_type == "rst":
                misformatted, _ = _process_rst(
                    check, file, raw_input, line_length, manager, True
                )
            if misformatted:
                misformatted_files.add(file)
        except InvalidRstErrors as errors:
            reporter.error(str(errors))
            context.exit(1)
        context.exit(0)

    cache = FileCache(context)
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
                raw_output,
                None,
            )
            if misformatted:
                misformatted_files.add(file)

    else:
        # This code is heavily based on that of psf/black
        # see here for license: https://github.com/psf/black/blob/master/LICENSE
        executor = None
        loop = asyncio.get_event_loop()
        worker_count = os.cpu_count()
        if sys.platform == "win32":  # pragma: no cover
            # Work around https://bugs.python.org/issue26903
            worker_count = min(worker_count, 61)
        try:
            executor = ProcessPoolExecutor(max_workers=worker_count)
        except (ImportError, OSError):  # pragma: no cover
            # we arrive here if the underlying system does not support multi-processing
            # like in AWS Lambda or Termux, in which case we gracefully fallback to
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
                    mode,
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
                f"{len(misformatted_files)} out of {plural('file', len(files))} could be reformatted."
            )
        else:
            reporter.print(
                f"{len(misformatted_files)} out of {plural('file', len(files))} were reformatted."
            )
    elif not raw_output:
        reporter.print(f"{plural('file', len(files))} were checked.")
    if error_count > 0:
        reporter.print(f"Done, but {plural('error', error_count)} occurred ❌💥❌")
    elif not raw_output:
        reporter.print("Done! 🎉")
    if (check and misformatted_files) or error_count:
        context.exit(1)
    context.exit(0)


if __name__ == "__main__":  # pragma: no cover
    freeze_support()
    main()
