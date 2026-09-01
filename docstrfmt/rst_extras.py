"""Handles adding constructs to the reST parser in a way that makes sense for docstrfmt.

Non-standard directives and roles are inserted into the tree unparsed (wrapped in custom
node classes defined here) so we can format them the way they came in without caring
about what they would normally expand to.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from docutils import nodes, utils
from docutils.parsers.rst import Directive, directives, roles
from docutils.parsers.rst.directives import (
    body,
    images,
    misc,
    parts,
    references,
    tables,
)
from docutils.parsers.rst.states import Body
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

CustomDirectiveSpec = str | dict[str, Any]
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


def register_custom(
    custom_directives: list[CustomDirectiveSpec] | None = None,
    custom_roles: list[str] | None = None,
) -> None:
    """Register user-supplied directives and roles.

    :param custom_directives: Directives to register. Each entry is either a name
        string (registered as a raw directive that accepts arbitrary content, matching
        the fallback docstrfmt uses for unknown directives) or a mapping with keys:
        ``name`` (required), ``raw`` (default ``True``), ``has_content``
        (default ``True``), ``required_arguments`` (default ``0``),
        ``optional_arguments`` (default ``1``), and ``final_argument_whitespace``
        (default ``True``).
    :param custom_roles: Names of roles to register as generic (contents are
        preserved verbatim on round-trip).

    """
    for name, options in validate_custom(custom_directives, custom_roles):
        cls = type(
            f"docstrfmt_custom_{name}",
            (Directive,),
            {
                "has_content": options["has_content"],
                "required_arguments": options["required_arguments"],
                "optional_arguments": options["optional_arguments"],
                "final_argument_whitespace": options["final_argument_whitespace"],
            },
        )
        add_directive(name, cls, raw=options["raw"])
    for name in custom_roles or []:
        roles.register_local_role(name, generic_role)


def validate_custom(
    custom_directives: list[CustomDirectiveSpec] | None = None,
    custom_roles: list[str] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Validate user-supplied directive and role configuration.

    :param custom_directives: Directive specs as accepted by :func:`register_custom`.
    :param custom_roles: Role names as accepted by :func:`register_custom`.

    :returns: The normalized ``(name, options)`` tuple for every directive spec.

    :raises ValueError: If either argument is not a list/tuple, or if any directive
        spec or role name is invalid.

    """
    for label, value in (
        ("custom_directives", custom_directives),
        ("custom_roles", custom_roles),
    ):
        if value is not None and not isinstance(value, (list, tuple)):
            msg = f"{label} must be a list, got {value!r}"
            raise ValueError(msg)
    normalized = [_normalize_directive_spec(spec) for spec in custom_directives or []]
    for name in custom_roles or []:
        if not isinstance(name, str) or not name:
            msg = f"custom role names must be non-empty strings, got {name!r}"
            raise ValueError(msg)
    return normalized


def _normalize_directive_spec(
    spec: CustomDirectiveSpec,
) -> tuple[str, dict[str, Any]]:
    """Normalize a user-provided directive spec into a (name, options) tuple.

    :param spec: Either the directive name or a mapping of options.

    :returns: The directive name (lowercased, since docutils looks directives up
        case-insensitively) and a fully populated options mapping.

    :raises ValueError: If the spec is missing a name, has an unsupported shape, or
        contains options with invalid types or unknown keys.

    """
    defaults = {
        "raw": True,
        "has_content": True,
        "required_arguments": 0,
        "optional_arguments": 1,
        "final_argument_whitespace": True,
    }
    if isinstance(spec, str):
        if not spec:
            msg = "custom directive names must be non-empty strings"
            raise ValueError(msg)
        return spec.lower(), dict(defaults)
    if isinstance(spec, dict):
        name = spec.get("name")
        if not isinstance(name, str) or not name:
            msg = "custom directive entries must include a non-empty 'name'"
            raise ValueError(msg)
        options = {key: spec.get(key, default) for key, default in defaults.items()}
        for key in ("raw", "has_content", "final_argument_whitespace"):
            if not isinstance(options[key], bool):
                msg = (
                    f"custom directive {name!r}: {key!r} must be a boolean, got"
                    f" {options[key]!r}"
                )
                raise ValueError(msg)
        for key in ("required_arguments", "optional_arguments"):
            value = options[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                msg = (
                    f"custom directive {name!r}: {key!r} must be a non-negative"
                    f" integer, got {value!r}"
                )
                raise ValueError(msg)
        unknown = set(spec) - {"name", *defaults}
        if unknown:
            msg = (
                f"custom directive {name!r}: unknown option(s)"
                f" {', '.join(sorted(map(repr, unknown)))}"
            )
            raise ValueError(msg)
        return name.lower(), options
    msg = f"unsupported custom directive spec: {spec!r}"
    raise ValueError(msg)


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


def _patch_run_directive() -> None:
    """Backfill ``.line`` on nodes returned by directives that don't set it.

    Docutils' ``Body.run_directive`` knows the source line where each directive was
    invoked (``lineno``) but doesn't propagate it to the returned nodes. Directives that
    hand-construct nodes in ``run()`` (e.g. ``Sectnum``/``Contents``/``Meta`` producing
    ``pending`` nodes) therefore reach the formatter with ``.line is None``, making
    error messages report ``line None``. Wrap ``run_directive`` once to fill in
    ``.line`` from the directive's own ``lineno``.

    """
    if getattr(Body.run_directive, "_docstrfmt_patched", False):
        return
    original = Body.run_directive

    def run_directive(
        self: Body,
        directive: type[Directive],
        match: Any,
        type_name: str,
        option_presets: Any,
    ) -> Any:
        lineno = self.state_machine.abs_line_number()
        result, blank_finish = original(
            self, directive, match, type_name, option_presets
        )
        for node in result:
            if node.line is None:
                node.line = lineno
        return result, blank_finish

    run_directive._docstrfmt_patched = True  # type: ignore[attr-defined]
    Body.run_directive = run_directive  # type: ignore[method-assign]


def register() -> None:
    """Register the custom directives and roles."""
    _patch_run_directive()
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
    add_directive("class", misc.Class)
    add_directive("code", body.CodeBlock)
    add_directive("compound", body.Compound, raw=False)
    add_directive("container", body.Container, raw=False)
    add_directive("contents", parts.Contents)
    add_directive("csv-table", tables.CSVTable)
    add_directive("epigraph", body.Epigraph, raw=False)
    add_directive("figure", images.Figure, raw=False)
    add_directive("footer", parts.Footer)
    add_directive("header", parts.Header)
    add_directive("highlights", body.Highlights, raw=False)
    add_directive("image", images.Image)
    add_directive("include", misc.Include)
    add_directive("list-table", tables.ListTable, raw=False)
    add_directive("math", body.MathBlock)
    add_directive("meta", misc.Meta)  # type: ignore[attr]
    add_directive("pull-quote", body.PullQuote, raw=False)
    add_directive("raw", misc.Raw)
    add_directive("rst-class", misc.Class)
    add_directive("rst-table", tables.RSTTable, raw=False)
    add_directive("rubric", body.Rubric, raw=False)
    add_directive("sectnum", parts.Sectnum)
    add_directive("sidebar", body.Sidebar, raw=False)
    add_directive("table", tables.RSTTable, raw=False)
    add_directive("target-notes", references.TargetNotes)
    add_directive("topic", body.Topic, raw=False)
    add_directive("unicode", misc.Unicode)

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
