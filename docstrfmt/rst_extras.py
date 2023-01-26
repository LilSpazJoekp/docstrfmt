"""This module handles adding constructs to the reST parser in a way that makes sense for docstrfmt.

Non-standard directives and roles are inserted into the tree unparsed (wrapped in custom
node classes defined here) so we can format them the way they came in without without
caring about what they would normally expand to.

"""
import sys
from collections import deque
from io import StringIO
from os.path import abspath, join
from tempfile import mkdtemp
from typing import Any, Iterator, List, Tuple, Type, TypeVar

import docutils
import sphinx
from docutils.parsers.rst import directives, roles
from docutils.parsers.rst.directives import body, images, misc, parts, tables
from sphinx.application import Sphinx, builtin_extensions
from sphinx.config import Config
from sphinx.directives import code, other

# Import these only to load their domain subclasses.
from sphinx.domains import c, cpp, python  # noqa: F401
from sphinx.domains.python import PyCurrentModule, PyFunction
from sphinx.errors import ConfigError, ExtensionError, VersionRequirementError
from sphinx.events import EventManager
from sphinx.ext import autodoc, autosummary
from sphinx.project import Project
from sphinx.registry import SphinxComponentRegistry
from sphinx.roles import code_role, generic_docroles, specific_docroles
from sphinx.util.build_phase import BuildPhase
from sphinx.util.docutils import ReferenceRole as _ReferenceRole
from sphinx.util.logging import prefixed_warnings
from sphinx.util.tags import Tags

from .util import Reporter

T = TypeVar("T")


class directive(docutils.nodes.Element):
    pass


class role(docutils.nodes.Element):
    pass


class ref_role(docutils.nodes.Element):
    pass


class ReferenceRole(_ReferenceRole):
    def run(
        self,
    ) -> Tuple[List[docutils.nodes.Node], List[docutils.nodes.system_message]]:
        node = ref_role(
            self.rawtext,
            name=self.name,
            has_explicit_title=self.has_explicit_title,
            target=self.target,
            title=self.title,
        )
        return [node], []


role_aliases = {
    "pep": "PEP",
    "pep-reference": "PEP",
    "rfc": "RFC",
    "rfc-reference": "RFC",
    "subscript": "sub",
    "superscript": "sup",
    "abbreviation": "Abbreviation",
}


def generic_role(r: str, rawtext: str, text: str, *_: Any, **__: Any) -> Any:
    r = role_aliases.get(r.lower(), r)
    text = docutils.utils.unescape(text, restore_backslashes=True)
    return [role(rawtext, text=text, role=r)], []


def _add_directive(
    name: str,
    cls: Type[docutils.parsers.rst.Directive],
    *,
    raw: bool = True,
) -> None:
    # We create a new class inheriting from the given directive class to automatically pick up the
    # argument counts and most of the other attributes that define how the directive is parsed, so
    # parsing can happen as normal. The things we change are:
    #
    # - Relax the option spec so an incorrect name doesn't stop formatting and every option comes
    #   through unchanged.
    # - Override the run method to just stick the directive into the tree.
    # - Add a `raw` attribute to inform formatting later on.
    from . import docstrfmt

    namespace = {
        "option_spec": autodoc.directive.DummyOptionSpec(),
        "run": lambda self: [directive(directive=self)],
        "raw": raw,
    }
    directives.register_directive(
        name, type(f"docstrfmt_{cls.__name__}", (cls,), namespace)
    )
    setattr(docstrfmt.Formatters, cls.__name__, docstrfmt.Formatters.directive)


def _subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _subclasses(subclass)


def register() -> None:
    patch()
    # `list-table` directives are parsed into table nodes by default and could be formatted as such,
    # but that's vulnerable to producing malformed tables when the given column widths are too
    # small.

    # docutils directives
    _add_directive("contents", parts.Contents)
    _add_directive("image", images.Image)
    _add_directive("include", misc.Include)
    _add_directive("math", body.MathBlock)
    _add_directive("raw", misc.Raw)
    _add_directive("figure", images.Figure, raw=False)
    _add_directive("list-table", tables.ListTable, raw=False)
    _add_directive("csv-table", tables.CSVTable, raw=False)

    # sphinx directives
    _add_directive("autosummary", autosummary.Autosummary)
    _add_directive("currentmodule", PyCurrentModule)
    _add_directive("deprecated", other.VersionChange, raw=False)
    _add_directive("function", PyFunction)
    _add_directive("literalinclude", code.LiteralInclude)
    _add_directive("py:function", PyFunction)
    _add_directive("rst-class", other.Class)
    _add_directive("seealso", other.SeeAlso, raw=False)
    _add_directive("toctree", other.TocTree)
    _add_directive("versionadded", other.VersionChange, raw=False)
    _add_directive("versionchanged", other.VersionChange, raw=False)

    for d in set(_subclasses(autodoc.Documenter)):
        if d.objtype != "object":
            _add_directive(
                f"auto{d.objtype}", autodoc.directive.AutodocDirective, raw=False
            )

    try:
        import sphinxarg.ext
    except ImportError:
        pass
    else:  # pragma: no cover
        _add_directive("argparse", sphinxarg.ext.ArgParseDirective)


def patch():
    for r in [
        # Standard roles (https://docutils.sourceforge.io/docs/ref/rst/roles.html) that don't have
        # equivalent non-role-based markup.
        "math",
        "pep-reference",
        "rfc-reference",
        "subscript",
        "superscript",
    ]:
        roles.register_local_role(r, generic_role)  # type: ignore

    roles.register_canonical_role("download", ReferenceRole())

    for name, nodeclass in generic_docroles.items():
        roles.register_local_role(name, generic_role)  # type: ignore

    for name, func in specific_docroles.items():
        roles.register_local_role(name, generic_role)

    # Since docutils registers it as a canonical role, override it as a
    # canonical role as well.
    roles.register_canonical_role("code", code_role)

    for domain in _subclasses(sphinx.domains.Domain):
        for name, role_callable in domain.roles.items():
            if isinstance(role_callable, sphinx.util.docutils.ReferenceRole):
                roles.register_canonical_role(name, ReferenceRole())
                roles.register_canonical_role(f"{domain.name}:{name}", ReferenceRole())

    _add_directive("contents", parts.Contents)
    _add_directive("image", images.Image)
    _add_directive("include", misc.Include)
    _add_directive("math", body.MathBlock)
    _add_directive("raw", misc.Raw)
    _add_directive("figure", images.Figure, raw=False)
    _add_directive("list-table", tables.ListTable, raw=False)
    _add_directive("csv-table", tables.CSVTable, raw=False)


# Adapted from sphinx.application.
# This is to import all the Sphinx extensions and register all the directives and
# roles.

builtin_extensions += (
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
)


class SphinxLoader(Sphinx):
    # noinspection PyMissingConstructor
    def __init__(
        self,
        reporter: Reporter,
        confdir: str,
        confoverrides=None,
        status=sys.stdout,
        warning=sys.stderr,
        freshenv: bool = False,
        warningiserror: bool = False,
        tags: List[str] = None,
        verbosity: int = 0,
        parallel: int = 0,
        keep_going: bool = False,
        pdb: bool = False,
    ):

        # for name, nodeclass in generic_docroles.items():
        #     roles.register_canonical_role(name, generic_role)  # type: ignore

        self.phase = BuildPhase.INITIALIZATION
        self.verbosity = verbosity
        self.extensions = {}
        self.registry = SphinxComponentRegistry()

        # validate provided directories
        self.srcdir = abspath(".")
        outdir = mkdtemp()
        self.outdir = abspath(outdir)
        doctreedir = mkdtemp()
        self.doctreedir = abspath(join(doctreedir, "doctree"))

        self.parallel = parallel

        self._status = StringIO()
        self.quiet: bool = True
        self._warning = StringIO()
        self._warncount = 0
        self.keep_going = warningiserror and keep_going
        if self.keep_going:
            self.warningiserror = False
        else:
            self.warningiserror = warningiserror
        self.pdb = pdb

        self.events = EventManager(self)

        # keep last few messages for traceback
        # This will be filled by sphinx.util.logging.LastMessagesWriter
        self.messagelog = deque(maxlen=10)

        # status code for command-line application
        self.statuscode = 0

        # read config
        self.tags = Tags(tags)
        if confdir is None:
            # set confdir to srcdir if -C given (!= no confdir); a few pieces
            # of code expect a confdir to be set
            self.confdir = abspath("./docs")
            self.config = Config({}, confoverrides or {})
        else:
            self.confdir = abspath(confdir)
            self.config = Config.read(self.confdir, confoverrides or {}, self.tags)

        # initialize some limited config variables before initialize i18n and loading
        # extensions
        self.config.pre_init_values()

        # set up translation infrastructure
        self._init_i18n()

        # check the Sphinx version if requested
        if (
            self.config.needs_sphinx
            and self.config.needs_sphinx > sphinx.__display_version__
        ):
            raise VersionRequirementError(
                f"This project needs at least Sphinx v{self.config.needs_sphinx} and"
                " therefore cannot be built with this version."
            )

        # load all built-in extension modules
        for extension in builtin_extensions:
            self.setup_extension(extension)

        # load all user-given extension modules
        for extension in self.config.extensions:
            try:
                self.setup_extension(extension)
            except ExtensionError:
                pass

        # preload builder module (before init config values)
        self.preload_builder("html")

        # the config file itself can be an extension
        if self.config.setup:
            prefix = "while setting up extension conf.py:"
            with prefixed_warnings(prefix):
                if callable(self.config.setup):
                    self.config.setup(self)
                else:
                    raise ConfigError(
                        "'setup' as currently defined in conf.py isn't a Python"
                        " callable. Please modify its definition to make it a callable"
                        " function. This is needed for conf.py to behave as a Sphinx"
                        " extension."
                    )

        # now that we know all config values, collect them from conf.py
        self.config.init_values()
        self.events.emit("config-inited", self.config)

        # create the project
        self.project = Project(self.srcdir, self.config.source_suffix)

        # set up the build environment
        self.env = self._init_env(freshenv)

        # create the builder
        self.builder = self.create_builder("html")
        self.builder.use_message_catalog = False

        # build environment post-initialization, after creating the builder
        self._post_init_env()

        # set up the builder
        self._init_builder()

        patch()

    def add_directive(self, name: str, cls: Any, override: bool = False) -> None:
        from . import docstrfmt

        has_content = getattr(cls, "has_content")
        namespace = {
            "option_spec": autodoc.directive.DummyOptionSpec(),
            "run": lambda d: [directive(directive=d)],
            "raw": has_content,
        }
        directives.register_directive(
            name, type(f"docstrfmt_{cls.__name__}", (cls,), namespace)
        )
        setattr(docstrfmt.Formatters, cls.__name__, docstrfmt.Formatters.directive)
