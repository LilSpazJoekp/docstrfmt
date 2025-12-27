"""Format reStructuredText docstrings to a consistent style."""

from __future__ import annotations

import itertools
import re
import string
from collections import namedtuple
from collections.abc import Iterable, Iterator
from copy import copy
from dataclasses import dataclass
from doctest import DocTestParser
from math import floor
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    cast,
)

import black
from black import Mode
from blib2to3.pgen2.tokenize import TokenError
from docutils import nodes, utils
from docutils.frontend import OptionParser
from docutils.parsers import rst
from docutils.parsers.rst import Directive, roles
from docutils.transforms import Transform
from docutils.utils import new_document, unescape

from . import NODE_MAPPING, rst_extras
from .exceptions import InvalidRstError, InvalidRstErrors
from .util import make_enumerator

if TYPE_CHECKING:
    import logging
    from pathlib import Path

    from .main import Reporter

T = TypeVar("T")

directive_first_line_attribute = re.compile(r"^\.\. (\w+):: +\S+\n")
valid_reference_id = re.compile(r"^[-_.:+a-zA-Z0-9]+$")
invalid_reference_id = re.compile("[-_.:+][-_.:+]")

unknown_handlers = [
    (
        re.compile(r'Unknown directive type "([^"]+)".'),
        lambda name: rst_extras.add_directive(
            name, Directive, raw=True, is_injected=True
        ),
    ),
    (
        re.compile(r'Unknown interpreted text role "([^"]+)".'),
        lambda name: roles.register_local_role(name, rst_extras.generic_role),
    ),
]

# https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#inline-markup-recognition-rules
space_chars = set(string.whitespace)
pre_markup_break_chars = space_chars | set("-:/'\"<([{")
post_markup_break_chars = space_chars | set("-.,:;!?\\/'\")]}>")

chain = itertools.chain.from_iterable


class IgnoreMessagesReporter(utils.Reporter):
    """A Docutils error reporter that ignores some messages.

    We want to handle most system messages normally, but it's useful to ignore some (and
    just doing it by level would be too coarse). In particular, having too short a title
    line leads to a warning but parses just fine; ignoring that message means we can
    automatically fix lengths whether they're too short or too long (though they do have
    to be at least four characters to be parsed correctly in the first place).

    """

    ignored_messages = {"Title overline too short.", "Title underline too short."}

    def system_message(
        self, level: int, message: str, *children: Any, **kwargs: Any
    ) -> nodes.system_message:  # pragma: no cover
        """Create a system message, possibly ignoring it.

        :param level: Message level.
        :param message: Message text.
        :param children: Child nodes.
        :param kwargs: Additional keyword arguments.

        :returns: System message node.

        """
        orig_level = self.halt_level
        if message in self.ignored_messages:
            self.halt_level = utils.Reporter.SEVERE_LEVEL + 1
        msg = super().system_message(level, message, *children, **kwargs)
        self.halt_level = orig_level
        return msg


class UnknownNodeTransformer(Transform):
    """Transform to handle unknown nodes."""

    default_priority = 0

    def apply(self, **_: Any):
        """Apply the transform.

        :param _: Unused keyword arguments.

        """
        for node in self.document.findall(nodes.system_message):
            message = node.children[0].children[0].astext()
            for regex, handler in unknown_handlers:
                match = regex.match(message)
                if match:
                    handler(match.group(1))
                    break


# noinspection PyPep8Naming
class inline_markup:
    """An inline markup block."""

    def __init__(self, text: str) -> None:
        """Initialize the inline markup block.

        :param text: The text content of the markup.

        """
        self.text = text


inline_item = str | inline_markup
inline_iterator = Iterator[inline_item]
line_iterator = Iterator[str]

word_info = namedtuple(  # noqa: PYI024
    "word_info",
    ["text", "in_markup", "start_space", "end_space", "start_punct", "end_punct"],
)


class FormatContext:
    """Context for formatting."""

    def __init__(
        self,
        width: int,
        current_file: Path | str,
        manager: Manager,
        black_config: Mode | None = None,
        **kwargs: Any,
    ):
        """Initialize the format context.

        :param width: Maximum line width.
        :param current_file: Path to the current file.
        :param manager: Manager instance.
        :param black_config: Black formatting configuration.
        :param kwargs: Additional keyword arguments.

        """
        self.width = width
        self.current_file = current_file
        self.manager = manager
        self.black_config = black_config
        self.starting_width = width
        self.bullet: str = ""
        self.column_widths = []
        self.current_ordinal = 0
        self.first_line_len: int = 0
        self.line_block_depth = 0
        self.ordinal_format = "arabic"
        self.section_depth = 0
        self.subsequent_indent = 0
        self.use_adornments = None
        self.is_docstring = False
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _replace(self, **kwargs: Any) -> FormatContext:
        """Return a copy of this context with some values replaced.

        :param kwargs: Keyword arguments to replace in the context.

        :returns: New FormatContext with replaced values.

        """
        current_context = copy(vars(self))
        for key, value in current_context.items():
            kwargs.setdefault(key, value)
        return self.__class__(**kwargs)

    def in_line_block(self) -> FormatContext:
        """Return a context for being in a line block.

        :returns: New FormatContext with incremented line block depth.

        """
        return self._replace(line_block_depth=self.line_block_depth + 1)

    def in_section(self) -> FormatContext:
        """Return a context for being in a section.

        :returns: New FormatContext with incremented section depth.

        """
        return self._replace(section_depth=self.section_depth + 1)

    def indent(self, spaces: int) -> FormatContext:
        """Return a context indented by the given number of spaces.

        :param spaces: Number of spaces to indent.

        :returns: New FormatContext with adjusted width.

        """
        return self._replace(width=max(1, self.width - spaces))

    def sub_indent(self, subsequent_indent: int) -> FormatContext:
        """Return a context with the given subsequent indent.

        :param subsequent_indent: Number of spaces for subsequent indent.

        :returns: New FormatContext with adjusted subsequent indent.

        """
        return self._replace(subsequent_indent=subsequent_indent)

    def with_bullet(self, bullet: str) -> FormatContext:
        """Return a context with the given bullet.

        :param bullet: Bullet character to use.

        :returns: New FormatContext with the specified bullet.

        """
        return self._replace(bullet=bullet)

    def with_column_widths(self, widths: list[int]) -> FormatContext:
        """Return a context with the given column widths.

        :param widths: List of column widths.

        :returns: New FormatContext with the specified column widths.

        """
        return self._replace(column_widths=widths)

    def with_ordinal(self, current_ordinal: int) -> FormatContext:
        """Return a context with the given current ordinal.

        :param current_ordinal: Current ordinal number.

        :returns: New FormatContext with the specified ordinal.

        """
        return self._replace(current_ordinal=current_ordinal)

    def with_ordinal_format(self, ordinal_format: str) -> FormatContext:
        """Return a context with the given ordinal format.

        :param ordinal_format: Format for ordinal numbers.

        :returns: New FormatContext with the specified ordinal format.

        """
        return self._replace(ordinal_format=ordinal_format)

    def with_width(self, width: int | None) -> FormatContext:
        """Return a context with the given width.

        :param width: Width for the context.

        :returns: New FormatContext with the specified width.

        """
        return self._replace(width=width)

    def wrap_first_at(self, width: int) -> FormatContext:
        """Return a context that wraps the first line at the given width.

        :param width: Width for the first line.

        :returns: New FormatContext with the specified first line width.

        """
        return self._replace(first_line_len=width)


@dataclass
class CodeFormatters:
    """Formatters for code blocks."""

    code: str
    context: FormatContext

    def python(self) -> str:
        """Format Python code.

        :returns: Formatted Python code.

        """
        if not self.context.manager.format_python_code_blocks:
            return self.code
        try:
            if self.context.black_config is not None:
                self.code = black.format_str(
                    self.code, mode=self.context.black_config
                ).rstrip()
        except (UserWarning, black.InvalidInput, TokenError):
            try:
                compile(self.code, "<code-block>", mode="exec")
            except SyntaxError as syntax_error:
                self.context.manager.error_count += 1
                document_line = self.context.manager.get_code_line(
                    self.code, strict=True
                ) - len(self.code.splitlines())
                if self.context.manager.reporter:
                    pointer = (
                        " " * (syntax_error.offset - 1) + "^"
                        if syntax_error.offset
                        else ""
                    )
                    self.context.manager.reporter.error(
                        f"SyntaxError: {syntax_error.msg}:\n\nFile"
                        f' "{self.context.current_file}", line'
                        f" {document_line + (syntax_error.lineno or 0)}:\n{syntax_error.text}\n{pointer}"
                    )
        return self.code

    def rst(self) -> str:
        """Format reStructuredText code.

        :returns: Formatted reStructuredText code.

        """
        manager = self.context.manager
        try:
            document = manager.parse_string(
                self.code, line_offset=manager.get_code_line(self.code) - 1
            )
            formatted = manager.format_node(
                self.context.width,
                document,
                is_docstring=False,
            )
            return formatted.rstrip()
        except InvalidRstErrors as errors:  # pragma: no cover
            manager.error_count += len(errors.errors)
            for error in errors.errors:
                if manager.reporter:
                    manager.reporter.error(str(error))
            return self.code


class Manager:
    """Manager for formatting reStructuredText."""

    def __init__(
        self,
        *,
        current_file: Path | str,
        black_config: Mode | None = None,
        docstring_trailing_line: bool = True,
        format_python_code_blocks: bool = True,
        reporter: Reporter | utils.Reporter | logging.Logger,
        section_adornments: list[tuple[str, bool]] | None = None,
    ):
        """Initialize the manager.

        :param current_file: The current file being processed.
        :param reporter: utils.Reporter instance for logging.
        :param black_config: Black formatting configuration.
        :param docstring_trailing_line: Whether to add trailing line to docstrings.
        :param format_python_code_blocks: Whether to format Python code blocks.
        :param section_adornments: Section adornment configuration.

        """
        rst_extras.register()
        self.current_file = current_file
        self.black_config = black_config
        self.current_offset = 0
        self.error_count = 0
        self.reporter = reporter
        self.settings = OptionParser(components=[rst.Parser]).get_default_values()
        self.settings.smart_quotes = True
        self.settings.report_level = 5
        self.settings.halt_level = 5
        self.settings.file_insertion_enabled = False
        self.settings.tab_width = 8
        self.formatters = Formatters(self)
        self.original_text = ""
        self.docstring_trailing_line = docstring_trailing_line
        self.format_python_code_blocks = format_python_code_blocks
        self._in_docstring = False  # for resolving line numbers in code blocks
        self.section_adornments = section_adornments

    def _patch_unknown_directives(self, text: str) -> None:
        """Patch unknown directives and roles into the parser.

        :param text: Text to parse for unknown directives.

        """
        doc = new_document(str(self.current_file), self.settings)
        parser = rst.Parser()
        doc.reporter = IgnoreMessagesReporter(
            "",
            utils.Reporter.SEVERE_LEVEL,
            utils.Reporter.SEVERE_LEVEL,
        )
        parser.parse(text, doc)
        doc.transformer.add_transform(UnknownNodeTransformer)
        doc.transformer.apply_transforms()

    def _pre_process(
        self,
        node: nodes.Node,
        line_offset: int,
        block_length: int,
    ) -> None:
        """Preprocess nodes.

        This does some preprocessing to all nodes that is generic across node types and
        is therefore most convenient to do as a simple recursive function rather than as
        part of the big dispatcher class.

        """
        # Strip all system_message nodes. (Just formatting them with no markup isn't enough, since that
        # could lead to extra spaces or empty lines between other elements.)
        errors = [
            child
            for child in node.children
            if isinstance(child, nodes.system_message)
            and child.attributes["type"] != "INFO"  # type: ignore[attr]
            and child.children[0].astext()
            not in IgnoreMessagesReporter.ignored_messages
        ]
        if errors:
            self.error_count += len(errors)
            raise InvalidRstErrors(
                [
                    InvalidRstError(
                        self.current_file,
                        error.attributes["type"],
                        (block_length - 1 if error.line is None else error.line)
                        + line_offset,
                        error.children[0].children[0].astext(),  # type: ignore[attr]
                    )
                    for error in errors
                ]
            )
        node.children = [
            child
            for child in node.children
            if not isinstance(child, nodes.system_message)
        ]

        # Match references to targets, which helps later with distinguishing whether they're anonymous.
        for reference, target in pairwise(node.children):
            if isinstance(reference, nodes.reference) and isinstance(
                target, nodes.target
            ):
                reference.attributes["target"] = target
        start = None
        for i, child in enumerate(itertools.chain(node.children, [None])):  # type: ignore[attr]
            in_run = start is not None
            is_target = isinstance(child, nodes.target)
            if in_run and not is_target:
                # Anonymous targets have a value of `[]` for "names", which will sort to the top. Also,
                # it's important here that `sorted` is stable, or anonymous targets could break.
                node.children[start:i] = sorted(  # type: ignore[arg-type]
                    node.children[start:i],
                    key=lambda t: t.attributes["names"],  # type: ignore[arg-type]
                )
                start = None
            elif not in_run and is_target:
                start = i

        # Recurse.
        for child in node.children:
            self._pre_process(child, line_offset, block_length)

    def format_node(
        self,
        width: int,
        node: nodes.Node,
        is_docstring: bool = False,
    ) -> str:
        """Format a node.

        :param width: Maximum line width for formatting.
        :param node: The node to format.
        :param is_docstring: Whether this is formatting a docstring.

        :returns: Formatted string representation of the node.

        """
        self._in_docstring = is_docstring
        formatted_node = "\n".join(
            self.perform_format(
                node,
                FormatContext(
                    width,
                    current_file=self.current_file,
                    manager=self,
                    black_config=self.black_config,
                    is_docstring=is_docstring,
                ),
            )
        )
        return f"{formatted_node}\n"

    @staticmethod
    def _register_adornments(input_lines: list[str], document: nodes.document) -> None:
        """Register adornments from source text on all individual sections.

        This method will parse the document tree and original text to-be-formatted, and
        will register, at the document tree, the current document configuration
        representing the adornments for parts, chapters and sections on each level of
        the document. In particular, it will install an attribute called
        ``adornment-character`` with the character used for underline or overlining the
        section, and ``adornment-overline``, if the section should be overlined or not.

        :param input_lines: The lines of input (split by newline), that we must format.
        :param document: The pre-parsed document tree, that will be modified with new
            section attributes as described above.

        """
        for section in document.findall(nodes.section):
            title_node = section.next_node(nodes.title)
            if (
                title_node
                and hasattr(title_node, "line")
                and title_node.line is not None
            ):
                underline = input_lines[title_node.line - 1].strip()[0]
                overline_lineno = title_node.line - 3
                overline = False

                if overline_lineno >= 0:
                    candidate_overline = input_lines[overline_lineno].strip()
                    if candidate_overline and candidate_overline[0] == underline:
                        overline = True

                # Store this information in the document tree
                section["adornment-character"] = underline
                section["adornment-overline"] = overline

    def get_code_line(self, code: str, strict: bool = False) -> int:
        """Get the line number of the code in the file.

        :param code: Code string to find.
        :param strict: Whether to use strict mode.

        :returns: Line number of the code in the file.

        :raises ValueError: If the code is not found.

        """
        lines = self.original_text.splitlines()
        code_lines = code.splitlines()
        multiple = len([line for line in lines if code_lines[0] in line]) > 1
        code_offset = self.current_offset - (1 if self._in_docstring else 0)
        for line_number, line in enumerate(lines, 1):  # noqa: RET503
            if line.endswith(code_lines[0]) if strict else code_lines[0] in line:
                if multiple:
                    current_offset = 0
                    for offset, sub_line in enumerate(code_lines):
                        current_offset = offset
                        if not (
                            lines[line_number - 1 + offset].endswith(sub_line)
                            if strict
                            else sub_line in lines[line_number - 1 + offset]
                        ):
                            break
                    else:
                        return line_number + current_offset + code_offset
                else:
                    return line_number + code_offset
        msg = f"Code not found in {self.current_file}:\n{code}"  # pragma: no cover
        raise ValueError(msg)  # pragma: no cover

    def parse_string(
        self,
        text: str,
        line_offset: int = 0,
        *,
        file: Path | str | None = None,
    ) -> nodes.document:
        """Parse a string of reStructuredText.

        :param file: Name of the file being parsed.
        :param text: Text content to parse.
        :param line_offset: Line offset for error reporting.

        :returns: Parsed document node.

        """
        if file:
            self.current_file = file
        self.current_offset = line_offset
        self.original_text = text
        self._patch_unknown_directives(text)
        doc = new_document(str(self.current_file), self.settings)
        parser = rst.Parser()
        doc.reporter = IgnoreMessagesReporter(
            "",
            self.settings.report_level,  # type: ignore[arg-type]
            self.settings.halt_level,  # type: ignore[arg-type]
        )
        parser.parse(text, doc)
        input_lines = text.splitlines()
        self._pre_process(doc, line_offset, len(input_lines))
        self._register_adornments(input_lines, doc)
        return doc

    def perform_format(
        self,
        node: nodes.Node,
        context: FormatContext,
    ) -> Iterator[str]:
        """Format a node.

        :param node: The node to format.
        :param context: Formatting context.

        :returns: Iterator of formatted lines.

        :raises ValueError: If the node type is unknown.

        """
        try:
            name = type(node).__name__
            func = getattr(self.formatters, NODE_MAPPING.get(name, name))
        except AttributeError:  # pragma: no cover
            msg = f'Unknown node type {type(node).__name__} at File "{context.current_file}", line {node.line}'
            raise ValueError(msg) from None
        return func(node, context)


def pairwise(items: Iterable[T]) -> Iterator[tuple[T, T]]:
    """Return pairs of adjacent items from the iterable.

    :param items: Iterable of items to pair.

    :returns: Iterator of adjacent item pairs.

    """
    a, b = itertools.tee(items)
    next(b, None)
    return zip(a, b, strict=False)


def _prepend_if_any(prefix: T, items: Iterator[T]) -> Iterator[T]:
    """Prepend a prefix if there are any items.

    :param prefix: Prefix to add to the first item.
    :param items: Iterator of items.

    :returns: Iterator with prefix prepended to first item if any items exist.

    """
    try:
        item = next(items)
    except StopIteration:
        return
    yield prefix
    yield item
    yield from items


def _with_spaces(space_count: int, lines: Iterable[str]) -> Iterator[str]:
    """Yield lines with the given number of leading spaces.

    :param space_count: Number of spaces to add.
    :param lines: Iterable of lines to indent.

    :returns: Iterator of indented lines.

    """
    spaces = " " * space_count
    for line in lines:
        yield spaces + line if line else line


class Formatters:
    """Formatters for reStructuredText nodes."""

    def __init__(self, manager: Manager):
        """Initialize the formatters.

        :param manager: Manager instance for formatting.

        """
        self.manager = manager

    def _format_children(
        self,
        node: nodes.Node,
        context: FormatContext,
    ) -> Iterator[Iterator[str]]:
        """Format the children of a node.

        :param node: The node whose children to format.
        :param context: Formatting context.

        :returns: Iterator of formatted child content.

        """
        return (
            (
                self.manager.perform_format(child, context)
                if index == 0
                else self.manager.perform_format(child, context.wrap_first_at(0))
            )
            for index, child in enumerate(node.children)  # type: ignore[attr]
        )

    def _generate_table_matrix(
        self,
        context: FormatContext,
        rows: list[nodes.Element],
        width: int | None,
        widths: dict[int, int] | None = None,
    ):
        """Generate a table matrix.

        :param context: Formatting context.
        :param rows: List of table rows.
        :param width: Overall table width.
        :param widths: Optional mapping of column widths.

        :returns: List of lists containing column widths for each row.

        """
        if widths:
            return [
                [
                    max(
                        [
                            len(line)
                            for child in self._format_children(
                                cell, context.with_width(width=widths[column_index])
                            )
                            for line in child
                        ]
                        or [0]
                    )
                    for column_index, cell in enumerate(row)
                ]
                for row in rows
            ]
        return [
            [
                max(
                    [
                        len(line)
                        for child in self._format_children(
                            cell, context.with_width(width=width)
                        )
                        for line in child
                    ]
                    or [0]
                )
                for cell in row
            ]
            for row in rows
        ]

    def _list(self, node: nodes.Node, context: FormatContext) -> line_iterator:
        """Format a list node.

        :param node: The list node to format.
        :param context: Formatting context.

        :returns: Iterator of formatted list lines.

        """
        sub_children = []
        for child_index, child in enumerate(node.children, 1):  # type: ignore[attr]
            sub_children.append(
                list(self.manager.perform_format(child, context))
                + (
                    [""]
                    if len(child.children) > 1 and len(node.children) != child_index  # type: ignore[attr]
                    else []
                )
            )

        yield from chain(sub_children)

    def _sub_admonition(
        self,
        node: nodes.admonition,
        context: FormatContext,
    ) -> line_iterator:
        """Format a sub-admonition node.

        Example:

        .. code-block:: rst

            .. note::

                This is a note admonition.

        """
        yield f".. {node.tagname}::"
        yield ""
        yield from _with_spaces(
            4,
            _chain_with_line_separator(
                "", self._format_children(node, context.indent(4))
            ),
        )

    def admonition(
        self,
        node: nodes.admonition,
        context: FormatContext,
    ) -> line_iterator:
        """Format an admonition node.

        Example:

        .. code-block:: rst

            .. admonition:: Custom Title

                This is a custom admonition with a title.

        """
        title = node.children[0]
        assert isinstance(title, nodes.title)
        yield (
            ".. admonition::"
            f" {''.join(_wrap_text(None, chain(self._format_children(title, context)), context, node.line))}"
        )
        yield ""
        context = context.indent(4)
        yield from _with_spaces(
            4,
            _chain_with_line_separator(
                "",
                (
                    self.manager.perform_format(child, context)
                    for child in node.children[1:]
                ),
            ),
        )

    def block_quote(
        self,
        node: nodes.block_quote,
        context: FormatContext,
    ) -> line_iterator:
        """Format a block quote node.

        :param node: The block quote node to format.
        :param context: Formatting context.

        :returns: Iterator of formatted block quote lines.

        Example:

        .. code-block:: rst

            This is a quote:

                Some quote

        """
        yield from _with_spaces(
            4,
            _chain_with_line_separator(
                "", self._format_children(node, context.indent(4))
            ),
        )

    def bullet_list(
        self,
        node: nodes.bullet_list,
        context: FormatContext,
    ) -> line_iterator:
        """Format a bullet list node.

        :param node: The bullet list node to format.
        :param context: Formatting context.

        :returns: Iterator of formatted bullet list lines.

        Example:

        .. code-block:: rst

            - First item
            - Second item
            - Third item

        """
        yield from self._list(node, context.with_bullet("-"))

    def comment(
        self,
        node: nodes.comment,
        context: FormatContext,
    ) -> line_iterator:
        """Format a comment node.

        Example:

        .. code-block:: rst

            ..
                This is a comment.
                It won't appear in the output.

        """
        if len(node.children) == 1:
            text = "\n".join(chain(self._format_children(node, context)))
            if "\n" not in text:
                yield f".. {text}"
                return

        yield ".."
        if node.children:
            text = "\n".join(chain(self._format_children(node, context)))
            yield from _with_spaces(4, text.splitlines())

    def definition(
        self,
        node: nodes.definition,
        context: FormatContext,
    ) -> line_iterator:
        """Format a definition node.

        Example:

        .. code-block:: rst

            term
                The definition of the term.

        """
        yield from _chain_with_line_separator("", self._format_children(node, context))

    def definition_list(
        self,
        node: nodes.definition_list,
        context: FormatContext,
    ) -> line_iterator:
        """Format a definition list node.

        Example:

        .. code-block:: rst

            term 1
                Definition 1.

            term 2
                Definition 2.

        """
        yield from _chain_with_line_separator("", self._format_children(node, context))

    def definition_list_item(
        self,
        node: nodes.definition_list_item,
        context: FormatContext,
    ) -> line_iterator:
        """Format a definition list item node.

        Example:

        .. code-block:: rst

            term
                The definition.

        """
        for child in node.children:
            if isinstance(child, nodes.term):
                yield from self.manager.perform_format(child, context)
            elif isinstance(child, nodes.definition):
                yield from _with_spaces(
                    4, self.manager.perform_format(child, context.indent(4))
                )

    def directive(
        self, node: rst_extras.directive, context: FormatContext
    ) -> line_iterator:
        """Format a directive node.

        Example:

        .. code-block:: rst

            .. note::

                This is a note directive.

        """
        attributes = node.attributes
        directive = attributes["directive"]
        is_code_block = directive.name in ["code", "code-block", "sourcecode"]
        in_substitution = isinstance(node.parent, nodes.substitution_definition)
        parts = [
            f".. {'code-block' if is_code_block else directive.name}::",
            *directive.arguments,
        ]
        if in_substitution:
            del parts[0]  # No need for the leading .. or the image:: part

        yield " ".join(parts)
        # Just rely on the order being stable, hopefully.
        leading_space = "" if in_substitution else " " * 4
        for k, v in directive.options.items():
            yield f"{leading_space}:{k}:" if v is None else f"{leading_space}:{k}: {v}"

        if is_code_block:
            text = "\n".join(directive.content.data)
            if directive.arguments:
                language = directive.arguments[0]
                try:
                    func = getattr(CodeFormatters(text, context), language)
                    text = func()
                except (AttributeError, TypeError):
                    pass
            yield ""
            yield from _with_spaces(4, text.splitlines())
        elif directive.raw:
            yield from _prepend_if_any("", _with_spaces(4, directive.content))
        else:
            sub_doc = self.manager.parse_string(
                "\n".join(directive.content),
                self.manager.current_offset + directive.content_offset,
                file=context.current_file,
            )
            if sub_doc.children:
                yield ""
                yield from _with_spaces(
                    4, self.manager.perform_format(sub_doc, context.indent(4))
                )

    def doctest_block(
        self,
        node: nodes.doctest_block,
        context: FormatContext,
    ) -> line_iterator:
        """Format a doctest block.

        Example:

        .. code-block:: rst

            >>> print("Hello")
            Hello
            >>> 1 + 1
            2

        """
        code = node.children[0].astext()
        parser = DocTestParser()
        try:
            parsed = parser.get_examples(code)
        except ValueError as e:
            raise InvalidRstError(
                context.current_file,
                "ERROR",
                self.manager.get_code_line(code, strict=True),
                f"Invalid doctest block: {e}",
            ) from None
        doctest_blocks = []
        for example in parsed:
            formatted = CodeFormatters(example.source.strip(), context).python()
            doctest_blocks.append((formatted, example.want.strip()))

        if not doctest_blocks:
            raise InvalidRstError(
                context.current_file,
                "ERROR",
                self.manager.get_code_line(code[0], strict=True),
                "Empty doctest block.",
            )
        for formatted, want in doctest_blocks:
            first_line, *other_lines = formatted.splitlines()
            yield f">>> {first_line}"
            for line in other_lines:
                yield f"... {line}" if line else "..."
            if want:
                yield from want.splitlines()

    def document(
        self,
        node: nodes.document,
        context: FormatContext,
    ) -> line_iterator:
        """Format a document node.

        Example:

        .. code-block:: rst

            The entire document content.

        """
        yield from _chain_with_line_separator("", self._format_children(node, context))

    def emphasis(
        self,
        node: nodes.emphasis,
        context: FormatContext,
    ) -> inline_iterator:
        """Format an emphasis node.

        Example:

        .. code-block:: rst

            This is *emphasized* text.

        """
        joined = "".join(chain(self._format_children(node, context))).replace(
            "*", "\\*"
        )
        yield inline_markup(f"*{joined}*")

    def enumerated_list(
        self,
        node: nodes.enumerated_list,
        context: FormatContext,
    ) -> line_iterator:
        """Format an enumerated list node.

        Example:

        .. code-block:: rst

            1. First item
            2. Second item
            3. Third item

        """
        yield from self._list(
            node,
            context.with_ordinal(node.attributes.get("start", 1)).with_ordinal_format(
                node.attributes["enumtype"]
            ),
        )
        context.current_ordinal = 0

    def field(
        self,
        node: nodes.field,
        context: FormatContext,
    ) -> line_iterator:
        """Format a field node.

        Example:

        .. code-block:: rst

            :nosearch:

        """
        children = chain(self._format_children(node, context))
        field_name = next(children)
        is_empty_sphinx_metadata_field = field_name.startswith(
            (":nocomments", ":nosearch", ":orphan")
        )
        try:
            first_line = next(children)
            if first_line and is_empty_sphinx_metadata_field:
                raise InvalidRstError(
                    context.current_file,
                    "ERROR",
                    self.manager.get_code_line(field_name),
                    f"Non-empty Sphinx `{field_name}` metadata"
                    " field. Please remove field body or omit completely.",
                )
        except StopIteration:
            if is_empty_sphinx_metadata_field:
                yield from chain(self._format_children(node, context))
                return
            raise InvalidRstError(
                context.current_file,
                "ERROR",
                self.manager.get_code_line(f":{node.astext().strip()}:", strict=True),
                f"Empty `:{node.astext().strip()}:` field. Please add a field body or"
                " omit completely.",
            ) from None

        children = list(children)
        children_processed = []
        for i, child in enumerate(children):
            if child.startswith(".."):
                blocks_in_child = [child]
                for block in children[i + 1 :]:
                    if block.startswith("    ") or block == "":
                        blocks_in_child.append(block)
                    else:  # pragma: no cover
                        break
                del children[i : i + len(blocks_in_child) - 1]
                if blocks_in_child[-1] != "":
                    blocks_in_child.append("")
                children_processed += blocks_in_child
            else:
                children_processed.append(child)
        children = children_processed
        yield f"{field_name} {first_line}"
        yield from _with_spaces(4, children)

    def field_body(
        self,
        node: nodes.field_body,
        context: FormatContext,
    ) -> line_iterator:
        """Format a field body node.

        Example:

        .. code-block:: rst

            Description of the field.

        """
        yield from _chain_with_line_separator(
            "",
            self._format_children(
                node,
                context.indent(4).wrap_first_at(
                    len(f":{node.parent.children[0].astext()}: ") - 4
                ),
            ),
        )

    def field_list(
        self,
        node: nodes.field_list,
        context: FormatContext,
    ) -> line_iterator:
        """Format a field list node.

        Example:

        .. code-block:: rst

            :param node: The node parameter.
            :param context: Format context.

            :returns: Return value description.

        """
        param_fields = []
        param_types = {}
        var_fields = []
        var_types = {}
        returns_fields = []
        rtype_fields = []
        raises_fields = []
        other_fields = []
        field_types_mapping = {
            "param": param_fields,
            "var": var_fields,
            "returns": returns_fields,
            "rtype": rtype_fields,
            "raises": raises_fields,
        }
        field_name_mapping = {
            "arg": "param",
            "argument": "param",
            "key": "param",
            "keyword": "param",
            "param": "param",
            "parameter": "param",
            "return": "returns",
            "returns": "returns",
            "except": "raises",
            "exception": "raises",
            "raise": "raises",
            "raises": "raises",
            "cvar": "var",
            "ivar": "var",
            "var": "var",
        }
        already_typed = []
        children = node.children
        for child in children[:]:
            field_name_node = cast("nodes.field_name", child.children[0])  # type: ignore[index]
            field_body = field_name_node.children[0].astext()
            try:
                field_kind, *field_typing, field_name = field_body.split(" ")
            except ValueError:
                field_kind = field_body.split(" ")[0]
                field_typing = []
                field_name = None
            new_field_kind = field_name_mapping.get(field_kind, field_kind)
            if field_kind != new_field_kind:
                to_join = [new_field_kind, *field_typing]
                if field_name:
                    to_join.append(field_name)
                field_name_node.replace_self(nodes.field_name("", " ".join(to_join)))
                field_kind = new_field_kind
            field_name_node.setdefault("name", field_name)
            if field_kind in ["type", "vartype"]:
                field_type = child.children[1].children[0].astext()  # type: ignore[index]
                if "\n" in field_type:
                    raise InvalidRstError(
                        context.current_file,
                        "ERROR",
                        self.manager.get_code_line(field_type),
                        "Multi-line type hints are not supported.",
                    )
                if field_kind == "type":
                    param_types[field_name] = field_type
                if field_kind == "vartype":
                    var_types[field_name] = field_type
                node.remove(child)
                continue
            if field_typing:
                already_typed.append(field_name)
            if field_kind in field_types_mapping:
                if field_kind.startswith("return") and returns_fields:
                    raise InvalidRstError(
                        context.current_file,
                        "ERROR",
                        self.manager.get_code_line(child.astext()),
                        "Multiple `:return:` fields are not allowed. Please"
                        " combine them into one.",
                    )
                field_types_mapping[field_kind].append(child)
            else:
                other_fields.append(child)
        for fields, types, type_field_name, field_type in [
            (param_fields, param_types, "type", "param"),
            (var_fields, var_types, "vartype", "var"),
        ]:
            for field in fields:
                field_name = field.children[0].get("name")
                if field_name in already_typed and field_name in types:
                    raise InvalidRstError(
                        context.current_file,
                        "ERROR",
                        self.manager.get_code_line(field.astext()),
                        "Type hint is specified both in the field body and in the"
                        f" `:{type_field_name}:` field. Please remove one of them.",
                    )
                else:
                    field_typing = types.get(field_name, [])
                    if field_typing:
                        field.children[0].replace_self(
                            nodes.field_name(
                                "", f"{field_type} {field_typing} {field_name}"
                            )
                        )
        yield from chain(
            self.manager.perform_format(child, context) for child in param_fields
        )
        previous_fields = param_fields
        if (
            previous_fields
            and returns_fields
            + rtype_fields
            + raises_fields
            + var_fields
            + other_fields
        ):
            yield ""
        yield from chain(
            self.manager.perform_format(child, context)
            for child in returns_fields + rtype_fields
        )
        previous_fields = returns_fields + rtype_fields
        if previous_fields and raises_fields + var_fields + other_fields:
            yield ""
        yield from chain(
            self.manager.perform_format(child, context) for child in raises_fields
        )
        previous_fields = raises_fields
        if previous_fields and var_fields + other_fields:
            yield ""
        yield from chain(
            self.manager.perform_format(child, context) for child in var_fields
        )
        previous_fields = var_fields
        if previous_fields and other_fields:
            yield ""
        yield from chain(
            self.manager.perform_format(child, context) for child in other_fields
        )

    def field_name(
        self,
        node: nodes.field_name,
        context: FormatContext,
    ) -> line_iterator:
        """Format a field name node.

        Example:

        .. code-block:: rst

            :param node: The node parameter.
            :param context: Format context.

        """
        text = " ".join(chain(self._format_children(node, context)))
        body = ":"
        field_kinds = [
            "param",
            "raise",
            "return",
        ]
        for field_kind in field_kinds:
            if text.startswith(field_kind):
                field_kind, *_ = text.split(" ", maxsplit=1)  # noqa: PLW2901
                body += field_kind
                text = text[len(field_kind) :]
                break
        body += text
        body += ":"
        yield body

    def footnote(self, node: nodes.footnote_reference, context: FormatContext):
        """Format a footnote node.

        Example:

        .. code-block:: rst

            .. [1] This is a footnote.

        """
        prefix = ".."
        children = _wrap_text(
            (context.width - 4 if context.width is not None else None),
            chain(self._format_children(node, context.indent(4))),
            context.wrap_first_at(len(prefix) - 4).indent(4),
            node.line,
        )
        footnote_name = (
            [f"[#{''.join(node.attributes['names'])}]"]
            if node.attributes.get("auto", False)
            else []
        )
        child = next(children)
        yield " ".join([prefix, *footnote_name, child])
        remaining = list(children)
        if remaining:
            yield from _with_spaces(4, remaining)

    citation = footnote

    @staticmethod
    def footnote_reference(
        node: nodes.footnote_reference,
        _: FormatContext,
    ):
        """Format a footnote reference node.

        Example:

        .. code-block:: rst

            This is a reference [1]_ to a footnote.

        """
        footnote_name = "#" if node.attributes.get("auto", False) else ""
        yield inline_markup(f"[{footnote_name}{node.attributes.get('refname', '')}]_")

    citation_reference = footnote_reference

    def inline(
        self,
        node: nodes.inline,
        context: FormatContext,
    ) -> inline_iterator:
        """Format an inline node.

        :param node: The inline node to format.
        :param context: Formatting context.

        :returns: Iterator of formatted inline content.

        Example:

        .. code-block:: rst

            This is inline content.

        """
        yield from chain(self._format_children(node, context))  # pragma: no cover

    def label(self, node: nodes.footnote_reference, context: FormatContext):
        """Format a label node.

        :param node: The label node to format.
        :param context: Formatting context.

        :returns: Formatted label string.

        Example:

        .. code-block:: rst

            [label]

        """
        yield f"[{' '.join(chain(self._format_children(node, context)))}]"

    def line(self, node: nodes.line, context: FormatContext) -> line_iterator:
        """Format a line node.

        Example:

        .. code-block:: rst

            |   This is a line
            |   in a line block.

        """
        if not node.children:
            yield "|"
            return

        indent = 4 * context.line_block_depth
        context = context.indent(indent)
        prefix1 = f"|{' ' * (indent - 1)}"
        prefix2 = " " * indent
        for first, line in _enum_first(
            _wrap_text(
                context.width,
                chain(self._format_children(node, context)),
                context,
                node.line,
            )
        ):
            yield (prefix1 if first else prefix2) + line

    def line_block(
        self,
        node: nodes.line_block,
        context: FormatContext,
    ) -> line_iterator:
        """Format a line block node.

        Example:

        .. code-block:: rst

            |   Line one
            |   Line two
            |   Line three

        """
        yield from chain(self._format_children(node, context.in_line_block()))

    def list_item(
        self,
        node: nodes.list_item,
        context: FormatContext,
    ) -> line_iterator:
        """Format a list item node.

        Example:

        .. code-block:: rst

            - This is a list item.

        """
        if not node.children:  # pragma: no cover
            yield "-"  # no idea why this isn't covered anymore
            return
        if context.current_ordinal and context.bullet not in ["-", "*", "+"]:
            context.bullet = make_enumerator(
                context.current_ordinal, context.ordinal_format, ("", ".")
            )
            context.current_ordinal += 1
        width = len(context.bullet) + 1
        bullet = f"{context.bullet} "
        spaces = " " * width
        context = context.indent(width)
        context.bullet = ""
        for first, child in _enum_first(
            _chain_with_line_separator("", self._format_children(node, context))
        ):
            yield ((bullet if first else spaces) if child else "") + child

    def literal(
        self,
        node: nodes.literal,
        context: FormatContext,
    ) -> inline_iterator:
        """Format a literal node.

        Example:

        .. code-block:: rst

            This is ``literal`` text.

        """
        yield inline_markup(
            f"``{''.join(chain(self._format_children(node, context)))}``"
        )

    @staticmethod
    def literal_block(
        node: nodes.literal_block,
        context: FormatContext,
    ) -> line_iterator:
        """Format a literal block node.

        Example:

        .. code-block:: rst

            ::

                This is a literal block
                with preformatted text.

            .. code-block:: python

                print("Hello, world!")

        """
        if len(node.attributes["classes"]) > 1 and node.attributes["classes"][0] in [
            "code",
            "code-block",
        ]:
            args = "".join([f" {arg}" for arg in node.attributes["classes"][1:]])
            yield f".. code-block::{args}"
            language = node.attributes["classes"][1]
            text = node.rawsource
            try:
                func = getattr(CodeFormatters(text, context), language)
                text = func()
            except (AttributeError, TypeError):
                pass
            yield ""
            yield from _with_spaces(4, text.splitlines())
            return
        else:
            yield "::"
        yield from _prepend_if_any("", _with_spaces(4, node.rawsource.splitlines()))

    def paragraph(
        self,
        node: nodes.paragraph,
        context: FormatContext,
    ) -> line_iterator:
        """Format a paragraph node.

        :param node: The paragraph node to format.
        :param context: Formatting context.

        :returns: Iterator of formatted paragraph lines.

        Example:

        .. code-block:: rst

            This is a paragraph of text that will be wrapped according to the line length
            settings.

        """
        wrap_text_context = context.sub_indent(context.subsequent_indent)
        if context.is_docstring:
            context.is_docstring = False
            wrap_text_context.is_docstring = False
            context = context.with_width(None)
        yield from _wrap_text(
            context.width,
            chain(
                self._format_children(
                    node, context.sub_indent(context.subsequent_indent)
                )
            ),
            wrap_text_context,
            node.line,
        )

    def pending(
        self,
        node: nodes.pending,
        context: FormatContext,
    ) -> inline_iterator:  # pragma: no cover
        """Format a pending node.

        :raises NotImplementedError: Always raised as pending nodes are not supported.

        """
        msg = f'Unknown node found at File "{context.current_file}", line {node.line}'
        raise NotImplementedError(msg)

    def problematic(
        self,
        node: nodes.problematic,
        context: FormatContext,
    ) -> line_iterator:  # pragma: no cover
        """Format a problematic node.

        :param node: The problematic node to format.
        :param context: Formatting context.

        :returns: Iterator of formatted lines.

        """
        yield from chain(self._format_children(node, context))

    @staticmethod
    def ref_role(
        node: rst_extras.ref_role,
        _: FormatContext,
    ) -> inline_iterator:
        """Format a ref_role node.

        Example:

        .. code-block:: rst

            :ref:`Link text <target>`

        """
        attributes = node.attributes
        target = attributes["target"]
        if attributes["has_explicit_title"]:
            title = attributes["title"].replace("<", r"\<")
            title = title.replace("`", r"\`")
            text = f"{title} <{target}>"
        else:
            text = target
        yield inline_markup(f":{attributes['name']}:`{text}`")

    def reference(
        self,
        node: nodes.reference,
        context: FormatContext,
    ) -> inline_iterator:
        """Format a reference node.

        Example:

        .. code-block:: rst

            `Link text <https://example.com>`_

        """
        title = " ".join(
            _wrap_text(
                None, chain(self._format_children(node, context)), context, node.line
            )
        )

        def anonymous_suffix(is_anonymous: bool) -> str:
            return "__" if is_anonymous else "_"

        attributes = node.attributes
        children = node.children

        # Handle references that are also substitution references.
        if len(children) == 1 and isinstance(children[0], nodes.substitution_reference):
            anonymous = bool(attributes.get("anonymous"))
            yield inline_markup(title + anonymous_suffix(anonymous))
            return

        # Handle references to external URIs. They can be either standalone hyperlinks,
        # written as just the URI, or an explicit "`text <url>`_" or "`text <url>`__".
        if "refuri" in attributes:
            uri = attributes["refuri"]
            if uri in (title, f"mailto:{title}"):
                yield inline_markup(title)
            else:
                anonymous = "target" not in attributes
                yield inline_markup(f"`{title} <{uri}>`{anonymous_suffix(anonymous)}")
            return

        # Simple reference names can consist of "alphanumerics plus isolated (no two
        # adjacent) internal hyphens, underscores, periods, colons and plus signs",
        # according to
        # https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#reference-names.
        is_single_word = valid_reference_id.match(
            title
        ) and not invalid_reference_id.search(title)

        # "x__" is one of the few cases to trigger an explicit "anonymous" attribute
        # (the other being the similar "|x|__", which is already handled above).
        if "anonymous" in attributes:
            if not is_single_word:
                title = f"`{title}`"
            yield inline_markup(title + anonymous_suffix(True))
            return

        anonymous = "target" not in attributes
        ref = attributes["refname"]
        # Check whether the reference name matches the text and can be made implicit.
        # (Reference names are case-insensitive.)
        if anonymous and ref.lower() == title.lower():
            if not is_single_word:
                title = f"`{title}`"
            # "x_" is equivalent to "`x <x_>`__"; it's anonymous despite having a single
            # underscore.
            yield inline_markup(title + anonymous_suffix(False))
        else:
            yield inline_markup(f"`{title} <{ref}_>`{anonymous_suffix(anonymous)}")

    @staticmethod
    def role(
        node: rst_extras.role,
        _: FormatContext,
    ) -> inline_iterator:
        """Format a role node.

        Example:

        .. code-block:: rst

            :guilabel:`Button Text`

        """
        yield inline_markup(f":{node.attributes['role']}:`{node.attributes['text']}`")

    def row(self, node: nodes.row, context: FormatContext) -> line_iterator:
        """Format a table row node.

        Example:

        .. code-block:: rst

            ===== =====
            Cell1 Cell2
            ===== =====

        """
        all_lines = [
            _chain_with_line_separator(
                "", self._format_children(entry, context.with_width(width))
            )
            for entry, width in zip(node.children, context.column_widths, strict=False)
        ]
        for line_group in itertools.zip_longest(*all_lines):  # type: ignore[arg-type]
            yield " ".join(
                (line or "").ljust(width)
                for line, width in zip(line_group, context.column_widths, strict=False)
            )

    def section(
        self,
        node: nodes.section,
        context: FormatContext,
    ) -> line_iterator:
        """Format a section node.

        Example:

        .. code-block:: rst

            ###############
             Section Title
            ###############

            Section content.

        """
        yield from _chain_with_line_separator(
            "", self._format_children(node, context.in_section())
        )

    def strong(
        self,
        node: nodes.strong,
        context: FormatContext,
    ) -> inline_iterator:
        """Format a strong node.

        Example:

        .. code-block:: rst

            This is **bold** text.

        """
        joined = "".join(chain(self._format_children(node, context))).replace(
            "*", "\\*"
        )
        yield inline_markup(f"**{joined}**")

    def substitution_definition(
        self,
        node: nodes.substitution_definition,
        context: FormatContext,
    ) -> line_iterator:
        """Format a substitution definition node.

        Example:

        .. code-block:: rst

            .. |name| replace:: replacement text

        """
        elements = node.rawsource.split("|")
        target = elements[1]
        directive = elements[2].strip().split("::")[0]
        prefix = f".. |{target}| {directive}::"
        if node.children and node.children[0].tagname == "directive":  # type: ignore[attr-defined]
            body = node.children[0]
            _directive = body.attributes["directive"]  # type: ignore[attr-defined]
            if _directive.options.get("alt") == node.attributes["names"][0]:
                del _directive.options["alt"]
        if directive in ["image", "unicode"]:
            children = chain(self._format_children(node, context.indent(4)))
        else:  # for date and replace
            children = _wrap_text(
                (context.width - 4 if context.width is not None else None),
                chain(self._format_children(node, context.indent(4))),
                context.wrap_first_at(len(prefix) - 4).indent(4),
                node.line,
            )
        next_child = next(children)
        yield f"{prefix} {next_child}"
        remaining = list(children)
        if remaining:
            yield from _with_spaces(4, remaining)

    def substitution_reference(
        self,
        node: nodes.substitution_reference,
        context: FormatContext,
    ) -> inline_iterator:
        """Format a substitution reference node.

        Example:

        .. code-block:: rst

            |name|

        """
        child = chain(self._format_children(node, context))
        yield inline_markup(f"|{''.join(child)}|")

    def table(
        self,
        node: nodes.table,
        context: FormatContext,
    ) -> line_iterator:
        """Format a table node.

        Example:

        .. code-block:: rst

            ===== =====
            Col 1 Col 2
            ===== =====
            Data1 Data2
            ===== =====

        """
        rows = []
        rows_to_check = []
        for row in node.findall(nodes.row):
            rows_to_check.append(row)

        for row in rows_to_check:
            for table in list(row.findall(nodes.table)):
                for sub_row in table.findall(nodes.row):
                    if sub_row in rows_to_check:
                        rows_to_check.remove(sub_row)
        for row in rows_to_check:
            current_row = []
            for column in row.findall(nodes.entry):
                if column.attributes.get("morerows", False) or column.attributes.get(
                    "morecols", False
                ):
                    msg = (
                        "Tables with cells that span multiple cells are not supported."
                        " Consider using the 'include' directive to include the table"
                        " from another file."
                    )
                    raise NotImplementedError(msg)
                current_row.append(column)
            for table in list(row.findall(nodes.table)):
                for entry in table.findall(nodes.entry):
                    if entry in current_row:
                        current_row.remove(entry)
            rows.append(current_row)

        column_count = len(rows[0])
        total_width = context.width - column_count + 1

        nested_column_count = len(list(node.findall(nodes.tgroup)))
        table_matrix_min = self._generate_table_matrix(
            context, rows, (nested_column_count * 2) - 1
        )
        table_matrix_max = self._generate_table_matrix(context, rows, total_width)
        min_col_len = {
            col_index: max([row[col_index] for row in table_matrix_min])
            for col_index in range(column_count)
        }
        max_col_len = {
            col_index: max([row[col_index] for row in table_matrix_max])
            for col_index in range(column_count)
        }
        column_lengths = {}
        current_width = 0
        if total_width is None or sum(max_col_len.values()) <= total_width:
            final_widths = [
                max(
                    self._generate_table_matrix(context, rows, 1, max_col_len),
                    key=lambda lengths: lengths[i],
                )[i]
                for i in range(column_count)
            ]
            context = context.with_column_widths(final_widths)
        else:
            for column_progress, column_info in enumerate(
                sorted(max_col_len.items(), key=lambda item: item[1])
            ):
                column_index, column_width = column_info
                if column_index not in column_lengths:
                    if (current_width + column_width) <= total_width:
                        current_width += column_width
                        column_lengths[column_index] = column_width
                    else:
                        proposed_column_length = _divide_evenly(
                            total_width - current_width, column_count - column_progress
                        ).pop()
                        if (column_width < proposed_column_length) or (
                            column_width < 25
                        ):
                            column_lengths[column_index] = column_width
                        elif proposed_column_length >= min_col_len[column_index]:
                            if proposed_column_length < 25:
                                column_lengths[column_index] = 25
                            else:
                                column_lengths[column_index] = proposed_column_length
                        else:
                            column_lengths[column_index] = column_width
            final_widths = [
                max(
                    self._generate_table_matrix(context, rows, None, column_lengths),
                    key=lambda lengths: lengths[i],
                )[i]
                for i in range(column_count)
            ]
            context = context.with_column_widths(final_widths)
        yield from [
            line.rstrip(" ")
            for line in _chain_with_line_separator(
                "", self._format_children(node, context)
            )
        ]

    @staticmethod
    def target(
        node: nodes.target,
        _: FormatContext,
    ) -> line_iterator:
        """Format a target node.

        Example:

        .. code-block:: rst

            .. _target-name: https://example.com

        """
        if not isinstance(node.parent, (nodes.document, nodes.section)):
            return
        try:
            body = f" {node.attributes['refuri']}"
        except KeyError:
            body = (
                f" {node.attributes['refname']}_"
                if "refname" in node.attributes
                else ""
            )

        name = "_" if node.attributes.get("anonymous") else node.attributes["names"][0]
        yield f".. _{name}:{body}"

    def tbody(
        self,
        node: nodes.tbody,
        context: FormatContext,
    ) -> line_iterator:
        """Format a table body node.

        Example:

        .. code-block:: rst

            Table body rows.

        """
        yield from chain(self._format_children(node, context))

    thead = tbody

    def term(self, node: nodes.term, context: FormatContext) -> line_iterator:
        """Format a term node.

        Example:

        .. code-block:: rst

            term
                Definition.

        """
        yield " ".join(
            _wrap_text(
                None, chain(self._format_children(node, context)), context, node.line
            )
        )

    @staticmethod
    def text(node: nodes.Text, _: FormatContext) -> inline_iterator:
        """Format a text node.

        Example:

        .. code-block:: rst

            Plain text content.

        """
        yield unescape(node, restore_backslashes=True).replace(r"\ ", "")

    def tgroup(
        self,
        node: nodes.tgroup,
        context: FormatContext,
    ) -> line_iterator:
        """Format a table group node.

        Example:

        .. code-block:: rst

            ===== =====
            Col1  Col2
            ===== =====
            Data1 Data2
            ===== =====

        """
        sep = " ".join("=" * width for width in context.column_widths)
        yield sep
        for child in node.children:
            if isinstance(child, nodes.colspec):
                continue
            if isinstance(child, nodes.thead):
                yield from self.manager.perform_format(child, context)
                yield " ".join("=" * width for width in context.column_widths)
            if isinstance(child, nodes.tbody):
                yield from self.manager.perform_format(child, context)
                yield sep

    def title(
        self,
        node: nodes.title,
        context: FormatContext,
    ) -> line_iterator:
        """Format a title node.

        Example:

        .. code-block:: rst

            ###############
             Section Title
            ###############

        """
        text = " ".join(
            _wrap_text(
                None, chain(self._format_children(node, context)), context, node.line
            )
        )
        char: str = node.parent["adornment-character"]
        overline: bool = node.parent["adornment-overline"]
        if context.manager.section_adornments is not None:
            try:
                char, overline = context.manager.section_adornments[
                    context.section_depth - 1
                ]
            except IndexError:
                context.manager.reporter.error(
                    f"Section at line {node.line} is at depth "
                    f"{context.section_depth}, however there are only "
                    f"{len(context.manager.section_adornments)} adornments to pick "
                    "from. You must review your inputs or change settings."
                )
                raise

        if overline:
            # section headings with overline are centered
            yield char * (2 + len(text))
            yield " " + text
            yield char * (2 + len(text))
        else:
            # sections headings without overline are justified
            yield text
            yield char * len(text)

    def title_reference(
        self,
        node: nodes.title_reference,
        context: FormatContext,
    ) -> inline_iterator:
        """Format a title reference node.

        Example:

        .. code-block:: rst

            `Title Reference`

        """
        yield inline_markup(f"`{''.join(chain(self._format_children(node, context)))}`")

    @staticmethod
    def transition(
        _: nodes.transition,
        __: FormatContext,
    ) -> line_iterator:
        """Format a transition node.

        Example:

        .. code-block:: rst

            Some text before the transition.

            ----

            Some text after the transition.

        """
        yield "----"


def _chain_with_line_separator(
    separator: T,
    items: Iterable[Iterable[T]],
) -> Iterator[T]:
    """Chain items with a separator between them.

    :param separator: Separator to insert between items.
    :param items: Iterable of iterables to chain.

    :returns: Iterator of chained items with separators.

    """
    first = True
    for item in items:
        if not first:
            yield separator
        first = False
        yield from item


def _divide_evenly(width: int, column_count: int) -> list[int]:
    """Divide width evenly among column_count columns.

    :param width: Total width to divide.
    :param column_count: Number of columns.

    :returns: List of widths for each column.

    """
    evenly = [floor(width / column_count)] * column_count
    for i in range(width % column_count):
        evenly[-1 - i] += 1
    return evenly


def _enum_first(items: Iterable[T]) -> Iterator[tuple[bool, T]]:
    """Yield items with a boolean indicating if it's the first item.

    :param items: Iterable of items to process.

    :returns: Iterator of tuples (is_first, item).

    """
    return zip(itertools.chain([True], itertools.repeat(False)), items, strict=False)


def _wrap_text(
    width: int | None,
    items: Iterable[inline_item],
    context: FormatContext,
    current_line: int | None,
) -> Iterator[str]:
    """Wrap text to the given width.

    Example:

    .. code-block:: rst

        Wraps inline text content to fit within the specified line width.

    """
    if width is not None and width <= 0:
        msg = f'Invalid starting width {context.starting_width} in File "{context.current_file}", line {current_line or "unknown"}'
        raise ValueError(msg)
    raw_words = []
    for item in list(items):
        new_words = []
        if isinstance(item, str):
            if not item:  # pragma: no cover
                # An empty string is treated as having trailing punctuation: it only
                # shows up when two inline markup blocks are separated by
                # backslash-space, and this means that after it is merged with its
                # predecessor the resulting word will not cause a second escape to
                # be introduced when merging with the successor.
                new_words = [word_info(item, False, False, False, False, True)]
            else:
                new_words = [
                    word_info(word, False, False, False, False, False)
                    for word in item.split()
                ]
                if item:
                    if not new_words:
                        new_words = [word_info("", False, True, True, True, True)]
                    if item[0] in space_chars:
                        new_words[0] = new_words[0]._replace(start_space=True)
                    if item[-1] in space_chars:
                        new_words[-1] = new_words[-1]._replace(end_space=True)
                    if item[0] in post_markup_break_chars:
                        new_words[0] = new_words[0]._replace(start_punct=True)
                    if item[-1] in pre_markup_break_chars:
                        new_words[-1] = new_words[-1]._replace(end_punct=True)
        elif isinstance(item, inline_markup):
            new_words = [
                word_info(word, True, False, False, False, False)
                for word in item.text.split()
            ]
        raw_words.append(new_words)
    raw_words = list(chain(raw_words))
    words = [word_info("", False, True, True, True, True)]
    for word in raw_words:
        last = words[-1]
        if not last.in_markup and word.in_markup and not last.end_space:
            join = "" if last.end_punct else r"\ "
            words[-1] = word_info(
                last.text + join + word.text, True, False, False, False, False
            )
        elif last.in_markup and not word.in_markup and not word.start_space:
            join = "" if word.start_punct else r"\ "
            words[-1] = word_info(
                last.text + join + word.text,
                False,
                False,
                word.end_space,
                word.start_punct,
                word.end_punct,
            )
        else:
            words.append(word)

    word_strings = (word.text for word in words if word.text)

    if width is None:
        yield " ".join(word_strings)
        return

    words = []
    current_line_length = 0
    if context.first_line_len:
        width -= context.first_line_len
    for word in word_strings:
        next_line_len = (
            current_line_length
            + (context.subsequent_indent if bool(words) else 0)
            + bool(words)
            + len(word)
        )
        if words and next_line_len > width:
            yield " " * context.subsequent_indent + " ".join(words)
            if context.first_line_len:
                width += context.first_line_len
                context.first_line_len = 0
            words = []
            next_line_len = len(word)
        words.append(word)
        current_line_length = next_line_len
    if words:
        yield " ".join(words)
