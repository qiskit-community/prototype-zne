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

"""Class constant descriptor."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class classconstant:  # pylint: disable=invalid-name

    """Class constant descriptor.

    Args:
        value: the constant value to store at the class level.
        copy: whether to return a deepcopy of the value or the original reference.

    Note: returning constant values by reference is more performant but opens the up
    the possibility to mutating them. For this reason, if the value type is not
    immutable, setting `copy` to `True` is recommended.
    """

    def __init__(self, value: Any, copy: bool = False) -> None:
        self.name: str = ""
        self.value: Any = value
        self.copy: bool = copy

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: object, objtype: type = None) -> Any:
        return deepcopy(self.value) if self.copy else self.value

    def __set__(self, obj: object, value: Any) -> None:
        raise AttributeError(f"Class constant '{self.name}' cannot be assigned.")

    def __delete__(self, obj: object) -> None:
        raise AttributeError(f"Class constant '{self.name}' cannot be deleted.")
