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

from pytest import mark, raises

from zne.utils.classconstant import classconstant


class TestClassConstant:
    """Test `classconstant` descriptor."""

    @mark.parametrize("value", [0, 1, "pi"])
    def test_get(self, value):
        """Test get."""
        cls = type("cls", (), {"CONSTANT": classconstant(value)})
        assert cls.CONSTANT == value
        assert cls().CONSTANT == value

    def test_set(self):
        """Test set."""
        cls = type("cls", (), {"CONSTANT": classconstant(0)})
        with raises(AttributeError):
            cls().CONSTANT = "value"

    def test_delete(self):
        """Test delete."""
        cls = type("cls", (), {"CONSTANT": classconstant(0)})
        with raises(AttributeError):
            del cls().CONSTANT
