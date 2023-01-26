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

from copy import copy, deepcopy
from typing import Any
from unittest.mock import Mock

from pytest import mark, raises

from zne.utils.unset import UNSET
from zne.utils.validation import quality


################################################################################
## AUXILIARY
################################################################################
class EqualCopies:
    """Auxiliary wrapper class to check that deepcopies are equal but not the same object."""

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

    def test_uset_name(self):
        q = quality()
        assert q.name is None
        assert q.private_name is None


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
        for key, value in kwargs.items():
            assert getattr(qq, key) is value
            assert getattr(q, key) is not value

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
        for key, value in kwargs.items():
            assert getattr(qq, key) == value
            assert getattr(q, key) != value

    @mark.parametrize("name", [None, "attr", "name", "foo", "bar"])
    def test_name(self, name):
        q = quality()
        q._name = name
        qq = q()
        assert q is not qq
        assert qq.name == q.name
        assert qq.private_name == q.private_name


@mark.parametrize("name", [None, "attr", "name", "foo", "bar"])
class TestQualityCopy:
    """Test `quality` descriptor copy logic."""

    def test_copy(self, name):
        fval = Mock()
        feff = Mock()
        default = EqualCopies("default")
        null = EqualCopies("null")
        descriptor = quality(fval, feff, default=default, null=null)
        descriptor._name = name
        duplicate = copy(descriptor)
        assert descriptor is not duplicate
        assert descriptor.fval is duplicate.fval
        assert descriptor.feff is duplicate.feff
        assert descriptor.default == duplicate.default
        assert descriptor.null == duplicate.null
        assert descriptor.name == duplicate.name
        assert descriptor.private_name == duplicate.private_name

    def test_deepcopy(self, name):
        fval = EqualCopies("fval")
        feff = EqualCopies("feff")
        default = EqualCopies("default")
        null = EqualCopies("null")
        descriptor = quality(fval, feff, default=default, null=null)
        descriptor._name = name
        duplicate = deepcopy(descriptor, memo := {})

        assert descriptor is not duplicate
        assert descriptor.fval is not duplicate.fval
        assert descriptor.fval == duplicate.fval
        assert descriptor.feff is not duplicate.feff
        assert descriptor.feff == duplicate.feff
        assert descriptor.default is not duplicate.default
        assert descriptor.default == duplicate.default
        assert descriptor.null is not duplicate.null
        assert descriptor.null == duplicate.null
        assert descriptor.name == duplicate.name
        assert descriptor.private_name == duplicate.private_name

        memo_values = [fval, feff, default, null]
        memo_values += [v.__dict__ for v in memo_values]
        for value in memo.values():
            if isinstance(value, quality):
                assert value is duplicate
            elif isinstance(value, list):
                assert descriptor in value
                for v in memo_values:
                    assert v in value
            else:
                assert value in memo_values


class TestQualityProperties:
    """Test `quality` descriptor properties."""

    @mark.parametrize("property", ["default", "null", "name", "private_name"])
    def test_immutable(self, property):
        descriptor = quality()
        with raises(AttributeError):
            setattr(descriptor, property, ...)

    @mark.parametrize("property", ["default", "null"])
    def test_copy(self, property):
        p = EqualCopies(property)
        descriptor = quality(**{property: p})
        assert getattr(descriptor, property) is not p
        assert getattr(descriptor, property) == p


class TestQualityDescriptor:
    """Test `quality` descriptor protocol."""

    @mark.parametrize("attr", [None, "attr", "name", "foo", "bar"])
    def test_set_name(self, attr):
        """Test `quality` descriptor `__set_name__` logic."""
        descriptor = quality()
        type("Dummy", (), {attr: descriptor})
        assert descriptor.name == attr
        assert descriptor.private_name == attr if attr is None else "__quality_" + attr

    def test_get(self):
        """Test `quality` descriptor `__get__` logic."""
        descriptor = quality()
        Dummy = type("Dummy", (), {"q": descriptor})
        assert Dummy.q is descriptor

    @mark.parametrize(
        "kwargs",
        [
            {"default": UNSET, "null": UNSET},
            {"default": EqualCopies("default"), "null": UNSET},
            {"default": UNSET, "null": EqualCopies("null")},
            {"default": EqualCopies("default"), "null": EqualCopies("null")},
        ],
    )
    class TestSet:
        """Test `quality` descriptor `__set__` logic."""

        def test_unset(self, kwargs):
            default = kwargs.get("default")
            null = kwargs.get("null")
            descriptor = quality(**kwargs)
            Dummy = type("Dummy", (), {"q": descriptor})
            d = Dummy()
            expected = None if default is UNSET and null is UNSET else default or null
            assert d.q is not UNSET
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
            assert d.q is not UNSET
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
            assert d.q is not UNSET
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

    def test_delete(self):
        """Test `quality` descriptor `__delete__` logic."""
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
        """Test `quality` descriptor `fval` attribute."""
        fval = Mock()
        descriptor = quality(fval=fval)
        Dummy = type("Dummy", (), {"q": descriptor})
        d = Dummy()
        q = Mock()
        d.q = q
        fval.assert_called_once_with(d, q)

    def test_feff(self):
        """Test `quality` descriptor `feff` attribute."""
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


class TestQualityDecorators:
    """Test `quality` descriptor decorators."""

    def test_validator(self):
        """Test validator decorator."""
        q = quality()
        fval = Mock()
        qq = q.validator(fval)
        assert qq is not q
        assert qq.fval is fval
        assert qq.fval is not q.fval
        assert qq.feff is q.feff
        assert qq.default == q.default
        assert qq.null == q.null
        assert qq.name == q.name
        assert qq.private_name == q.private_name

    def test_side_effect(self):
        """Test side effect decorator."""
        q = quality()
        feff = Mock()
        qq = q.side_effect(feff)
        assert qq is not q
        assert qq.fval is q.fval
        assert qq.feff is feff
        assert qq.feff is not q.feff
        assert qq.default == q.default
        assert qq.null == q.null
        assert qq.name == q.name
        assert qq.private_name == q.private_name
