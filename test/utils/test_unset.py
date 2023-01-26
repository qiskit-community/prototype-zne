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

from zne.utils.unset import UNSET, UnsetType


class TestUnsetType:
    """Test `UnsetType` class."""

    def test_singleton(self):
        """Test that class is a singleton."""
        assert UnsetType() is UnsetType()
        assert UNSET is UnsetType()

    def test_bool(self):
        """Test that instances evaluate to `False`."""
        assert not UNSET
        assert not UnsetType()

    def test_eq(self):
        """Test equality."""
        assert UnsetType() == UnsetType()
        assert UNSET == UnsetType()

    def test_repr(sefl):
        """Test string representation."""
        assert str(UNSET) == "UNSET"
        assert repr(UNSET) == "UNSET"

    def test_copy(self):
        """Test copy."""
        assert copy(UNSET) is UNSET

    def test_deepcopy(self):
        """Test deepcopy."""
        assert deepcopy(UNSET, memo := {}) is UNSET
        assert not memo
