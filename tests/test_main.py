import os
import subprocess
import sys

import pytest
import toml
from black import DEFAULT_LINE_LENGTH

from docstrfmt.main import main

test_files = [
    "tests/test_files",
    "**/*.rst",
    "**/*.py",
    "tests/test_files/test_file.rst",
    "tests/test_files/py_file.py",
]

test_line_length = [13, 34, 55, 72, 89, 144]

NON_NATIVE_NEWLINE = "\r\n" if os.linesep == "\n" else "\n"


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_check(runner, file):
    args = ["-c", "-l", 80, os.path.abspath(file)]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.endswith(
        "could be reformatted.\n1 out of 1 file could be reformatted.\nDone! 🎉\n"
    )


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_call(file):
    args = ["-c", "-l", "80", os.path.abspath(file)]
    result = subprocess.run(
        [sys.executable, "-m", "docstrfmt", *args],
        stderr=subprocess.PIPE,
        text=True,
        encoding="unicode-escape" if os.name == "nt" else None,
    )
    assert result.returncode == 1
    assert result.stderr.endswith(
        "could be reformatted.\n1 out of 1 file could be reformatted.\nDone! 🎉\n"
    )


@pytest.mark.parametrize("flag", [True, False])
def test_docstring_trailing_line(runner, flag):
    args = [
        f'--{"" if flag else "no-"}docstring-trailing-line',
        "tests/test_files/py_file.py",
    ]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    if flag:
        assert result.output == "1 file were checked.\nDone! 🎉\n"
    else:
        assert result.output.endswith("1 out of 1 file were reformatted.\nDone! 🎉\n")


def test_encoding(runner):
    file = "tests/test_files/test_encoding.rst"
    args = [file]
    result = runner.invoke(main, args=args)
    assert result.output == "1 file were checked.\nDone! 🎉\n"
    assert result.exit_code == 0


def test_encoding_raw_input(runner):
    file = (
        ".. note::\n\n    á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì Ì î Î ï"
        " Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö.\n    õ Õ ø Ø œ Œ ß ú Ú ù Ù û Û ü Ü á Á à À â Â ä Ä ã Ã"
        " å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì.\n"
    )
    args = ["-r", file]
    result = runner.invoke(main, args=args)
    assert result.output == file
    assert result.exit_code == 0


def test_encoding_raw_output(runner):
    file = "tests/test_files/test_encoding.rst"
    args = ["-o", file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert (
        result.output
        == ".. note::\n\n    á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì Ì î"
        " Î ï Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö.\n    õ Õ ø Ø œ Œ ß ú Ú ù Ù û Û ü Ü á Á à À â Â"
        " ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì.\n"
    )


def test_encoding_stdin(runner):
    file = (
        ".. note::\n\n    á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì Ì î Î ï"
        " Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö.\n    õ Õ ø Ø œ Œ ß ú Ú ù Ù û Û ü Ü á Á à À â Â ä Ä ã Ã"
        " å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì.\n"
    )
    args = ["-"]
    result = runner.invoke(main, args=args, input=file)
    assert result.exit_code == 0
    assert result.output == file


@pytest.mark.parametrize(
    "block_type,expected_block_type",
    [
        ("::", "::"),
        (".. code:: sh", ".. code-block:: sh"),
        (".. code:: python", ".. code-block:: python"),
        (".. code-block::", ".. code-block::"),
        (".. code-block:: java", ".. code-block:: java"),
    ],
)
def test_code_to_codeblock(runner, block_type, expected_block_type):
    file = f"{block_type}\n\n    name = ''"
    args = ["-"]
    result = runner.invoke(main, args=args, input=file)
    assert result.exit_code == 0
    name_value = '""' if "python" in file else "''"
    assert result.output == f"{expected_block_type}\n\n    name = {name_value}\n"


def test_exclude(runner):
    args = [
        "-e",
        "tests/test_files/",
        "-e",
        "tests/test_files/error_files/",
        "tests/test_files/",
    ]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == "0 files were checked.\nDone! 🎉\n"


def test_extend_exclude(runner):
    args = [
        "-x",
        "tests/test_files/",
        "-e",
        "tests/test_files/error_files/",
        "tests/test_files/",
    ]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == "0 files were checked.\nDone! 🎉\n"


@pytest.mark.parametrize("file", test_files)
def test_globbing(runner, file):
    args = [
        "-e",
        "tests/test_files/error_files/",
        "-e",
        "tests/test_files/test_encoding.rst",
        "-l",
        80,
        file,
    ]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.endswith("were reformatted.\nDone! 🎉\n")


def test_include_txt(runner):
    args = ["-l", 80, "-T", "tests/test_files/test_file.txt"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.endswith("1 out of 1 file were reformatted.\nDone! 🎉\n")


def test_invalid_blank_return_py(runner):
    file = "tests/test_files/error_files/py_file_error_empty_returns.py"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'InvalidRstError: ERROR: File "{os.path.abspath(file)}", line 66:\nEmpty'
        " `:returns:` field. Please add a field body or omit completely."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_invalid_duplicate_returns_py(runner):
    file = "tests/test_files/error_files/py_file_error_duplicate_returns.py"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'InvalidRstError: ERROR: File "{os.path.abspath(file)}", line 10:\nMultiple'
        " `:return:` fields are not allowed. Please combine them into one."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_invalid_duplicate_types_py(runner):
    file = "tests/test_files/error_files/py_file_error_duplicate_types.py"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'InvalidRstError: ERROR: File "{os.path.abspath(file)}", line 8:\nType hint '
        "is specified both in the field body and in the `:type:` field. Please remove"
        " one of them."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_invalid_multiline_types_py(runner):
    file = "tests/test_files/error_files/py_file_error_multiline_types.py"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'InvalidRstError: ERROR: File "{os.path.abspath(file)}", line 10:\nMulti-line'
        " type hints are not supported."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_invalid_code_block_rst(runner):
    file = "tests/test_files/error_files/test_invalid_syntax.rst"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'{"SyntaxError: unterminated string literal (detected at line 1)" if sys.version_info >= (3, 10, 0) else "SyntaxError: EOL while scanning string literal"}:\n\nFile'
        f' "{os.path.abspath(file)}", line 3:'
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_invalid_code_block_py(runner):
    file = "tests/test_files/error_files/py_file_error_bad_codeblock.py"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    if sys.version_info >= (3, 10, 0):
        error = "SyntaxError: unterminated string literal (detected at line 2)"
    else:
        error = "SyntaxError: EOL while scanning string literal"
    assert result.output.startswith(
        f'{error}:\n\nFile "{os.path.abspath(file)}", line 43:'
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 2 errors occurred ❌💥❌\n"
    )


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_invalid_line_length(runner, file):
    args = ["-l", 3, file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 2
    assert (
        result.output
        == "Usage: main [OPTIONS] [FILES]...\nTry 'main -h' for help.\n\nError: Invalid"
        " value for '-l' / '--line-length': 3 is not in the range x>=4.\n"
    )


def test_invalid_pyproject_toml(runner):
    args = [
        "-p",
        "tests/test_files/error_files/bad_pyproject.toml",
        "tests/test_files/test_file.rst",
    ]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 2
    assert result.output.endswith("Error: Config key extend_exclude must be a list\n")


def test_invalid_rst_file(runner):
    args = ["-", "tests/test_files/test_file.rst"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 2
    assert result.output == "ValueError: stdin can not be used with other paths\n"


def test_invalid_sphinx_metadata_rst(runner):
    file = "tests/test_files/error_files/test_invalid_sphinx_metadata.rst"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'InvalidRstError: ERROR: File "{os.path.abspath(file)}":\nNon-empty Sphinx'
        " `:nocomments\n\ninvalid:` metadata field. Please remove field body or omit"
        " completely."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_invalid_table(runner):
    file = "tests/test_files/error_files/test_invalid_table.rst"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        "NotImplementedError: Tables with cells that span "
        "multiple cells are not supported. Consider using "
        "the 'include' directive to include the table from "
        f"another file.\nFailed to format {os.path.abspath(file)!r}"
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


@pytest.mark.parametrize("length", test_line_length)
@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_line_length(runner, length, file):
    args = ["-l", length, file]
    result = runner.invoke(main, args=args, catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


def test_line_length_resolution__none_set(runner):
    # None is set, should default to black default
    args = ["-p", "tests/test_files/pyproject-line-length_none.toml"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")
    result = runner.invoke(main, args=args + ["-l", DEFAULT_LINE_LENGTH])
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


def test_line_length_resolution__black_set(runner):
    # black is set, should use black value
    args = ["-p", "tests/test_files/pyproject-line-length_black.toml"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    toml_config = toml.load(args[1])
    result = runner.invoke(
        main, args=args + ["-l", toml_config["tool"]["black"]["line-length"]]
    )
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


def test_line_length_resolution__docstrfmt_set(runner):
    # docstrfmt is set, should use docstrfmt value
    args = ["-p", "tests/test_files/pyproject-line-length_docstrfmt.toml"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    toml_config = toml.load(args[1])
    result = runner.invoke(
        main, args=args + ["-l", toml_config["tool"]["docstrfmt"]["line-length"]]
    )
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


def test_line_length_resolution__black_docstrfmt_set(runner):
    # black and docstrfmt is set, should use docstrfmt value
    args = ["-p", "tests/test_files/pyproject-line-length_black+docstrfmt.toml"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    toml_config = toml.load(args[1])
    result = runner.invoke(
        main, args=args + ["-l", toml_config["tool"]["docstrfmt"]["line-length"]]
    )
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


def test_line_length_resolution__cli_black_docstrfmt_set(runner):
    # cli, black, and docstrfmt is set, should use cli value
    args = ["-p", "tests/test_files/pyproject-line-length_black+docstrfmt.toml"]
    result = runner.invoke(main, args=args + ["-l", 125])
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    result = runner.invoke(main, args=args + ["-l", 126])
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")


def test_pyproject_toml(runner):
    args = ["-p", "tests/test_files/pyproject.toml"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


def test_quiet(runner):
    args = ["-q", "-l", 80, "tests/test_files/test_file.rst"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == ""


@pytest.mark.parametrize(
    "file,file_type",
    [("tests/test_files/test_file.rst", "rst"), ("tests/test_files/py_file.py", "py")],
)
def test_raw_input(runner, file, file_type):
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", file_type, "-l", 80, "-r", raw_file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    args[-1] = output = result.output
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == output


def test_raw_input_rst_error(runner):
    file = "tests/test_files/error_files/test_invalid_rst_error.rst"
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", "rst", "-r", raw_file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.startswith(
        'ERROR: File "<raw_input>", line 3:\nMalformed table.\nText in column margin in table line 2.'
    )


def test_raw_input_rst_errors_py(runner):
    file = "tests/test_files/error_files/py_file_error_invalid_rst.py"
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", "py", "-r", raw_file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.startswith(
        'ERROR: File "<raw_input>", line 5:\nMalformed table.\nText in column margin in table line 2.'
    )


def test_raw_input_rst_severe(runner):
    file = "tests/test_files/error_files/test_invalid_rst_severe.rst"
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", "rst", "-r", raw_file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.startswith(
        'SEVERE: File "<raw_input>", line 3:\nTitle overline & underline mismatch.'
    )


def test_raw_input_rst_warning(runner):
    file = "tests/test_files/error_files/test_invalid_rst_warning.rst"
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", "rst", "-r", raw_file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.startswith(
        'WARNING: File "<raw_input>", line 1:\nBullet list ends without a blank line;'
        " unexpected unindent."
    )


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_raw_output(runner, file):
    args = ["-o", file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    if file.endswith("rst"):
        assert result.output.startswith("A ReStructuredText Primer")
    elif file.endswith("py"):
        assert result.output.startswith('"""This is an example python file"""')
    output = result.output
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == output


def test_rst_error(runner):
    file = "tests/test_files/error_files/test_invalid_rst_error.rst"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'ERROR: File "{os.path.abspath(file)}", line 3:\nMalformed table.\nText in'
        " column margin in table line 2."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_rst_severe(runner):
    file = "tests/test_files/error_files/test_invalid_rst_severe.rst"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'SEVERE: File "{os.path.abspath(file)}", line 3:\nTitle overline & underline'
        " mismatch."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


def test_rst_warning(runner):
    file = "tests/test_files/error_files/test_invalid_rst_warning.rst"
    result = runner.invoke(main, args=[file])
    assert result.exit_code == 1
    assert result.output.startswith(
        f'WARNING: File "{os.path.abspath(file)}", line 1:\nBullet list ends without a'
        " blank line; unexpected unindent."
    )
    assert result.output.endswith(
        "1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"
    )


@pytest.mark.parametrize(
    "file,file_type",
    [("tests/test_files/test_file.rst", "rst"), ("tests/test_files/py_file.py", "py")],
)
def test_stdin(runner, file, file_type):
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", file_type, "-l", 80, "-"]
    result = runner.invoke(main, args=args, input=raw_file)
    assert result.exit_code == 0
    output = result.output
    result = runner.invoke(main, args=args, input=output)
    assert result.exit_code == 0
    assert result.output == output


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_too_small_line_length(runner, file):
    args = ["-l", 4, file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.startswith("ValueError: Invalid starting width")


@pytest.mark.parametrize("verbose", ["-v", "-vv", "-vvv"])
@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_verbose(runner, verbose, file):
    args = [verbose, file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0

    file_path = os.path.abspath(file)
    suffix = (
        f"{os.path.basename(file)}' is formatted correctly. Nice!\n1 file were"
        " checked.\nDone! 🎉\n"
    )
    if file.endswith("rst"):
        results = [
            ("File '", suffix),
            (f"Checking {file_path}\nFile '", suffix),
        ]
    else:
        results = [
            ("Docstring for module 'py_file' in file", suffix),
            (f"Checking {file_path}\nDocstring for module 'py_file' in file", suffix),
        ]
    results.append(
        (
            (
                "Checking"
                f" {file_path}\n============================================================\n-"
                " document"
            ),
            suffix,
        )
    )
    level = verbose.count("v")
    startswith, endswith = results[level - 1]
    assert result.output.startswith(startswith)
    assert result.output.endswith(endswith)


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
@pytest.mark.parametrize("newline", [os.linesep, NON_NATIVE_NEWLINE])
def test_newline_preserved(runner, tmp_path, file, newline):
    with open(file, encoding="utf-8") as source_file:
        source_content = source_file.read()
    test_file_path = tmp_path / os.path.basename(file)
    with open(test_file_path, "w", encoding="utf-8", newline=newline) as test_file:
        test_file.write(source_content)

    cli_args = ["-l", 80, test_file_path.resolve().as_posix()]
    result = runner.invoke(main, args=cli_args)
    assert result.exit_code == 0
    assert result.output.endswith("1 out of 1 file were reformatted.\nDone! 🎉\n")
    with open(test_file_path, encoding="utf-8") as output_file:
        output_file.read()
        assert output_file.newlines == newline


def test_type_replaced(runner, tmp_path):
    file = "tests/test_files/error_files/py_file_type_field_removal.py"
    args = ["-o", file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert (
        result.output
        == '"""This is an example python file"""\n\n\nclass ExampleClass:\n    def'
        ' __init__(self, arg, *args, **kwargs):\n        """First doc str\n\n       '
        " :param arg: Arg\n        :param list args: Args\n        :param dict kwargs:"
        " Kwargs but with a really long description that will need to\n            be"
        " rewrapped because it is really long and won't fit in the default 88\n"
        "            characters.\n\n        :returns: Returns\n\n        :var str arg:"
        ' Arg\n\n        """\n'
    )
