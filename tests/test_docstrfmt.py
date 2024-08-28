import pytest

from tests import node_eq

test_lengths = [8, 13, 34, 55, 89, 144, 72]


@pytest.mark.parametrize("length", test_lengths)
def test_formatting(manager, length):
    file = "tests/test_files/test_file.rst"
    with open(file, encoding="utf-8") as f:
        test_string = f.read()
    doc = manager.parse_string(file, test_string)
    output = manager.format_node(length, doc)
    doc2 = manager.parse_string(file, output)
    output2 = manager.format_node(length, doc2)
    assert node_eq(doc, doc2)
    assert output == output2
