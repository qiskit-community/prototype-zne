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
# that they have been altered from the originals.

from itertools import product

from pytest import mark, raises

from zne.utils.validation import (
    _validate_isinstance_types,
    validate_object_type,
    validate_sequence,
)

from .. import TYPES


################################################################################
## VALIDATION
################################################################################
@mark.parametrize("obj", [*(t for t in TYPES if t == t)])
def test_validate_object_type(obj):
    assert obj == validate_object_type(None, type(obj), default=obj)
    assert obj == validate_object_type(obj, type(obj))
    assert obj == validate_object_type(obj, (type(obj), *[type(t) for t in TYPES]))
    with raises(TypeError):
        validate_object_type(obj, [])
    with raises(TypeError):
        validate_object_type(obj, tuple(type(t) for t in TYPES if not isinstance(obj, type(t))))


@mark.parametrize(
    "seq, typecast",
    cases := tuple(
        product(
            [
                [0],
                (0,),
                [0, 1],
                (0, 1),
                [0, 1, 2],
                (0, 1, 2),
                [(), (0,), (0, 1)],
                ((), (0,), (0, 1)),
            ],
            [list, tuple],
        )
    ),
    ids=[f"{s}-{t.__name__}" for s, t in cases],
)
def test_validate_sequence(seq, typecast):
    assert validate_sequence(seq) == seq
    assert validate_sequence(None, default=seq) == seq
    assert validate_sequence(seq, cast_single=True) == seq
    assert validate_sequence(seq, standard_type=typecast) == typecast(seq)
    assert validate_sequence(None, standard_type=typecast, default=seq) == typecast(seq)
    assert validate_sequence(seq, standard_type=typecast, cast_single=True) == typecast(seq)
    if len(seq) > 0:
        el = seq[-1]
        el_type = type(el)
        assert validate_sequence(seq, el_type) == seq
        assert validate_sequence(el, el_type, cast_single=True) == (el,)
        assert validate_sequence(seq, el_type, standard_type=typecast) == typecast(seq)
        assert validate_sequence(el, el_type, standard_type=typecast, cast_single=True) == typecast(
            [el]
        )
    with raises(ValueError):
        validate_sequence(seq, standard_type=type(None))
    s = set(range(len(seq)))
    assert validate_sequence(s, allow_set=True) == s
    assert validate_sequence(tuple(s), allow_set=True, standard_type=set) == s


################################################################################
## AUXILIARY
################################################################################
@mark.parametrize("obj", [*(t for t in TYPES if t == t)])
def test_validate_isinstance_types(obj):
    tp = type(obj)
    assert _validate_isinstance_types(tp) == (tp,)
    assert _validate_isinstance_types((int, tp)) == (int, tp)
    assert _validate_isinstance_types((tp, tp)) == (tp, tp)
    with raises(TypeError):
        _validate_isinstance_types(obj)
