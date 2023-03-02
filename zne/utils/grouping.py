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

"""Grouping utils module."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import Any


def group_elements(elements: Sequence, group_size: int) -> list[tuple]:
    """Group elements in iterable into tuples of a given size.

    Args:
        elements: A list of elements to be grouped
        group_size: The size of grouped tuples

    Returns:
        List of grouped tuples
    """
    return list(group_elements_gen(elements, group_size))


def group_elements_gen(elements: Sequence, group_size: int) -> Iterator[tuple]:
    """Generate groups of elements from iterable as tuples of a given size.

    Args:
        elements: A list of elements to be grouped
        group_size: The size of grouped tuples

    Yields:
        The next grouped tuple
    """
    if not isinstance(elements, Iterable):
        raise TypeError("Values argument must be iterable.")
    if not isinstance(group_size, int):
        raise TypeError("Size argument must be non-zero positive int.")
    if group_size < 1:
        raise ValueError("Size argument must be non-zero positive int.")
    elements = list(elements)
    while elements:
        yield tuple(elements[:group_size])
        del elements[:group_size]


def merge_dicts(dict_list: Sequence[dict]) -> dict:
    """Given a sequence of dictionaries merge them all into one.

    Args:
        dict_list: A sequence of dictuinaries.

    Returns:
        A dictionary resulting from merging all the input ones. In case of key collision,
        only the latest value will be preserved.
    """
    dictionary: dict = {}
    for dct in dict_list:
        dictionary.update(dct)
    return dictionary


def from_common_key(dict_list: Sequence[dict], key: Any) -> tuple:
    """Given a sequence of dictionaries and a common key extract all values.

    Args:
        dict_list: A sequence of dictuinaries

    Returns:
        A tuple with all values extracted from the input dictionaries. Whenever key is not
        present in a dictionary, ``None`` will be inserted instead of the corresponding value.
    """
    return tuple(d.get(key, None) for d in dict_list)


def squash_for_equal_elements(sequence: Sequence) -> Any:
    """Squash values in sequence to a single output if all are equal.

    Args:
        sequence: the sequence of values to collapse.

    Returns:
        The common value if all elements are equal, or the input sequence otherwise.
    """
    if not isinstance(sequence, Sequence):
        raise TypeError("Expected Sequence object, received {type(self.noise_amplifier)} instead.")
    if len(sequence) == 0:
        raise ValueError("Empty Sequence provided.")
    first = sequence[0]
    if all(element == first for element in sequence):
        return first
    return sequence
