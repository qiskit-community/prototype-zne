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
# that they have been altered from the originals.

"""Docstrings utils module."""

from __future__ import annotations

SECTIONS = ["Args", "Returns", "Yields", "Raises"]  # TODO add header section


def insert_into_docstring(original_docstring: str, new_content_list: list[tuple[str, str]]) -> str:
    """Inserts new lines of content into existing docstring.

    Args:
        original_docstring: The docstring where to insert new lines.
        new_content_list: A list of tuples. The first element of a tuple specifies the section to
            append to, while the second element contains the new information to be added to that
            section, e.g.: [("Args", "param: example"), ("Raises", "Error: example")].

    Returns:
        Updated docstring.
    """
    docstring_lines = original_docstring.split("\n")
    docstring_lines = remove_all_leading_spaces_in_docstring(docstring_lines)
    for section, new_content in new_content_list:
        validate_section(section)
        docstring_lines = insert_into_docstring_lines(docstring_lines, new_content, section)
    return "\n".join(docstring_lines)


def remove_all_leading_spaces_in_docstring(docstring_lines: list[str]) -> list[str]:
    """Removes all common leading spaces in each line.

    Args:
        docstring_lines: A list of docstring lines.

    Returns:
        Docstring lines with leading spaces removed.
    """
    num_leading_spaces = get_num_leading_spaces(docstring_lines)
    docstring_lines[1:] = [line[num_leading_spaces:] for line in docstring_lines[1:]]
    return docstring_lines


def get_num_leading_spaces(docstring_lines: list[str]) -> int:
    """Returns the number of leading spaces in docstring.

    Args:
        docstring_lines: A list of docstring lines.

    Returns:
        The number of leading spaces.

    Raises:
        RuntimeError: If docstring is empty or one-liner.
    """
    for line in docstring_lines[1:]:
        if len(line) > 0:
            return len(line) - len(line.lstrip(" "))
    raise ValueError("Functionality not supported for single-line docstrings.")


def validate_section(section: str) -> None:
    """Validates provided docstring section.

    Args:
        section: The docstring section to be validated.

    Raises:
        ValueError: If section not a valid docstring section.
    """
    if section not in SECTIONS:
        raise ValueError(f"section has to be one of {SECTIONS}. Received {section} instead.")


def insert_into_docstring_lines(
    docstring_lines: list[str], new_content: str, section: str
) -> list[str]:
    """Inserts new entry into list of docstring lines.

    Args:
        docstring_lines: A list of docstring lines.
        new_content: The new content.
        section: The section to append to.

    Returns:
        The updated list of docstring lines.
    """
    section_exists = check_section_exists_in_docstring(docstring_lines, section)
    insert_location = get_insert_location_in_docstring(docstring_lines, section)
    if not section_exists:
        docstring_lines, insert_location = insert_new_section_into_docstring(
            docstring_lines, insert_location, section
        )
    docstring_lines, insert_location = insert_new_content_into_docstring(
        docstring_lines, insert_location, new_content
    )
    return docstring_lines


def check_section_exists_in_docstring(docstring_lines: list[str], section: str) -> bool:
    """Checks whether section already exists in docstring.

    Args:
        docstring_lines: A list of docstring lines.
        section: The section to append to.

    Returns:
        True if section already exists and False otherwise.
    """
    for line in docstring_lines:
        if section in line:
            return True
    return False


def get_insert_location_in_docstring(docstring_lines: list[str], section: str) -> int:
    """Returns index at which to insert into docstring.

    Args:
        docstring_lines: A list of docstring lines.
        section: The section to append to.

    Returns:
        The index.
    """
    section_idx = SECTIONS.index(section)
    truncated_sections = SECTIONS[section_idx + 1 :]
    for idx, line in enumerate(docstring_lines):
        if any(section in line for section in truncated_sections):
            return idx - 1
    return len(docstring_lines) - 1


def insert_new_section_into_docstring(
    docstring_lines: list[str], insert_location: int, section: str
) -> tuple[list[str], int]:
    """Inserts a new section heading into docstring.

    Args:
        docstring_lines: A list of docstring lines.
        insert_location: The index at which to insert.
        section: The section to append to.

    Returns:
        A tuple containing the updated list of docstring lines and insert location.
    """
    docstring_lines.insert(insert_location, "")
    docstring_lines.insert(insert_location + 1, section + ":")
    return docstring_lines, insert_location + 2


def insert_new_content_into_docstring(
    docstring_lines: list[str], insert_location: int, new_content: str
) -> tuple[list[str], int]:
    """Inserts a new line of content into docstring.

    Args:
        docstring_lines: A list of docstring lines.
        insert_location: The index at which to insert.
        new_content: The new content.

    Returns:
        A tuple containing the updated list of docstring lines and insert location.
    """
    new_content_lines = new_content.split("\n")
    counter = 0
    for counter, line in enumerate(new_content_lines):
        # TODO infer tab size instead of hardcoding it
        num_leading_spaces = 4 if counter == 0 else 8
        docstring_lines.insert(insert_location + counter, " " * num_leading_spaces + line)
    return docstring_lines, insert_location + counter + 1
