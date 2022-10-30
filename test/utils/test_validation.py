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

from typing import Any
from unittest.mock import Mock

from pytest import mark, raises

from zne.utils.unset import UNSET
from zne.utils.validation import quality


################################################################################
## AUXILIARY
################################################################################
class EqualCopies:
    """Auxiliary wrapper class to check that deepcopies are equal."""

    def __init__(self, value: Any = None) -> None:
        self.value = value

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self.__class__):
            return False
        return self.value == __o.value


################################################################################
## TESTS
################################################################################
class TestQualityInit:
    """Test `quality` descriptor init."""

    def test_defaults(self):
        q = quality()
        assert q.fval is None
        assert q.feff is None
        assert q.default is UNSET
        assert q.null is UNSET

    def test_custom(self):
        fval = Mock()
        feff = Mock()
        default = EqualCopies("default")
        null = EqualCopies("null")
        q = quality(fval, feff, default=default, null=null)
        assert q.fval is fval
        assert q.feff is feff
        assert q.default == default
        assert q.null == null

    def test_keyword_only(self):
        with raises(TypeError):
            quality(None, None, "default")


class TestQualityCall:
    """Test `quality` descriptor call."""

    @mark.parametrize(
        "keys",
        [
            ("fval",),
            ("feff",),
            ("fval", "feff"),
        ],
    )
    def test_mutable(self, keys):
        q = quality()
        kwargs = {k: Mock() for k in keys}
        qq = q(**kwargs)
        assert q is not qq
        for key in kwargs:
            assert getattr(qq, key) is kwargs.get(key)

    @mark.parametrize(
        "keys",
        [
            ("default",),
            ("null",),
            ("default", "null"),
        ],
    )
    def test_immutable(self, keys):
        q = quality()
        kwargs = {k: EqualCopies(k) for k in keys}
        qq = q(**kwargs)
        assert q is not qq
        for key in kwargs:
            assert getattr(qq, key) == kwargs.get(key)


@mark.parametrize("property", ["default", "null"])
class TestQualityProperties:
    """Test `quality` descriptor properties."""

    def test_immutable(self, property):
        descriptor = quality()
        with raises(AttributeError):
            setattr(descriptor, property, ...)

    def test_copy(self, property):
        p = EqualCopies(property)
        descriptor = quality(**{property: p})
        assert getattr(descriptor, property) is not p
        assert getattr(descriptor, property) == p


class TestQualityDescriptor:
    """Test `quality` descriptor protocol (exept for `__set__`)."""

    @mark.parametrize("attr", ["attr", "name", "foo", "bar"])
    def test_set_name(self, attr):
        descriptor = quality()
        type("Dummy", (), {attr: descriptor})
        assert descriptor.name == attr
        assert descriptor.private_name == "_" + attr

    def test_get(self):
        descriptor = quality()
        Dummy = type("Dummy", (), {"q": descriptor})
        assert Dummy.q is descriptor

    def test_delete(self):
        descriptor = quality()
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        assert not hasattr(d, descriptor.private_name)
        del d.q  # Does not raise error
        q = Mock()
        d.q = q
        assert getattr(d, descriptor.private_name) is q
        del d.q
        assert not hasattr(d, descriptor.private_name)

    def test_fval(self):
        fval = Mock()
        descriptor = quality(fval=fval)
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        q = Mock()
        d.q = q
        fval.assert_called_once_with(d, q)

    def test_feff(self):
        feff = Mock()
        descriptor = quality(feff=feff)
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        q = Mock()
        d.q = q
        feff.assert_called_once_with(d)
        feff.reset_mock()
        del d.q
        feff.assert_called_once_with(d)


@mark.parametrize(
    "kwargs",
    [
        {"default": UNSET, "null": UNSET},
        {"default": EqualCopies("default"), "null": UNSET},
        {"default": UNSET, "null": EqualCopies("null")},
        {"default": EqualCopies("default"), "null": EqualCopies("null")},
    ],
)
class TestQualityDescriptorSet:
    """Test `quality` descriptor `__set__` logic."""

    def test_unset(self, kwargs):
        default = kwargs.get("default")
        null = kwargs.get("null")
        descriptor = quality(**kwargs)
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        expected = None if default is UNSET and null is UNSET else default or null
        assert d.q == expected
        assert d.q == getattr(d, descriptor.private_name)

    def test_none(self, kwargs):
        default = kwargs.get("default")
        null = kwargs.get("null")
        descriptor = quality(**kwargs)
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        d.q = None
        expected = None if default is UNSET and null is UNSET else null or default
        assert d.q == expected
        assert d.q == getattr(d, descriptor.private_name)

    def test_ellipsis(self, kwargs):
        default = kwargs.get("default")
        null = kwargs.get("null")
        descriptor = quality(**kwargs)
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        d.q = ...
        expected = ... if default is UNSET and null is UNSET else default or null
        assert d.q == expected
        assert d.q == getattr(d, descriptor.private_name)

    def test_set(self, kwargs):
        descriptor = quality(**kwargs)
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        q = Mock()
        d.q = q
        assert d.q is q
        assert d.q is getattr(d, descriptor.private_name)


class TestQualityDecorators:
    """Test `quality` descriptor decorators."""

    def test_validator(self):
        """Test validator decorator."""
        q = quality()
        fval = Mock()
        assert q.fval is not fval
        q = q.validator(fval)
        assert q.fval is fval

    def test_side_effect(self):
        """Test side effect decorator."""
        q = quality()
        feff = Mock()
        assert q.feff is not feff
        q = q.side_effect(feff)
        assert q.feff is feff
