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
from typing import Any

from numpy import array, dtype, float_, mean, ndarray, sqrt, zeros
from scipy.optimize import curve_fit

from zne.types import Metadata

from .extrapolator import Extrapolator, ReckoningResult

################################################################################
## GENERAL
################################################################################
_RegressionData = namedtuple("_RegressionData", ("x_data", "y_data", "sigma_x", "sigma_y"))


class PolynomialExtrapolator(Extrapolator):
    """Polynomial ordinary-least-squares (OLS) extrapolator."""

    def __init__(self, degree: int = 1):  # pylint: disable=super-init-not-called
        """Initializes the Polynomial extrapolator.

        Args:
            degree: The degree of the polynomial regression curve.

        Raises:
            ValueError: If degree is less than one.
        """
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
        x_data: "ndarray[Any, dtype[float_]]",
        y_data: "ndarray[Any, dtype[float_]]",
        sigma_x: "ndarray[Any, dtype[float_]]",
        sigma_y: "ndarray[Any, dtype[float_]]",
    ) -> ReckoningResult:
        # TODO: if curve fit fails (e.g. p-value test) warn and return closest to zero
        regression_data = _RegressionData(x_data, y_data, sigma_x, sigma_y)
        return self._infer(0, regression_data)

    ################################################################################
    ## AUXILIARY
    ################################################################################
    def _infer(self, target: float, regression_data: _RegressionData) -> ReckoningResult:
        """Fit regression model from data and infer evaluation for target value."""
        coefficients, covariance_matrix = curve_fit(
            self._model,
            regression_data.x_data,
            regression_data.y_data,
            sigma=regression_data.sigma_y,
            absolute_sigma=True,
            p0=zeros(self.degree + 1),  # Note: Initial point determines number of d.o.f.
        )
        target_powers = array([target**p for p in range(self.degree + 1)])
        value = target_powers @ coefficients  # Note: == self._model(target, *coefficients)
        variance = target_powers @ covariance_matrix @ target_powers
        std_error = sqrt(variance)
        metadata = self._build_metadata(
            regression_data.x_data,
            regression_data.y_data,
            coefficients,
            covariance_matrix,
        )
        return ReckoningResult(value.tolist(), std_error.tolist(), metadata)

    @staticmethod
    def _model(x, *coefficients):  # pylint: disable=invalid-name
        """Polynomial regression model for curve fitting."""
        x = array(x)
        return sum(c * (x**i) for i, c in enumerate(coefficients))

    def _build_metadata(
        self,
        x_data: "ndarray[Any, dtype[float_]]",
        y_data: "ndarray[Any, dtype[float_]]",
        coefficients: "ndarray[Any, dtype[float_]]",
        covariance_matrix: "ndarray[Any, dtype[float_]]",
    ) -> Metadata:
        """Build regression metadata."""
        residuals = y_data - self._model(x_data, *coefficients)
        r_squared = self._r_squared(y_data, residuals)
        return {
            "coefficients": tuple(coefficients.tolist()),
            "covariance_matrix": tuple(tuple(r) for r in covariance_matrix.tolist()),
            "residuals": tuple(residuals.tolist()),
            "R2": r_squared.tolist(),
            # TODO: CHI2, p_value, ...
        }

    @staticmethod
    def _r_squared(
        y_data: "ndarray[Any, dtype[float_]]", residuals: "ndarray[Any, dtype[float_]]"
    ) -> float_:
        """Compute R-squared (i.e. coefficient of determination)."""
        y_diff = y_data - mean(y_data)
        TSS = y_diff @ y_diff  # pylint: disable=invalid-name
        RSS = residuals @ residuals  # pylint: disable=invalid-name
        return 1 - RSS / TSS


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
