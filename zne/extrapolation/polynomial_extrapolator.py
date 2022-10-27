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

"""Polynomial extrapolator."""

from __future__ import annotations

from functools import cached_property

from numpy.polynomial import Polynomial

from ..types import Metadata, RegressionDatum, RegressionModel
from .extrapolator import Extrapolator


################################################################################
## GENERAL
################################################################################
class PolynomialExtrapolator(Extrapolator):
    """Polynomial regression based extrapolator."""

    def __init__(self, degree: int = 1):  # pylint: disable=super-init-not-called
        """Initializes the Polynomial extrapolator.

        Args:
            degree: The degree of the polynomial regression curve.

        Raises:
            ValueError: If degree is less than one.
        """
        if degree < 1:
            raise ValueError("Polynomial degree must be at least 1.")
        self._degree: int = degree

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def degree(self) -> int:
        """The degree of the polynomial."""
        return self._degree

    ################################################################################
    ## IMPLEMENTATION
    ################################################################################
    @cached_property
    def min_points(self) -> int:
        return self.degree + 1

    def _fit_regression_model(
        self, data: tuple[RegressionDatum, ...]
    ) -> tuple[RegressionModel, Metadata]:
        x, y, _ = zip(*data)  # pylint: disable=invalid-name
        fit = Polynomial.fit(x, y, deg=self.degree)
        model = lambda target: (fit(target), None)  # TODO: calculate variance of fitted
        return model, {}


################################################################################
## FACADES
################################################################################
class LinearExtrapolator(PolynomialExtrapolator):
    """Linear extrapolator."""

    def __init__(self):
        super().__init__(degree=1)


class QuadraticExtrapolator(PolynomialExtrapolator):
    """Quadratic extrapolator."""

    def __init__(self):
        super().__init__(degree=2)


class CubicExtrapolator(PolynomialExtrapolator):
    """Cubic extrapolator."""

    def __init__(self):
        super().__init__(degree=3)


class QuarticExtrapolator(PolynomialExtrapolator):
    """Quartic extrapolator."""

    def __init__(self):
        super().__init__(degree=4)
