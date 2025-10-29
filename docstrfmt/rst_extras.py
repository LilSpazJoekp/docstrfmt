"""Handles adding constructs to the reST parser in a way that makes sense for docstrfmt.

Non-standard directives and roles are inserted into the tree unparsed (wrapped in custom
node classes defined here) so we can format them the way they came in without caring
about what they would normally expand to.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from docutils import nodes, utils
from docutils.parsers.rst import Directive, directives, roles
from docutils.parsers.rst.directives import body, images, misc, parts, tables
from sphinx import domains, util
from sphinx.directives import code, other
from sphinx.domains.std import ProductionList
from sphinx.ext.autodoc import directive as sphinx_directive

try:  # pragma: no cover
    from sphinx.directives.admonitions import SeeAlso
except ImportError:  # pragma: no cover
    from sphinx.directives.other import SeeAlso  # type: ignore[assignment]

# Import these only to load their domain subclasses.
from sphinx.domains import c, changeset, cpp, python  # noqa: F401
from sphinx.ext import autodoc, autosummary
from sphinx.roles import generic_docroles, specific_docroles

from . import ROLE_ALIASES

if TYPE_CHECKING:
    from collections.abc import Iterator

T = TypeVar("T")


def add_directive(
    name: str,
    cls: type[Directive],
    *,
    raw: bool = True,
    is_injected: bool = False,
) -> None:
    """Add a directive to the parser.

    :param name: Name of the directive to add.
    :param cls: Directive class to register.
    :param raw: Whether the directive is raw.
    :param is_injected: Whether the directive is injected.

    """
    # We create a new class inheriting from the given directive class to automatically pick up the
    # argument counts and most of the other attributes that define how the directive is parsed, so
    # parsing can happen as normal. The things we change are:
    #
    # - Relax the option spec so an incorrect name doesn't stop formatting and every option comes
    #   through unchanged.
    # - Override the run method to just stick the directive into the tree.
    # - Add a `raw` attribute to inform formatting later on.
    namespace = {
        "option_spec": sphinx_directive.DummyOptionSpec(),
        "run": lambda self: [directive(directive=self)],
        "raw": raw,
        "has_content": True if is_injected else cls.has_content,
    }
    if is_injected:
        namespace["final_argument_whitespace"] = True
        namespace["optional_arguments"] = 1
    directives.register_directive(
        name, type(f"docstrfmt_{cls.__name__}", (cls,), namespace)
    )


def generic_role(r: str, rawtext: str, text: str, *_: Any, **__: Any) -> Any:
    """Provide a generic role that doesn't do anything.

    :param r: Role name.
    :param rawtext: Raw text of the role.
    :param text: Text content of the role.
    :param _: Unused positional arguments.
    :param __: Unused keyword arguments.

    :returns: List containing the role node and empty list.

    """
    r = ROLE_ALIASES.get(r.lower(), r)
    text = utils.unescape(text, restore_backslashes=True)
    return [role(rawtext, text=text, role=r)], []


def register() -> None:
    """Register the custom directives and roles."""
    for r in [
        # Standard roles (https://docutils.sourceforge.io/docs/ref/rst/roles.html) that don't have
        # equivalent non-role-based markup.
        "math",
        "pep-reference",
        "rfc-reference",
        "subscript",
        "superscript",
    ]:
        roles.register_canonical_role(r, generic_role)

    roles.register_canonical_role("download", ReferenceRole())
    for domain in _subclasses(domains.Domain):
        for name, role_callable in domain.roles.items():
            if isinstance(role_callable, util.docutils.ReferenceRole):
                roles.register_canonical_role(name, ReferenceRole())
                roles.register_canonical_role(f"{domain.name}:{name}", ReferenceRole())

        for name, directive_callable in domain.directives.items():
            add_directive(name, directive_callable)
            add_directive(f"{domain.name}:{name}", directive_callable)

    for name, _nodeclass in generic_docroles.items():
        roles.register_local_role(name, generic_role)

    for name, _func in specific_docroles.items():
        roles.register_local_role(name, generic_role)

    # docutils directives
    add_directive("contents", parts.Contents)
    add_directive("figure", images.Figure, raw=False)
    add_directive("image", images.Image)
    add_directive("include", misc.Include)
    add_directive("unicode", misc.Unicode)
    add_directive("list-table", tables.ListTable, raw=False)
    add_directive("csv-table", tables.CSVTable, raw=False)
    add_directive("rst-table", tables.RSTTable, raw=False)
    add_directive("rst-class", misc.Class)
    add_directive("math", body.MathBlock)
    add_directive("meta", misc.Meta)  # type: ignore[attr]
    add_directive("raw", misc.Raw)
    add_directive("rubric", body.Rubric, raw=False)

    # sphinx directives
    add_directive("autosummary", autosummary.Autosummary)
    add_directive("code-block", code.CodeBlock)
    add_directive("deprecated", changeset.VersionChange, raw=False)
    add_directive("highlight", code.Highlight)
    add_directive("literalinclude", code.LiteralInclude)
    add_directive("productionlist", ProductionList)
    add_directive("seealso", SeeAlso, raw=False)
    add_directive("sourcecode", code.CodeBlock)
    add_directive("toctree", other.TocTree)
    add_directive("versionadded", changeset.VersionChange, raw=False)
    add_directive("versionchanged", changeset.VersionChange, raw=False)
    add_directive("versionremoved", changeset.VersionChange, raw=False)

    for d in set(_subclasses(autodoc.Documenter)):
        if d.objtype != "object":
            add_directive(
                f"auto{d.objtype}", sphinx_directive.AutodocDirective, raw=False
            )

    try:  # pragma: no cover
        import sphinxarg.ext  # noqa: PLC0415

        add_directive("argparse", sphinxarg.ext.ArgParseDirective)
    except ImportError:
        pass


class ReferenceRole(util.docutils.ReferenceRole):
    """Role that doesn't do anything."""

    def run(
        self,
    ) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """Run the role.

        :returns: Tuple containing list of nodes and empty list of system messages.

        """
        node = ref_role(
            self.rawtext,
            name=self.name,
            has_explicit_title=self.has_explicit_title,
            target=self.target,
            title=self.title,
        )
        return [node], []


# noinspection PyPep8Naming
class directive(nodes.Element, nodes.Inline):
    """A directive that doesn't do anything."""


# noinspection PyPep8Naming
class ref_role(nodes.Element):
    """A role that doesn't do anything."""


# noinspection PyPep8Naming
class role(nodes.Element):
    """A role that doesn't do anything."""


def _subclasses(cls: type[T]) -> Iterator[type[T]]:
    """Get all subclasses of a class recursively.

    :param cls: The class to get subclasses for.

    :returns: Iterator of all subclasses.

    """
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _subclasses(subclass)
