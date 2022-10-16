# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered fr om the originals.

from test import TYPES

from pytest import mark, raises

from zne.utils.dict_library import build_dict_library


def test_build_dict_library():
    types = [type(t) for t in TYPES]
    names = {t.__name__ for t in types}
    library = build_dict_library(*types)
    assert len(library) == len(names) != len(types)
    assert all(n in library.keys() for n in names)
    assert all(t in library.values() for t in types)
    assert all(n in names for n in library.keys())
    assert all(t in types for t in library.values())
    assert all(n == t.__name__ for n, t in library.items())


def test_build_dict_library_value_error():
    class DummyFloat(float):
        __name__ = "float"

    with raises(ValueError):
        _ = build_dict_library(float, DummyFloat())


@mark.parametrize("unnamed_object", ["Arya Stark", None, True, 1, 2.4])
def test_build_dict_library_type_error(unnamed_object):
    with raises(TypeError):
        _ = build_dict_library(unnamed_object)
