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

from numpy import array, float_, ones

from zne.types import NumericArray
from zne.utils.strategy import strategy

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
        x_data: NumericArray,
        y_data: NumericArray,
        sigma_x: NumericArray,
        sigma_y: NumericArray,
    ) -> ReckoningResult:
        """Core functionality for `extrapolate_zero` after input validation."""
        raise NotImplementedError  # pragma: no cover

    ################################################################################
    ## API
    ################################################################################
    def extrapolate_zero(
        self,
        x_data: Sequence[float] | NumericArray,
        y_data: Sequence[float] | NumericArray,
        sigma_x: Sequence[float] | NumericArray | None = None,
        sigma_y: Sequence[float] | NumericArray | None = None,
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
        sigma_x = self._validate_sigma(sigma_x, default_size=x_data.size)
        sigma_y = self._validate_sigma(sigma_y, default_size=y_data.size)
        # Cross-validation
        num_points = len(set(x_data))
        if num_points < self.min_points:
            raise ValueError(
                f"Insufficient number of distinct data points provided ({num_points}), "
                f"at least {self.min_points} needed."
            )
        sizes = (x_data.size, y_data.size, sigma_x.size, sigma_y.size)
        if any(s != x_data.size for s in sizes):
            raise ValueError(
                "Invalid data, all inputs should be of the same size: "
                f"{x_data.size = }, {y_data.size = }, {sigma_x.size = }, {sigma_y.size = }."
            )
        return self._extrapolate_zero(x_data, y_data, sigma_x, sigma_y)

    ################################################################################
    ## VALIDATION
    ################################################################################
    def _validate_data(self, data: Sequence[float] | NumericArray) -> NumericArray:
        """Validates data for the regression model.

        Args:
            data: A sequence of values for the regression model.

        Returns:
            Validated data normalized.
        """
        try:
            data = array(data).astype(float_, casting="same_kind")
        except TypeError as exc:
            raise TypeError(f"Invalid non-numeric (i.e. non-real) data array: {data}.") from exc
        if len(data.shape) != 1:
            raise ValueError(
                "Invalid regression data provided, expected one dimensional sequence of floats."
            )
        return data

    def _validate_sigma(
        self,
        sigma: Sequence[float] | NumericArray | None,
        default_size: int,
    ) -> NumericArray | None:
        """Validates sigma for the regression model data.

        Args:
            sigma: A sequence of values for the std error in the regression model data.
            default_size: Default size of the sigma to be returned if `None`.

        Returns:
            Validated sigma normalized. If `None`, ones of default size is returned.
        """
        if sigma is None:
            sigma = ones(default_size)  # Note: zeros mean that the data is exact
        return self._validate_data(sigma)
