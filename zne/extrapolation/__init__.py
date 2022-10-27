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

"""Extrapolation library."""

from ..utils import build_dict_library
from .extrapolator import Extrapolator
from .polynomial_extrapolator import (
    CubicExtrapolator,
    LinearExtrapolator,
    PolynomialExtrapolator,
    QuadraticExtrapolator,
    QuarticExtrapolator,
)

EXTRAPOLATOR_LIBRARY: dict = build_dict_library(
    PolynomialExtrapolator,
    LinearExtrapolator,
    QuadraticExtrapolator,
    CubicExtrapolator,
    QuarticExtrapolator,
)

__all__ = ["Extrapolator", *EXTRAPOLATOR_LIBRARY.keys()]
