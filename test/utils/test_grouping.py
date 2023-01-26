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

from test import NO_INTS, NO_ITERS

from pytest import mark, raises

from zne.utils.grouping import (
    from_common_key,
    group_elements,
    merge_dicts,
    squash_for_equal_elements,
)


@mark.parametrize(
    "elements, size, expected",
    cases := [
        ([], 1, []),
        ([], 2, []),
        ([], 3, []),
        ([0], 1, [(0,)]),
        ([0], 2, [(0,)]),
        ([0], 3, [(0,)]),
        ([0, 1], 1, [(0,), (1,)]),
        ([0, 1], 2, [(0, 1)]),
        ([0, 1], 3, [(0, 1)]),
        ([0, 1, 2], 1, [(0,), (1,), (2,)]),
        ([0, 1, 2], 2, [(0, 1), (2,)]),
        ([0, 1, 2], 3, [(0, 1, 2)]),
        ([0, 1, 2, 3], 1, [(0,), (1,), (2,), (3,)]),
        ([0, 1, 2, 3], 2, [(0, 1), (2, 3)]),
        ([0, 1, 2, 3], 3, [(0, 1, 2), (3,)]),
    ],
    ids=[f"list<{len(value)}>-{size}" for value, size, expected in cases],
)
def test_group_elements(elements, size, expected):
    groups = group_elements(elements, group_size=size)
    assert groups == (expected)


@mark.parametrize("elements", NO_ITERS, ids=[str(type(i).__name__) for i in NO_ITERS])
def test_group_elements_type_error_iter(elements):
    with raises(TypeError):
        assert group_elements(elements, group_size=1)


@mark.parametrize("size", NO_INTS, ids=[str(type(i).__name__) for i in NO_INTS])
def test_group_elements_type_error_int(size):
    with raises(TypeError):
        assert group_elements(elements=[], group_size=size)


@mark.parametrize("size", [0, -1])
def test_group_elements_value_error(size):
    with raises(ValueError):
        assert group_elements(elements=[], group_size=size)


@mark.parametrize(
    "dict_list, expected",
    [
        ([{}, {}], {}),
        ([{0: 1}, {}], {0: 1}),
        ([{}, {0: 1}], {0: 1}),
        ([{0: 1}, {0: 1}], {0: 1}),
        ([{0: 2}, {0: 1}], {0: 1}),
        ([{0: 1}, {0: 2}], {0: 2}),
        ([{0: 1}, {2: 3}], {0: 1, 2: 3}),
        ([{2: 3}, {0: 1}], {2: 3, 0: 1}),
        ([{0: 1, 2: 3}, {4: 5}], {0: 1, 2: 3, 4: 5}),
        ([{0: 1, 4: 5}, {2: 3}], {0: 1, 4: 5, 2: 3}),
        ([{4: 5, 0: 1}, {2: 3}], {4: 5, 0: 1, 2: 3}),
        ([{4: 5, 2: 3}, {0: 1}], {4: 5, 2: 3, 0: 1}),
        ([{0: 1, 2: 3}, {0: 2}], {0: 2, 2: 3}),
        ([{4: 5}, {0: 1, 2: 3}], {4: 5, 0: 1, 2: 3}),
        ([{2: 3}, {0: 1, 4: 5}], {2: 3, 0: 1, 4: 5}),
        ([{2: 3}, {4: 5, 0: 1}], {2: 3, 4: 5, 0: 1}),
        ([{0: 1}, {4: 5, 2: 3}], {0: 1, 4: 5, 2: 3}),
        ([{0: 1}, {0: 2, 2: 3}], {0: 2, 2: 3}),
    ],
)
def test_merge_dicts(dict_list, expected):
    assert merge_dicts(dict_list) == expected


@mark.parametrize(
    "dict_list, key, expected",
    tuple(
        zip(
            [
                ({"key": 0}, {"key": 1}),
                ({"key": 0}, {}),
                ({}, {}),
            ],
            ["key", "key", "key"],
            [(0, 1), (0, None), (None, None)],
        )
    ),
)
def test_from_common_key(dict_list, key, expected):
    assert from_common_key(dict_list, key) == expected


@mark.parametrize(
    "sequence, expected",
    tuple(
        zip(
            [(0, 0), (1, 1), (0, 1)],
            [0, 1, (0, 1)],
        )
    ),
)
def test_squash_for_equal_elements(sequence, expected):
    assert squash_for_equal_elements(sequence) == expected


@mark.parametrize("obj", NO_ITERS, ids=[str(type(i).__name__) for i in NO_ITERS])
def test_squash_for_equal_elements_type_error(obj):
    with raises(TypeError):
        assert squash_for_equal_elements(obj)


def test_squash_for_equal_elements_value_error():
    with raises(ValueError):
        assert squash_for_equal_elements([])
