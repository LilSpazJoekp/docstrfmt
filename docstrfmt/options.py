"""Configuration objects shared by the CLI, the file pipeline, and the formatter.

Configuration flows in one direction:

1. :func:`docstrfmt.main.main` collects values from the command line and
   ``pyproject.toml`` and builds a single :class:`RunOptions`.
2. The file pipeline (``_run_formatter`` -> ``_format_file`` -> ``_process_*``) passes
   that object down unchanged.
3. ``_format_file`` hands ``RunOptions.format_options`` to :class:`docstrfmt.Manager`,
   which exposes it as ``manager.options`` and on every
   :class:`docstrfmt.docstrfmt.FormatContext` as ``context.options``.

To add a formatting option, add a field to :class:`FormatOptions`, a matching
``click.option`` in :mod:`docstrfmt.main`, and read it from ``context.options`` in the
formatter. Nothing in between needs to change.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .const import DEFAULT_LINE_LENGTH

if TYPE_CHECKING:
    from collections.abc import Sequence

    from black import Mode

    from .rst_extras import CustomDirectiveSpec


@dataclass(frozen=True)
class FormatOptions:
    """Options that control how reStructuredText is formatted.

    This is the only configuration :class:`docstrfmt.Manager` needs. Instances are
    frozen and the sequence fields are stored as tuples, so an options object can be
    shared between files, threads, and worker processes without one consumer's changes
    leaking into another. Directive specs supplied as mappings are kept as given and are
    not copied.

    """

    black_config: Mode | None = None
    """Black configuration used to format Python code blocks.

    ``None`` leaves Python code blocks untouched.

    """
    bullet_list_marker: str = "-"
    """Bullet character to use for unordered lists."""
    center_section_titles: bool = True
    """Whether to center section titles that have overlines with a leading space."""
    custom_directives: Sequence[CustomDirectiveSpec] = ()
    """User-supplied directives to register.

    See :func:`docstrfmt.rst_extras.register_custom`.

    """
    custom_roles: Sequence[str] = ()
    """User-supplied role names to register as generic roles."""
    docstring_trailing_line: bool = True
    """Whether to add a blank line at the end of multi-line docstrings."""
    format_python_code_blocks: bool = True
    """Whether to format Python code blocks with black."""
    indent_width: int = 4
    """Number of spaces per indentation level."""
    keep_blanks: bool = False
    """Keep blank lines between sections as they appear in the source."""
    line_length: int = DEFAULT_LINE_LENGTH
    """Maximum line length to wrap to."""
    ordered_marker: str = "1"
    """Marker style for ordered lists: ``1`` keeps numbering, ``#`` auto-enumerates."""
    section_adornments: Sequence[tuple[str, bool]] | None = None
    """Adornment ``(character, has_overline)`` per section depth.

    ``None`` preserves the adornments found in the source.

    """

    def __post_init__(self) -> None:
        """Store sequence fields as tuples so they cannot be mutated through a shared reference."""
        for name in ("custom_directives", "custom_roles", "section_adornments"):
            value: Any = getattr(self, name)
            # Only sequences are converted; anything else is left for
            # rst_extras.validate_custom to reject with a clear message.
            if isinstance(value, (list, tuple)):
                object.__setattr__(self, name, tuple(value))


@dataclass(frozen=True)
class RunOptions:
    """Options that control how a single ``docstrfmt`` invocation handles files.

    These affect what is read, written, and reported, not how text is formatted.

    """

    check: bool = False
    """Report files that would change instead of rewriting them."""
    file_type: str = "rst"
    """How to interpret input without a file extension (stdin or raw input)."""
    format_options: FormatOptions = field(default_factory=FormatOptions)
    """Formatting options handed to :class:`docstrfmt.Manager`."""
    include_txt: bool = False
    """Interpret ``*.txt`` files as reStructuredText."""
    raw_output: bool = False
    """Write formatted text to stdout instead of back to the file."""
