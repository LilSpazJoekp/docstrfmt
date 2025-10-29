"""Utility functions for docstrfmt."""

from __future__ import annotations

import pickle
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import roman
from docutils.parsers.rst.states import ParserError
from platformdirs import user_cache_path

if TYPE_CHECKING:
    import click


# Modified from docutils.parsers.rst.states.Body
def make_enumerator(ordinal: int, sequence: str, fmt: tuple[str, str]) -> str:
    """Construct and return the next enumerated list item marker, and an auto-enumerator ("#" instead of the regular enumerator).

    :param ordinal: The ordinal number.
    :param sequence: The sequence type (arabic, alpha, roman, etc.).
    :param fmt: Format tuple for the enumerator.

    :returns: The formatted enumerator string or None for invalid ordinals.

    """
    if sequence == "#":  # pragma: no cover
        enumerator = "#"
    elif sequence == "arabic":
        enumerator = str(ordinal)
    else:
        if sequence.endswith("alpha"):
            if ordinal > 26:  # pragma: no cover
                msg = "alphabetic enumerators support only up to 26 items"
                raise ParserError(msg) from None
            enumerator = chr(ordinal + ord("a") - 1)
        elif sequence.endswith("roman"):
            try:
                enumerator = roman.toRoman(ordinal)
            except roman.RomanError:  # pragma: no cover
                msg = "invalid roman numeric enumerator"
                raise ParserError(msg) from None
        else:  # pragma: no cover
            msg = f'unknown enumerator sequence: "{sequence}"'
            raise ParserError(msg)
        if sequence.startswith("lower"):
            enumerator = enumerator.lower()
        elif sequence.startswith("upper"):
            enumerator = enumerator.upper()
        else:  # pragma: no cover
            msg = f'unknown enumerator sequence: "{sequence}"'
            raise ParserError(msg) from None
    return fmt[0] + enumerator + fmt[1]


class FileCache:
    """A class to manage the cache of files."""

    @staticmethod
    def _get_file_info(file: Path) -> tuple[float, int]:
        """Get the file info.

        :param file: Path to the file.

        :returns: Tuple of (modification time, file size).

        """
        file_info = file.stat()
        return file_info.st_mtime, file_info.st_size

    def __init__(self, context: click.Context, ignore_cache: bool = False):
        """Initialize the cache.

        :param context: Click context containing command parameters.
        :param ignore_cache: Whether to ignore the cache.

        """
        from . import __version__  # noqa: PLC0415

        self.cache_dir = user_cache_path("docstrfmt", version=__version__)
        self.context = context
        self.cache = self._read_cache()
        self.ignore_cache = ignore_cache

    def _get_cache_filename(self) -> Path:
        """Get the cache filename.

        :returns: Path to the cache file.

        """
        docstring_trailing_line = str(self.context.params["docstring_trailing_line"])
        format_python_code_blocks = str(
            self.context.params["format_python_code_blocks"]
        )
        line_length = str(self.context.params["line_length"])
        mode = self.context.params["mode"].get_cache_key()
        include_txt = str(self.context.params["include_txt"])
        return (
            self.cache_dir
            / f"cache.{f'{docstring_trailing_line}_{format_python_code_blocks}_{include_txt}_{line_length}_{mode}'}.pickle"
        )

    def _read_cache(self) -> dict[str, tuple[float, int]]:
        """Read the cache file.

        :returns: Dictionary mapping file paths to (modification time, file size)
            tuples.

        """
        cache_file = self._get_cache_filename()
        if not cache_file.exists():
            return {}
        with cache_file.open("rb") as f:
            try:
                return pickle.load(f)  # noqa: S301
            except (
                pickle.UnpicklingError,
                ValueError,
                ModuleNotFoundError,
            ):  # pragma: no cover
                return {}

    def gen_todo_list(self, files: list[str]) -> tuple[set[Path], set[Path]]:
        """Generate the list of files to process.

        :param files: List of file paths to check.

        :returns: Tuple of (files to process, files already done).

        """
        todo, done = set(), set()
        for file in (Path(f).resolve() for f in files):
            if (
                self.cache.get(str(file)) != self._get_file_info(file)
                or self.ignore_cache
            ):
                todo.add(file)
            else:
                done.add(file)
        return todo, done

    def write_cache(self, files: list[Path]) -> None:
        """Update the cache file.

        :param files: List of file paths to cache.

        """
        cache_file = self._get_cache_filename()
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            new_cache = {
                **self.cache,
                **{str(file.resolve()): self._get_file_info(file) for file in files},
            }
            with tempfile.NamedTemporaryFile(
                dir=str(cache_file.parent), delete=False
            ) as f:
                pickle.dump(new_cache, f, protocol=4)  # type: ignore[call-arg]
            Path(f.name).replace(cache_file)
        except OSError:  # pragma: no cover
            pass


class LineResolver:
    """A class to resolve the line number of a code block in a file."""

    def __init__(self, file: Path | str, source: str) -> None:
        """Initialize the class.

        :param file: Path to the file.
        :param source: Source code content.

        """
        self.file = file
        self.source = source
        self._results = defaultdict(list)
        self._searches = set()

    def offset(self, code: str) -> int:
        """Get the line number of the code in the file.

        :param code: Code string to find.

        :returns: Line number of the code in the file.

        :raises ValueError: If the code is not found in the file.

        """
        if code not in self._searches:
            if code not in self.source:  # pragma: no cover should be impossible
                msg = f"Code not found in {self.file}"
                raise ValueError(msg)
            self._searches.add(code)
            split = self.source.split(code)
            for i, _block in enumerate(split[:-1]):
                self._results[code].append(code.join(split[: i + 1]).count("\n") + 1)
        if not self._results[code]:  # pragma: no cover should be impossible
            msg = f"Code not found in {self.file}"
            raise ValueError(msg)
        return self._results[code].pop(0)


class plural:  # noqa: N801
    """A class to format a number with a singular or plural form."""

    def __format__(self, format_spec: str) -> str:
        """Format the number with a singular or plural form.

        :param format_spec: Format specification string.

        :returns: Formatted string with singular or plural form.

        """
        v = self.value
        singular_form, _, plural_form = format_spec.partition("|")
        plural_form = plural_form or f"{singular_form}s"
        if abs(v) != 1:
            return f"{v:,} {plural_form}"
        return f"{v:,} {singular_form}"

    def __init__(self, value: int) -> None:
        """Initialize the class with a number.

        :param value: The numeric value.

        """
        self.value: int = value
