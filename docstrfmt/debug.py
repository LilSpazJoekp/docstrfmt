"""Debugging utilities for docstrfmt."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

from docutils import nodes


def _dump_lines(node: nodes.Node) -> Iterator[tuple[int, str]]:
    """Dump a docutils node to a list of strings.

    :param node: The docutils node to dump.

    :returns: Iterator of (indent level, line content) tuples.

    """
    node_type = type(node).__name__
    head = f"- \x1b[34m{node_type}\x1b[m"
    if isinstance(node, nodes.Text):
        body = repr(node.astext()[:100])
    else:
        body = str({k: v for k, v in node.attributes.items() if v})  # type: ignore[misc]
    yield 0, f"{head} {body}"
    for c in node.children:  # type: ignore[attr]
        for n, line in _dump_lines(c):
            yield n + 1, line


def dump_node(node: nodes.Node) -> str:
    """Dump a docutils node to a string.

    :param node: The docutils node to dump.

    :returns: Formatted string representation of the node.

    """
    return "\n".join(["    " * indent + line for indent, line in _dump_lines(node)])
