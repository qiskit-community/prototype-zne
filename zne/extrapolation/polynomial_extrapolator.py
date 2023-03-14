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

from numpy import array, float_, mean, sqrt, zeros
from scipy.optimize import curve_fit

from zne.types import Metadata, NumericArray

from .extrapolator import Extrapolator, ReckoningResult


################################################################################
## GENERAL
################################################################################
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
        x_data: NumericArray,
        y_data: NumericArray,
        sigma_x: NumericArray,
        sigma_y: NumericArray,
    ) -> ReckoningResult:
        # TODO: if curve fit fails (e.g. p-value test) warn and return closest to zero
        regression_data = (x_data, y_data, sigma_x, sigma_y)
        return self._infer(0, regression_data)

    ################################################################################
    ## AUXILIARY
    ################################################################################
    def _infer(  #
        self,
        target: float,
        regression_data: tuple[NumericArray, NumericArray, NumericArray, NumericArray],
    ) -> ReckoningResult:
        """Fit regression model from data and infer evaluation for target value."""
        x_data, y_data, _, sigma_y = regression_data
        coefficients, covariance_matrix = curve_fit(
            self._model,
            x_data,
            y_data,
            sigma=sigma_y,
            absolute_sigma=True,
            p0=zeros(self.degree + 1),  # Note: Initial point determines number of d.o.f.
        )
        target_powers = array([target**p for p in range(self.degree + 1)])
        value = target_powers @ coefficients  # Note: == self._model(target, *coefficients)
        variance = target_powers @ covariance_matrix @ target_powers
        std_error = sqrt(variance)
        metadata = self._build_metadata(x_data, y_data, coefficients, covariance_matrix)
        return ReckoningResult(value.tolist(), std_error.tolist(), metadata)

    @staticmethod
    def _model(x, *coefficients):  # pylint: disable=invalid-name
        """Polynomial regression model for curve fitting."""
        x = array(x)
        return sum(c * (x**i) for i, c in enumerate(coefficients))

    def _build_metadata(
        self,
        x_data: NumericArray,
        y_data: NumericArray,
        coefficients: NumericArray,
        covariance_matrix: NumericArray,
    ) -> Metadata:
        """Build regression metadata."""
        residuals = y_data - self._model(x_data, *coefficients)
        r_squared = self._r_squared(y_data, residuals)
        return {
            "coefficients": coefficients.tolist(),
            "covariance_matrix": covariance_matrix.tolist(),
            "residuals": residuals.tolist(),
            "R2": r_squared.tolist(),
            # TODO: CHI2, p_value, ...
        }

    @staticmethod
    def _r_squared(y_data: NumericArray, residuals: NumericArray) -> float_:
        """Compute R-squared (i.e. coefficient of determination)."""
        y_diff = y_data - mean(y_data)
        TSS = y_diff @ y_diff  # pylint: disable=invalid-name
        RSS = residuals @ residuals  # pylint: disable=invalid-name
        return 1 - RSS / TSS  # type: ignore


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
