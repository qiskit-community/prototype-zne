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

from numpy import array, exp, inf, ndarray, ones, sqrt
from scipy.optimize import curve_fit

from zne.utils.grouping import group_elements_gen

from .extrapolator import OLSExtrapolator, ReckoningResult


################################################################################
## GENERAL
################################################################################
class ExponentialExtrapolator(OLSExtrapolator):
    """Exponential ordinary-least-squares (OLS) extrapolator.

    Args:
        num_terms: The number of exponential terms `amp * exp(tau * x)`
            added in the regression model.
    """

    def __init__(self, num_terms: int = 1):  # pylint: disable=super-init-not-called
        self._set_num_terms(num_terms)

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def num_terms(self) -> int:
        """The number of exponential terms added in the regression model."""
        return self._num_terms

    def _set_num_terms(self, num_terms: int) -> None:
        """Number of terms setter."""
        num_terms = int(num_terms)
        if num_terms < 1:
            raise ValueError("Number of exponential terms must be at least 1.")
        self._num_terms: int = num_terms

    ################################################################################
    ## IMPLEMENTATION
    ################################################################################
    @property
    def min_points(self) -> int:
        return self.num_terms * 2

    # pylint: disable=duplicate-code
    def _extrapolate_zero(
        self,
        x_data: tuple[float, ...],
        y_data: tuple[float, ...],
        sigma_x: tuple[float, ...],  # pylint: disable=unused-argument
        sigma_y: tuple[float, ...],
    ) -> ReckoningResult:
        coefficients, covariance_matrix = curve_fit(
            self._model,
            x_data,
            y_data,
            sigma=sigma_y,
            absolute_sigma=True,
            p0=ones(self.num_terms * 2),
            bounds=(-inf, [inf, 7e2 / max(x_data)] * self.num_terms),
        )
        value = self._model(0, *coefficients)
        entries = ones(self.num_terms)  # Note: entries for to amplitude coefficients
        variance = entries @ covariance_matrix[::2, ::2] @ entries
        std_error = sqrt(variance)
        metadata = self._build_metadata(
            array(x_data),
            array(y_data),
            coefficients,
            covariance_matrix,
        )
        return ReckoningResult(value.tolist(), std_error.tolist(), metadata)

    def _model(self, x, *coefficients) -> ndarray:  # pylint: disable=invalid-name
        """Exponential regression model for curve fitting."""
        x = array(x)
        return sum(
            amp * exp(tau * x) for amp, tau in group_elements_gen(coefficients, group_size=2)
        )


################################################################################
## FACADES
################################################################################
class UniExponentialExtrapolator(ExponentialExtrapolator):
    """Uni-exponential ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(num_terms=1)


class BiExponentialExtrapolator(ExponentialExtrapolator):
    """Bi-exponential ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(num_terms=2)


class TriExponentialExtrapolator(ExponentialExtrapolator):
    """Tri-exponential ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(num_terms=3)


class QuadExponentialExtrapolator(ExponentialExtrapolator):
    """Quad-exponential ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(num_terms=4)
