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

from zne.utils.strategy import strategy
from zne.utils.typing import isreal

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
            A ReckoningResult object with the extrapolated value, std error, and metadata.
        """
        # Single validation
        x_data = self._validate_data(x_data)
        y_data = self._validate_data(y_data)
        sigma_x = self._validate_sigma(sigma_x, default_size=len(x_data))
        sigma_y = self._validate_sigma(sigma_y, default_size=len(y_data))
        # Cross-validation
        sizes = (len(x_data), len(y_data), len(sigma_x), len(sigma_y))
        if len(set(sizes)) != 1:
            raise ValueError(
                "Invalid data, all inputs should be of the same size: "
                f"{len(x_data) = }, {len(y_data) = }, {len(sigma_x) = }, {len(sigma_y) = }."
            )
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
        if len(data) < self.min_points:
            raise ValueError(
                f"Insufficient number of distinct data points provided ({len(data)}), "
                f"at least {self.min_points} needed."
            )
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
