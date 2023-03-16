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

from test import NO_INTS, NO_REAL

from numpy import array
from pytest import mark

from zne.utils.typing import isint, isinteger, isreal, normalize_array


################################################################################
## TYPE CHECKING
################################################################################
@mark.parametrize("object", [0, 1, -1])
def test_isint_true(object):
    """Test isint true."""
    assert isint(object)


@mark.parametrize("object", NO_INTS, ids=[str(type(i).__name__) for i in NO_INTS])
def test_isint_false(object):
    """Test isint false."""
    assert not isint(object)


@mark.parametrize("object", [0, 1, -1, 1.0, -1.0])
def test_isinteger_true(object):
    """Test isinteger true."""
    assert isinteger(object)


@mark.parametrize("object", [1.2, -2.4])
def test_isinteger_false(object):
    """Test isinteger false."""
    assert not isinteger(object)


@mark.parametrize("object", [0, 1, -1, 1.2, -2.4])
def test_isreal_true(object):
    """Test isreal true."""
    assert isreal(object)


@mark.parametrize("object", NO_REAL, ids=[str(type(i).__name__) for i in NO_REAL])
def test_isreal_false(object):
    """Test isreal false."""
    assert not isreal(object)


@mark.parametrize(
    "arr, expected",
    [
        (1, 1),
        (1.0, 1.0),
        (1j, 1j),
        (None, None),
        (dict(), dict()),
        (set(), set()),
        (list(), tuple()),
        (tuple(), tuple()),
        ([1], (1,)),
        ((1,), (1,)),
        ([1, 2], (1, 2)),
        ((1, 2), (1, 2)),
        ([[1, 2]], ((1, 2),)),
        (((1, 2),), ((1, 2),)),
        ([[1], [2]], ((1,), (2,))),
        (([1], [2]), ((1,), (2,))),
        (((1,), (2,)), ((1,), (2,))),
        ([[[1]]], (((1,),),)),
        ([[[1, 2], [3, 4]]], (((1, 2), (3, 4)),)),
    ],
)
def test_normalize_array(arr, expected):
    """Test normalize array."""
    assert normalize_array(arr) == expected
    arr = array(arr)
    assert normalize_array(arr) == expected
