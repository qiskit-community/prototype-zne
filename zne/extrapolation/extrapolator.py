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

"""Interface for extrapolation strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import namedtuple
from collections.abc import Sequence

from numpy import array
from numpy import float_ as npfloat
from numpy import isclose, mean, ndarray, ones

from zne.types import Metadata
from zne.utils.strategy import strategy
from zne.utils.typing import isreal, normalize_array

# TODO: import from staged_primitives
ReckoningResult = namedtuple("ReckoningResult", ("value", "std_error", "metadata"))


################################################################################
## EXTRAPOLATOR
################################################################################
@strategy
class Extrapolator(ABC):
    """Interface for extrapolation strategies."""

    @property
    @abstractmethod
    def min_points(self) -> int:
        """The minimum number of data points required to fit the regression model."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _extrapolate_zero(
        self,
        x_data: tuple[float, ...],
        y_data: tuple[float, ...],
        sigma_x: tuple[float, ...],
        sigma_y: tuple[float, ...],
    ) -> ReckoningResult:
        """Core functionality for `extrapolate_zero` after input validation."""
        raise NotImplementedError  # pragma: no cover

    ################################################################################
    ## API
    ################################################################################
    def extrapolate_zero(
        self,
        x_data: Sequence[float],
        y_data: Sequence[float],
        sigma_x: Sequence[float] | None = None,
        sigma_y: Sequence[float] | None = None,
    ) -> ReckoningResult:
        """Extrapolate to zero by fitting a regression model to the provided data.

        Args:
            x_data: A sequence of X values for the data points to fit.
            y_data: A sequence of Y values for the data points to fit.
            sigma_x: A sequence of std errors along the X axis for the data points to fit.
                If `None`, ones of `x_data` size is assumed.
            sigma_y: A sequence of std errors along the Y axis for the data points to fit.
                If `None`, ones of `y_data` size is assumed.

        Returns:
            A ReckoningResult namedtuple object holding the extrapolated value, std error,
            and metadata.
        """
        x_data = self._validate_data(x_data)
        y_data = self._validate_data(y_data)
        sigma_x = self._validate_sigma(sigma_x, default_size=len(x_data))
        sigma_y = self._validate_sigma(sigma_y, default_size=len(y_data))
        self._cross_validate_data_sigma(x_data, y_data, sigma_x, sigma_y)
        self._validate_min_points(x_data, y_data)
        return self._extrapolate_zero(x_data, y_data, sigma_x, sigma_y)

    ################################################################################
    ## VALIDATION
    ################################################################################
    def _validate_data(self, data: Sequence[float]) -> tuple[float, ...]:
        """Validates data for the regression model.

        Args:
            data: A sequence of values for the regression model.

        Returns:
            Validated data normalized.
        """
        if not isinstance(data, Sequence) or not all(isreal(d) for d in data):
            raise TypeError(f"Invalid data {data}, expected sequence of floats.")
        return tuple(data)

    def _validate_sigma(
        self, sigma: Sequence[float] | None, default_size: int
    ) -> tuple[float, ...]:
        """Validates sigma for the regression model data.

        Args:
            sigma: A sequence of values for the std error in the regression model data.
            default_size: Default size of the sigma to be returned if `None`.

        Returns:
            Validated sigma normalized. If `None`, ones of default size is returned.
        """
        if sigma is None:
            sigma = [1] * default_size  # Note: zeros mean that the data is exact
        return self._validate_data(sigma)

    def _cross_validate_data_sigma(
        self,
        x_data: tuple[float, ...],
        y_data: tuple[float, ...],
        sigma_x: tuple[float, ...],
        sigma_y: tuple[float, ...],
    ) -> None:
        """Cross-validate data and sigmas."""
        sizes = {len(x_data), len(y_data), len(sigma_x), len(sigma_y)}
        if len(sizes) != 1:
            raise ValueError(
                "Invalid data, all inputs should be of the same size: "
                f"{len(x_data) = }, {len(y_data) = }, "  # noqa: E251,E202
                f"{len(sigma_x) = }, {len(sigma_y) = }."  # noqa: E251,E202
            )

    def _validate_min_points(
        self,
        x_data: tuple[float, ...],
        y_data: tuple[float, ...],  # pylint: disable=unused-argument
    ) -> None:
        """Validate that min points threshold is achieved."""
        num_points = len(set(x_data))  # TODO: equal up to tolerance
        if num_points < self.min_points:
            raise ValueError(
                f"Insufficient number of distinct data points provided ({num_points}), "
                f"at least {self.min_points} needed."
            )


################################################################################
## OLS EXTRAPOLATOR
################################################################################
class OLSExtrapolator(Extrapolator):
    """Interface for ordinary-least-squares (OLS) extrapolation strategies."""

    @abstractmethod
    def _model(self, x, *coefficients) -> ndarray:  # pylint: disable=invalid-name
        """Regression model for curve fitting."""
        raise NotImplementedError  # pragma: no cover

    ################################################################################
    ## AUXILIARY
    ################################################################################
    def _compute_sigma(
        self,
        y_data: tuple[float, ...],
        sigma_y: tuple[float, ...],
    ) -> ndarray:
        """Compute sensible sigma values for curve fitting.

        This implementation bypasses zero effective variance which would
        lead to numerical errors in the curve fitting procedure.
        """
        values = array(y_data)
        errors = array(sigma_y)
        relative_errors = errors / values
        return ones(errors.shape) if any(isclose(relative_errors, 0)) else errors

    def _build_metadata(
        self,
        x_data: ndarray,
        y_data: ndarray,
        coefficients: ndarray,
        covariance_matrix: ndarray,
    ) -> Metadata:
        """Build regression metadata."""
        residuals = y_data - self._model(x_data, *coefficients)
        r_squared = self._r_squared(y_data, residuals)
        return {
            "coefficients": normalize_array(coefficients),
            "covariance_matrix": normalize_array(covariance_matrix),
            "residuals": normalize_array(residuals),
            "R2": normalize_array(r_squared),
        }

    @staticmethod
    def _r_squared(y_data: ndarray, residuals: ndarray) -> npfloat:
        """Compute R-squared (i.e. coefficient of determination)."""
        y_diff = y_data - mean(y_data)
        TSS = y_diff @ y_diff  # pylint: disable=invalid-name
        RSS = residuals @ residuals  # pylint: disable=invalid-name
        return 1 - RSS / TSS
