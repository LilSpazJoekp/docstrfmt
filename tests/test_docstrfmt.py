import logging

import black
import pytest
from docutils import nodes
from docutils.utils import new_document

from docstrfmt.docstrfmt import FormatContext, UnknownNodeTransformer

from docstrfmt import Manager
from docstrfmt.rst_extras import register_custom
from tests import node_eq

test_lengths = [8, 13, 34, 55, 89, 144, 72]


@pytest.mark.parametrize("length", test_lengths)
def test_formatting(manager, length):
    file = "tests/test_files/test_file.rst"
    with open(file, encoding="utf-8") as f:
        test_string = f.read()
    doc = manager.parse_string(test_string, file=file)
    output = manager.format_node(length, doc)
    doc2 = manager.parse_string(output, file=file)
    output2 = manager.format_node(length, doc2)
    assert node_eq(doc, doc2)
    assert output == output2


def test_unknown_node_transformer_skips_empty_system_message(manager):
    doc = new_document("<test>", manager.settings)
    sm = nodes.system_message("", type="WARNING")
    sm.append(nodes.paragraph())
    doc.append(sm)

    UnknownNodeTransformer(doc).apply()


def test_get_error_message_normal(manager):
    sm = nodes.system_message("", type="WARNING")
    sm.append(nodes.paragraph("", "the message"))
    assert manager._get_error_message(sm) == "the message"


def test_get_error_message_empty_paragraph(manager):
    sm = nodes.system_message("", type="WARNING")
    sm.append(nodes.paragraph())
    assert manager._get_error_message(sm) == ""


def test_get_error_message_no_children(manager):
    sm = nodes.system_message("", type="WARNING", source="src", level=2)
    assert manager._get_error_message(sm) == "src:: (WARNING/2) "


def test_register_adornments_skips_empty_title_line(manager):
    doc = new_document("<test>", manager.settings)
    section = nodes.section()
    title = nodes.title(text="Section")
    title.line = 2
    section.append(title)
    doc.append(section)

    manager._register_adornments(["Some text", "", "More text"], doc)

    assert "adornment-character" not in section.attributes


def test_target_formatter_falls_back_to_dupnames(manager):
    target = nodes.target()
    target.attributes["names"] = []
    target.attributes["dupnames"] = ["mytarget"]
    target.attributes["refuri"] = "https://example.com"
    parent = nodes.section()
    parent.append(target)

    ctx = FormatContext(width=80, current_file="<test>", manager=manager)
    assert list(manager.formatters.target(target, ctx)) == [
        ".. _mytarget: https://example.com"
    ]


def test_substitution_definition_falls_back_to_dupnames(manager):
    text = ".. |target| image:: pic.png"
    doc = manager.parse_string(text)
    sub = next(iter(doc.findall(nodes.substitution_definition)))
    sub.attributes["names"] = []
    sub.attributes["dupnames"] = ["target"]

    ctx = FormatContext(width=80, current_file="<test>", manager=manager)
    assert list(manager.formatters.substitution_definition(sub, ctx)) == [
        ".. |target| image:: pic.png"
    ]


def test_pre_process_reports_childless_system_message(manager):
    from docstrfmt.exceptions import InvalidRstErrors

    doc = new_document("<test>", manager.settings)
    sm = nodes.system_message("", type="WARNING", source="src", level=2)
    doc.append(sm)

    with pytest.raises(InvalidRstErrors) as excinfo:
        manager._pre_process(doc, 0, 1)
    assert len(excinfo.value.errors) == 1
    assert excinfo.value.errors[0].message == "src:: (WARNING/2) "


def test_substitution_definition_handles_missing_names(manager):
    text = ".. |target| image:: pic.png\n   :alt: target"
    doc = manager.parse_string(text)
    sub = next(iter(doc.findall(nodes.substitution_definition)))
    sub.attributes["names"] = []
    sub.attributes["dupnames"] = []

    ctx = FormatContext(width=80, current_file="<test>", manager=manager)
    assert list(manager.formatters.substitution_definition(sub, ctx)) == [
        ".. |target| image:: pic.png",
        "    :alt: target",
    ]


def test_target_formatter_skips_unnamed_target(manager):
    target = nodes.target()
    target.attributes["names"] = []
    target.attributes["dupnames"] = []
    target.attributes["refuri"] = "https://example.com"
    parent = nodes.section()
    parent.append(target)

    ctx = FormatContext(width=80, current_file="<test>", manager=manager)
    assert list(manager.formatters.target(target, ctx)) == []


def test_target_formatter_anonymous(manager):
    target = nodes.target()
    target.attributes["names"] = []
    target.attributes["anonymous"] = 1
    target.attributes["refuri"] = "https://example.com"
    parent = nodes.section()
    parent.append(target)

    ctx = FormatContext(width=80, current_file="<test>", manager=manager)
    assert list(manager.formatters.target(target, ctx)) == [
        ".. __: https://example.com"
    ]


def test_duplicate_targets_roundtrip(manager):
    """Regression test for #176.

    A target that duplicates an existing name with the same URI is only reported by
    docutils at INFO level, so formatting continued and raised an IndexError because
    the duplicate's name lives in ``dupnames`` instead of ``names``.

    """
    text = (
        "*****\n"
        "Title\n"
        "*****\n"
        "\n"
        "Some content with `external link <https://example.com/>`_.\n"
        "\n"
        ".. toctree::\n"
        "   :caption: Project\n"
        "   :hidden:\n"
        "\n"
        "   changelog\n"
        "   Source Code <https://github.com/example/>\n"
        "\n"
        ".. _external link: https://example.com/\n"
        ".. _pip: https://github.com/pypa/pip\n"
        ".. _pip: https://github.com/pypa/pip\n"
    )
    doc = manager.parse_string(text, file="<test>")
    output = manager.format_node(120, doc)
    assert output.count(".. _external link: https://example.com/") == 1
    assert output.count(".. _pip: https://github.com/pypa/pip") == 2
    doc2 = manager.parse_string(output, file="<test>")
    output2 = manager.format_node(120, doc2)
    assert node_eq(doc, doc2)
    assert output == output2


def test_manager_registers_custom_directives_and_roles():
    manager = Manager(
        current_file="<in>",
        black_config=black.Mode(),
        reporter=logging.getLogger(__name__),
        custom_directives=[
            "raw_default",
            {"name": "formatted_body", "raw": False, "has_content": True},
        ],
        custom_roles=["mycolor"],
    )
    src = (
        ".. raw_default:: arg\n"
        "   :opt: val\n"
        "\n"
        "   raw body\n"
        "\n"
        ".. formatted_body::\n"
        "\n"
        "   -   item one\n"
        "   -   item two\n"
        "\n"
        "Text with :mycolor:`red` in it.\n"
    )
    output = manager.format_node(80, manager.parse_string(src))
    assert output == (
        ".. raw_default:: arg\n"
        "    :opt: val\n"
        "\n"
        "    raw body\n"
        "\n"
        ".. formatted_body::\n"
        "\n"
        "    - item one\n"
        "    - item two\n"
        "\n"
        "Text with :mycolor:`red` in it.\n"
    )


def test_register_custom_rejects_bad_spec():
    with pytest.raises(ValueError, match="non-empty 'name'"):
        register_custom(custom_directives=[{}])
    with pytest.raises(ValueError, match="unsupported custom directive spec"):
        register_custom(custom_directives=[42])
    with pytest.raises(ValueError, match="names must be non-empty strings"):
        register_custom(custom_directives=[""])
    with pytest.raises(ValueError, match="'raw' must be a boolean"):
        register_custom(custom_directives=[{"name": "d", "raw": "no"}])
    with pytest.raises(ValueError, match="'required_arguments' must be a non-negative"):
        register_custom(custom_directives=[{"name": "d", "required_arguments": "2"}])
    with pytest.raises(ValueError, match="'optional_arguments' must be a non-negative"):
        register_custom(custom_directives=[{"name": "d", "optional_arguments": -1}])
    with pytest.raises(ValueError, match="unknown option"):
        register_custom(custom_directives=[{"name": "d", "bogus": 1}])
    with pytest.raises(ValueError, match="custom role names must be non-empty"):
        register_custom(custom_roles=[""])
    with pytest.raises(ValueError, match="custom role names must be non-empty"):
        register_custom(custom_roles=[{"name": "r"}])
    # A bare string must not be iterated character by character.
    with pytest.raises(ValueError, match="custom_directives must be a list"):
        register_custom(custom_directives="dir")
    with pytest.raises(ValueError, match="custom_roles must be a list"):
        register_custom(custom_roles="role")
    with pytest.raises(ValueError, match="custom_roles must be a list"):
        Manager(
            current_file="<in>",
            black_config=black.Mode(),
            reporter=logging.getLogger(__name__),
            custom_roles="role",
        )


def test_custom_directive_names_are_case_insensitive():
    """docutils looks directives up lowercased, so ``MyDir`` must still register."""
    manager = Manager(
        current_file="<in>",
        black_config=black.Mode(),
        reporter=logging.getLogger(__name__),
        custom_directives=[{"name": "MixedCase", "raw": False}],
    )
    src = ".. mixedcase::\n\n   -   one\n\n.. MIXEDCASE::\n\n   -   two\n"
    output = manager.format_node(80, manager.parse_string(src))
    assert output == ".. mixedcase::\n\n    - one\n\n.. MIXEDCASE::\n\n    - two\n"
