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

"""Polynomial extrapolator."""

from __future__ import annotations

from collections import namedtuple

from numpy import array, ndarray, sqrt, zeros
from scipy.optimize import curve_fit

from .extrapolator import OLSExtrapolator, ReckoningResult

################################################################################
## GENERAL
################################################################################
_RegressionData = namedtuple("_RegressionData", ("x_data", "y_data", "sigma_x", "sigma_y"))


class PolynomialExtrapolator(OLSExtrapolator):
    """Polynomial ordinary-least-squares (OLS) extrapolator.

    Args:
        degree: The degree of the polynomial regression curve.
    """

    def __init__(self, degree: int = 1):  # pylint: disable=super-init-not-called
        self._set_degree(degree)

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def degree(self) -> int:
        """The degree of the regression polynomial."""
        return self._degree

    def _set_degree(self, degree: int) -> None:
        """Degree setter."""
        degree = int(degree)
        if degree < 1:
            raise ValueError("Polynomial degree must be at least 1.")
        self._degree: int = degree

    ################################################################################
    ## IMPLEMENTATION
    ################################################################################
    @property
    def min_points(self) -> int:
        return self.degree + 1

    # pylint: disable=duplicate-code
    def _extrapolate_zero(
        self,
        x_data: tuple[float, ...],
        y_data: tuple[float, ...],
        sigma_x: tuple[float, ...],
        sigma_y: tuple[float, ...],
    ) -> ReckoningResult:
        # TODO: if curve fit fails (e.g. p-value test) warn and return closest to zero
        regression_data = _RegressionData(x_data, y_data, sigma_x, sigma_y)
        return self._infer(0, regression_data)

    def _model(self, x, *coefficients) -> ndarray:  # pylint: disable=invalid-name
        """Polynomial regression model for curve fitting."""
        x = array(x)
        return sum(c * (x**i) for i, c in enumerate(coefficients))

    ################################################################################
    ## AUXILIARY
    ################################################################################
    def _infer(self, target: float, regression_data: _RegressionData) -> ReckoningResult:
        """Fit regression model from data and infer evaluation for target value.

        Args:
            target: The target X value to infer a Y value for.
            regression_data: A four-tuple of tuples representing X-data, Y-data,
                and corresponding std errors for the X and Y data respectively.

        Returns:
            Reckoning result holding the inferred value, std error, and metadata about
            the curve fit procedure.
        """
        coefficients, covariance_matrix = curve_fit(
            self._model,
            regression_data.x_data,
            regression_data.y_data,
            sigma=self._compute_sigma(regression_data.y_data, regression_data.sigma_y),
            absolute_sigma=True,
            p0=zeros(self.degree + 1),  # Note: Initial point determines number of d.o.f.
        )
        target_powers = array([target**p for p in range(self.degree + 1)])
        value = target_powers @ coefficients  # Note: == self._model(target, *coefficients)
        variance = target_powers @ covariance_matrix @ target_powers
        std_error = sqrt(variance)
        metadata = self._build_metadata(
            array(regression_data.x_data),
            array(regression_data.y_data),
            coefficients,
            covariance_matrix,
        )
        return ReckoningResult(value.tolist(), std_error.tolist(), metadata)


################################################################################
## FACADES
################################################################################
class LinearExtrapolator(PolynomialExtrapolator):
    """Linear ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(degree=1)


class QuadraticExtrapolator(PolynomialExtrapolator):
    """Quadratic ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(degree=2)


class CubicExtrapolator(PolynomialExtrapolator):
    """Cubic ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(degree=3)


class QuarticExtrapolator(PolynomialExtrapolator):
    """Quartic ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(degree=4)
