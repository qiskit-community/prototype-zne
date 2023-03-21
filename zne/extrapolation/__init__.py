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

"""Extrapolation library."""

from .exponential_extrapolator import (
    BiExponentialExtrapolator,
    ExponentialExtrapolator,
    MonoExponentialExtrapolator,
    MultiExponentialExtrapolator,
)
from .extrapolator import Extrapolator, OLSExtrapolator, ReckoningResult
from .polynomial_extrapolator import (
    CubicExtrapolator,
    LinearExtrapolator,
    PolynomialExtrapolator,
    QuadraticExtrapolator,
    QuarticExtrapolator,
)

EXTRAPOLATOR_LIBRARY = {
    cls.__name__: cls
    for cls in (
        PolynomialExtrapolator,
        LinearExtrapolator,
        QuadraticExtrapolator,
        CubicExtrapolator,
        QuarticExtrapolator,
        MultiExponentialExtrapolator,
        ExponentialExtrapolator,
        MonoExponentialExtrapolator,
        BiExponentialExtrapolator,
    )
}

__all__ = [
    "Extrapolator",
    "OLSExtrapolator",
    "ReckoningResult",
    *EXTRAPOLATOR_LIBRARY.keys(),
]
