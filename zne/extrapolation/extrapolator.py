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

"""Interface for extrapolation strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..immutable_strategy import ImmutableStrategy
from ..types import Metadata, RegressionDatum, RegressionModel


class Extrapolator(ImmutableStrategy, ABC):
    """Interface for extrapolation strategies."""

    @property
    @abstractmethod
    def min_points(self) -> int:
        """The minimum number of data points required to fit the regression model."""

    @abstractmethod
    def _fit_regression_model(
        self, data: tuple[RegressionDatum, ...]
    ) -> tuple[RegressionModel, Metadata]:
        """Core functionality for `fit_regression_model` after input normalization."""

    ################################################################################
    ## API
    ################################################################################
    def fit_regression_model(
        self, data: Sequence[Sequence[float]]
    ) -> tuple[RegressionModel, Metadata]:
        """Fit regression model given data points.

        Args:
            data: A sequence of data points to fit the regression model from, each of which
                consisting on the value of the regressor, measured mean, and estimated variance.

        Returns:
            A two-tuple consisting on a callable, representing the fitted model, and
                metadata about the fitting process. The model callable takes in a target
                float value for the regressor, and returns two floats representing the
                inferred value of the regressand and its associated variance.
        """
        data = self._validate_data(data)
        return self._fit_regression_model(data)

    def infer(self, target: float, data: Sequence[Sequence[float]]) -> tuple[float, Metadata]:
        """Infer a prediction for the target value of the regressor based on data.

        Args:
            target: A target value for the regressor.
            data: A sequence of data points to fit the regression model from, each of which
                consisting on the value of the regressor, measured mean, and estimated variance.

        Returns:
            A two-tuple consisting on the inferred value of the regressand and metadata.
        """
        model, metadata = self.fit_regression_model(data)
        prediction, variance = model(target)
        if variance is not None:
            metadata = {"variance": variance, **metadata}
        return prediction, metadata

    def extrapolate_zero(self, data: Sequence[Sequence[float]]) -> tuple[float, Metadata]:
        """Same as `infer` but fixing `target = 0`."""
        return self.infer(0, data)

    ################################################################################
    ## VALIDATION
    ################################################################################
    def _validate_data(self, data: Sequence[Sequence[float]]) -> tuple[RegressionDatum, ...]:
        """Validates data points for the regression model.

        Args:
            data: A sequence of data points to fit the regression model from, each of which
                consisting on the value of the regressor, measured mean, and estimated variance.

        Returns:
            Validated data normalized.

        Raises:
            TypeError: If provided data is not a valid sequence of data points.
            ValueError: If the number of data points is smaller than the minimum required
                number of data points for the given Estrapolator.
        """
        if not isinstance(data, Sequence) or not all(
            isinstance(d, Sequence) and len(d) == 3 and all(isinstance(v, (float, int)) for v in d)
            for d in data
        ):
            raise TypeError(
                "Invalid data provided, expeceted Sequence[Sequence[float, float, float]]."
            )
        if len(data) < self.min_points:
            raise ValueError(
                f"At least {self.min_points} data point{'s' if self.min_points != 1 else ''} "
                "must be provided to fit the regression model."
            )
        return tuple(tuple(d) for d in data)  # type: ignore
