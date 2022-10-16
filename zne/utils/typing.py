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

"""Type checking utils module."""

from typing import Any


def isint(obj: Any) -> bool:
    """Check if object is int"""
    return isinstance(obj, int) and not isinstance(obj, bool)


def isinteger(obj: Any) -> bool:
    """Check if object is an integer number"""
    return isint(obj) or isinstance(obj, float) and obj.is_integer()


def isreal(obj: Any) -> bool:
    """Check if object is a real number: int or float minus ``±Inf`` and ``NaN``."""
    return isint(obj) or isinstance(obj, float) and float("-Inf") < obj < float("Inf")
