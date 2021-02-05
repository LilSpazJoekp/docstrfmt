import os
import pickle
import tempfile
from copy import copy
from pathlib import Path

from appdirs import user_cache_dir
from docutils.parsers.rst.states import ParserError
from docutils.utils import roman

from .const import __version__


class FileCache:
    def __init__(self, context):
        self.cache_dir = Path(user_cache_dir("docstrfmt", version=__version__))
        self.context = context
        self.cache = self.read_cache()

    @staticmethod
    def get_file_info(file):
        file_info = file.stat()
        return file_info.st_mtime, file_info.st_size

    def gen_todo_list(self, files):
        todo, done = set(), set()
        for file in files:
            file = Path(file)
            file = file.resolve()
            if self.cache.get(file) != self.get_file_info(file):
                todo.add(file)
            else:  # pragma: no cover
                done.add(file)
        return todo, done

    def get_cache_filename(self):
        mode = copy(self.context.params["mode"].__dict__)
        mode["target_versions"] = ",".join(
            sorted([str(version.value) for version in mode["target_versions"]])
        )
        docstring_trailing_line = str(self.context.params["docstring_trailing_line"])
        line_length = str(self.context.params["line_length"])
        mode = "_".join([str(mode[key]) for key in sorted(mode)])
        include_txt = str(self.context.params["include_txt"])
        return (
            self.cache_dir
            / f"cache.{'_'.join([docstring_trailing_line, line_length, mode, include_txt])}.pickle"
        )

    def read_cache(self):
        cache_file = self.get_cache_filename()
        if not cache_file.exists():
            return {}
        with cache_file.open("rb") as f:
            try:
                return pickle.load(f)
            except (pickle.UnpicklingError, ValueError):  # pragma: no cover
                return {}

    def write_cache(self, files) -> None:
        """Update the cache file."""
        cache_file = self.get_cache_filename()
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            new_cache = {
                **self.cache,
                **{file.resolve(): self.get_file_info(file) for file in files},
            }
            with tempfile.NamedTemporaryFile(
                dir=str(cache_file.parent), delete=False
            ) as f:
                pickle.dump(new_cache, f, protocol=4)
            os.replace(f.name, cache_file)
        except OSError:  # pragma: no cover
            pass


def get_code_line(current_source, code):
    lines = current_source.splitlines()
    code_lines = code.splitlines()
    multiple = len([line for line in lines if code_lines[0] in line]) > 1
    for line_number, line in enumerate(lines, 1):
        if code_lines[0] in line:
            if multiple:
                current_offset = 0
                for offset, sub_line in enumerate(code_lines):
                    current_offset = offset
                    if sub_line not in lines[line_number - 1 + offset]:
                        break
                else:
                    return line_number + current_offset
            else:
                return line_number


# Modified from docutils.parsers.rst.states.Body
def make_enumerator(ordinal, sequence, format):
    """Construct and return the next enumerated list item marker, and an auto-enumerator
    ("#" instead of the regular enumerator).

    Return ``None`` for invalid (out of range) ordinals.

    """
    if sequence == "#":  # pragma: no cover
        enumerator = "#"
    elif sequence == "arabic":
        enumerator = str(ordinal)
    else:
        if sequence.endswith("alpha"):
            if ordinal > 26:  # pragma: no cover
                return None
            enumerator = chr(ordinal + ord("a") - 1)
        elif sequence.endswith("roman"):
            try:
                enumerator = roman.toRoman(ordinal)
            except roman.RomanError:  # pragma: no cover
                return None
        else:  # pragma: no cover
            raise ParserError(f'unknown enumerator sequence: "{sequence}"')
        if sequence.startswith("lower"):
            enumerator = enumerator.lower()
        elif sequence.startswith("upper"):
            enumerator = enumerator.upper()
        else:  # pragma: no cover
            raise ParserError(f'unknown enumerator sequence: "{sequence}"')
    next_enumerator = format[0] + enumerator + format[1]
    return next_enumerator


def plural(word, count, thousands_separator=True):
    if count == 1:
        s = False
    else:
        s = True
    count_str = f"{count:,}" if thousands_separator else str(count)
    return f"{count_str} {word}s" if s else f"{count_str} {word}"
