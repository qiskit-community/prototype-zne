# This code is part of Qiskit.
#
# (C) Copyright IBM 2022-2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered fr om the originals.

from unittest.mock import Mock, call, patch

from pytest import fixture, mark, raises

from zne.utils.docstrings import (
    check_section_exists_in_docstring,
    get_insert_location_in_docstring,
    get_num_leading_spaces,
    insert_into_docstring,
    insert_into_docstring_lines,
    insert_new_content_into_docstring,
    insert_new_section_into_docstring,
    remove_all_leading_spaces_in_docstring,
    validate_section,
)

################################################################################
## CONSTANTS
################################################################################

SECTIONS = ["Args", "Returns", "Yields", "Raises"]

MOCK_TARGET_PATH = "zne.utils.docstrings"

docstring1 = """Some explanation.

    And more.

    Args:
        param1: The first parameter.
        param2: The second parameter,
            some more explanation.

    Returns:
        True if successful, False otherwise.
    """

docstring2 = """Some explanation.

        Returns:
            True if successful, False otherwise.

        Raises:
            Error: If something fails.
        """

docstring3 = """Some explanation.

Yields:
    The next number.
"""

DOCSTRINGS = [docstring1, docstring2, docstring3]
DOCSTRINGS_LINES = [docstring.split("\n") for docstring in DOCSTRINGS]

################################################################################
## MODULE FIXTURES
################################################################################


@fixture(scope="module")
def docstring():
    return DOCSTRINGS[0]


@fixture(scope="module")
def docstring_lines():
    return DOCSTRINGS_LINES[0]


@fixture(scope="module")
def new_content():
    return "param: example"


@fixture(scope="module")
def section():
    return "Args"


@fixture(scope="module")
def tab_size():  # TODO use '\t' instead
    return 4


@fixture(scope="module")
def patch_with_mock():
    def factory_method(method_name=None, **kwargs):
        method_name = method_name or ""
        return patch(MOCK_TARGET_PATH + method_name, **kwargs)

    return factory_method


@fixture(scope="module")
def patch_with_multiple_mocks():
    def factory_method(**kwargs):
        return patch.multiple(MOCK_TARGET_PATH, **kwargs)

    return factory_method


################################################################################
## TESTS
################################################################################


def test_insert_into_docstring(patch_with_multiple_mocks, docstring):
    new_content_list = [("Args", "param"), ("Raises", "Error")]
    mocks = {
        "remove_all_leading_spaces_in_docstring": Mock(return_value=["string1"]),
        "validate_section": Mock(),
        "insert_into_docstring_lines": Mock(return_value=["string2", "string3"]),
    }
    with patch_with_multiple_mocks(**mocks):
        new_docstring = insert_into_docstring(docstring, new_content_list)
    mocks["remove_all_leading_spaces_in_docstring"].assert_called_once_with(docstring.split("\n"))
    assert mocks["validate_section"].call_count == len(new_content_list)
    calls = [call("Args"), call("Raises")]
    mocks["validate_section"].assert_has_calls(calls, any_order=False)
    assert mocks["insert_into_docstring_lines"].call_count == len(new_content_list)
    calls = [call(["string1"], "param", "Args"), call(["string2", "string3"], "Error", "Raises")]
    mocks["insert_into_docstring_lines"].assert_has_calls(calls, any_order=False)
    assert new_docstring == "string2\nstring3"


def test_remove_all_leading_spaces_in_docstring(patch_with_mock, docstring_lines):
    docstring_lines_copy = docstring_lines.copy()
    with patch_with_mock(".get_num_leading_spaces", return_value=3) as mock:
        new_docstring_lines = remove_all_leading_spaces_in_docstring(docstring_lines_copy)
    mock.assert_called_once_with(docstring_lines_copy)
    assert new_docstring_lines[0] == docstring_lines[0]
    for i, line in enumerate(new_docstring_lines[1:]):
        assert line == docstring_lines[i + 1][3:]


@mark.parametrize(
    "docstring_lines, num_leading_spaces_expected",
    cases := tuple(
        zip(
            DOCSTRINGS_LINES,
            [4, 8, 0],
        )
    ),
    ids=[f"{type(dl).__name__}<{len(dl)}>-{nlse}" for dl, nlse in cases],
)
def test_get_num_leading_spaces(docstring_lines, num_leading_spaces_expected):
    assert get_num_leading_spaces(docstring_lines) == num_leading_spaces_expected


@mark.parametrize("docstring_lines", cases := [[""], ["One-liner"]], ids=[f"{c}" for c in cases])
def test_get_num_leading_spaces_value_error(docstring_lines):
    with raises(ValueError):
        assert get_num_leading_spaces(docstring_lines)


@mark.parametrize("section", cases := SECTIONS, ids=[f"{c}" for c in cases])
def test_validate_section(section):
    validate_section(section)


@mark.parametrize("section", cases := ["Argss", "returns", "Raises:"], ids=[f"{c}" for c in cases])
def test_validate_section_value_error(section):
    with raises(ValueError):
        assert validate_section(section)


def test_insert_into_docstring_lines_section_exists_false(
    patch_with_multiple_mocks, section, new_content
):
    mocks = {
        "check_section_exists_in_docstring": Mock(return_value=False),
        "get_insert_location_in_docstring": Mock(return_value=1),
        "insert_new_section_into_docstring": Mock(return_value=(["string2"], 2)),
        "insert_new_content_into_docstring": Mock(return_value=(["string3"], 3)),
    }
    with patch_with_multiple_mocks(**mocks):
        docstring_lines = insert_into_docstring_lines(["string1"], new_content, section)
    mocks["check_section_exists_in_docstring"].assert_called_once_with(["string1"], section)
    mocks["get_insert_location_in_docstring"].assert_called_once_with(["string1"], section)
    mocks["insert_new_section_into_docstring"].assert_called_once_with(["string1"], 1, section)
    mocks["insert_new_content_into_docstring"].assert_called_once_with(["string2"], 2, new_content)
    assert docstring_lines == ["string3"]


def test_insert_into_docstring_lines_section_exists_true(
    patch_with_multiple_mocks, section, new_content
):
    mocks = {
        "check_section_exists_in_docstring": Mock(return_value=True),
        "get_insert_location_in_docstring": Mock(return_value=1),
        "insert_new_section_into_docstring": Mock(return_value=(["string2"], 2)),
        "insert_new_content_into_docstring": Mock(return_value=(["string3"], 3)),
    }
    with patch_with_multiple_mocks(**mocks):
        docstring_lines = insert_into_docstring_lines(["string1"], new_content, section)
    mocks["check_section_exists_in_docstring"].assert_called_once_with(["string1"], section)
    mocks["get_insert_location_in_docstring"].assert_called_once_with(["string1"], section)
    mocks["insert_new_section_into_docstring"].assert_not_called()
    mocks["insert_new_content_into_docstring"].assert_called_once_with(["string1"], 1, new_content)
    assert docstring_lines == ["string3"]


@mark.parametrize(
    "docstring_lines, section, section_exists_expected",
    cases := tuple(
        zip(
            DOCSTRINGS_LINES,
            ["Args", "Yields", "Raises"],
            [True, False, False],
        )
    ),
    ids=[f"{type(dl).__name__}<{len(dl)}>-{s}-{see}" for dl, s, see in cases],
)
def test_check_section_exists_in_docstring(docstring_lines, section, section_exists_expected):
    assert check_section_exists_in_docstring(docstring_lines, section) == section_exists_expected


@mark.parametrize(
    "docstring_lines, section, insert_location_expected",
    cases := tuple(
        zip(
            DOCSTRINGS_LINES,
            ["Args", "Yields", "Raises"],
            [8, 4, 4],
        )
    ),
    ids=[f"{type(dl).__name__}<{len(dl)}>-{s}-{ile}" for dl, s, ile in cases],
)
def test_get_insert_location_in_docstring(docstring_lines, section, insert_location_expected):
    assert get_insert_location_in_docstring(docstring_lines, section) == insert_location_expected


@mark.parametrize(
    "docstring_lines, section, insert_location",
    cases := tuple(
        zip(
            DOCSTRINGS_LINES,
            ["Args", "Yields", "Raises"],
            [8, 4, 4],
        )
    ),
    ids=[f"{type(dl).__name__}<{len(dl)}>-{s}-{il}" for dl, s, il in cases],
)
def test_insert_new_section_into_docstring(docstring_lines, section, insert_location):
    new_docstring_lines, new_insert_location = insert_new_section_into_docstring(
        docstring_lines.copy(), insert_location, section
    )
    assert new_insert_location == insert_location + 2
    assert new_docstring_lines[:insert_location] == docstring_lines[:insert_location]
    assert new_docstring_lines[insert_location] == ""
    assert new_docstring_lines[insert_location + 1] == section + ":"
    assert new_docstring_lines[insert_location + 2 :] == docstring_lines[insert_location:]


@mark.parametrize(
    "docstring_lines, new_content, insert_location",
    cases := tuple(
        zip(
            DOCSTRINGS_LINES,
            ["Lorem ipsum"],
            [8, 4, 4],
        )
    ),
    ids=[f"{type(dl).__name__}<{len(dl)}>-{nc}-{il}" for dl, nc, il in cases],
)
def test_insert_new_content_into_docstring_single_line(
    docstring_lines, new_content, insert_location, tab_size
):
    new_docstring_lines, new_insert_location = insert_new_content_into_docstring(
        docstring_lines.copy(), insert_location, new_content
    )
    new_content_lines = new_content.split("\n")
    expected_new_insert_location = insert_location + len(new_content_lines)
    assert new_insert_location == expected_new_insert_location
    assert len(new_docstring_lines) == len(docstring_lines) + len(new_content_lines)
    assert new_docstring_lines[:insert_location] == docstring_lines[:insert_location]
    assert new_docstring_lines[insert_location] == " " * tab_size + new_content_lines[0]
    assert new_docstring_lines[expected_new_insert_location:] == docstring_lines[insert_location:]


@mark.parametrize(
    "docstring_lines, new_content, insert_location",
    cases := tuple(
        zip(
            DOCSTRINGS_LINES,
            ["Lorem\nipsum", "dolor\nsit\namet"],
            [8, 4, 4],
        )
    ),
    ids=[f"{type(dl).__name__}<{len(dl)}>-{nc}-{il}" for dl, nc, il in cases],
)
def test_insert_new_content_into_docstring_multiple_lines(
    docstring_lines, new_content, insert_location, tab_size
):
    new_docstring_lines, new_insert_location = insert_new_content_into_docstring(
        docstring_lines.copy(), insert_location, new_content
    )
    new_content_lines = new_content.split("\n")
    expected_new_insert_location = insert_location + len(new_content_lines)
    assert new_insert_location == expected_new_insert_location
    assert len(new_docstring_lines) == len(docstring_lines) + len(new_content_lines)
    assert new_docstring_lines[:insert_location] == docstring_lines[:insert_location]
    assert new_docstring_lines[insert_location] == " " * tab_size + new_content_lines[0]
    expected = [" " * tab_size * 2 + content for content in new_content_lines[1:]]
    assert new_docstring_lines[insert_location + 1 : expected_new_insert_location] == expected
    assert new_docstring_lines[expected_new_insert_location:] == docstring_lines[insert_location:]
