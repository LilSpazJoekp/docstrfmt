import pytest
from docutils import nodes
from docutils.utils import new_document

from docstrfmt.docstrfmt import FormatContext, UnknownNodeTransformer

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
