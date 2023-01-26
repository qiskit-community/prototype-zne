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

"""Module for singleton type to represent unset args."""

from __future__ import annotations

from typing import Any


class UnsetType:
    """Singleton type to represent unset args."""

    __slots__ = ()

    def __new__(cls) -> UnsetType:
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __bool__(self) -> bool:
        return False

    def __eq__(self, __o: Any) -> bool:
        return self is __o

    def __repr__(self) -> str:
        return "UNSET"

    def __copy__(self) -> UnsetType:
        return self

    def __deepcopy__(self, memo: dict) -> UnsetType:
        return self


UNSET = UnsetType()
