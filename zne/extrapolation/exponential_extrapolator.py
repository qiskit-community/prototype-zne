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

"""Multi-exponential ordinary-least-squares (OLS) extrapolator.

Theoretical results [1] point at the multi-exponential model being the
most suitable for performing zero-noise extrapolation; nonetheless, the
nature of this regression model, where all the exponential terms are
identical, make it unstable to fit in practice [2] for more than one
exponential term. For the sake of generality, this class provides an
extrapolator for the multi-exponential regression model OLS fitted:
`shift + sum(amplitude[i] * exp(-rate[i] * x) for i in range(num_terms))`

Notice that a multi-exponential decay always tends towards zero, however,
a general observable will tend towards the average of its eigenvalues
(i.e. trace over the number of dimensions) for a state closer and closer
to the complete mixed state (i.e. as noise increases). Generally speaking,
such average will not be zero, and therefore, the multi-exponential decay
will not be a valid model in all scenarios. Nonetheless, by expressing
such general observable as a sum Pauli operators, it is easy to notice
that the only non-traceless element will be the one associated to the
identity operator (i.e. other Paulis are always traceless), hence
determining the expectation value that the general observable will tend
towards. Since the expectation value of the identity operator is trivial
to obtain, by virtue of subtracting such term from the sum of Paulis, the
remaining observable will naturally tend towards zero just as the
multi-exponential model assumes. However, coherent noise can make the
expected asymptote to drift. For that reason, this regression model
includes one extra shift coefficient in the form of a constant factor
added to the exponential terms globally.

Extrapolating constant noise profiles will generally fail due to a poor
convergence of the model. There are several reasons for this:
    1. Assuming all decay rates are fitted to zero, there is ambiguity in
    how the constant factor should be distributed across the shift
    coefficient and the amplitudes.
    2. Even with non-zero amplitude coefficients, one could fit
    arbitrarily many data points on the constant by virtue of boosting
    the decay rates; as this will make the contributions from the
    exponential terms arbitrarily close to zero for value of `x!=0`.

There are two main scenarios in the context of ZNE when this is relevant:
    1. If noise saturation has been reached for all input data points;
    in which case no relevant information can be extracted and
    extrapolation is therefore meaningless.
    2. If the desired mitigated value is close to the decayed value;
    in which case the instability will prevent from achieving meaningful
    error mitigation by providing either bad accuracy, precision or both.

Solving for this phenomena is beyond the scope of this class, but users
may consider techniques such as:
    1. After extrapolation: Comparing with other extrapolation methods
    (e.g. linear) and choosing the result based on metrics such as the std
    error of the extrapolated value, or goodness of fit.
    2. Before extrapolation: trying to predict whether the profile
    corresponds to a constant before fitting by pre-analyzing the data
    points, and manually assigning the coefficient values if so.

Notice however that, a priori, there is no way to identify which of the
possible scenarios we may be operating under. Therefore, one always has to
be wary of constant noise profiles regardless of the extrapolator;
as sometimes they will carry no information about the ideal value (i.e.
scenario #1), and sometimes they will portray relevant information and
be meaningful (i.e. scenario #2).

References:
    [1] Cai, Zhenyu. "Multi-exponential error extrapolation and combining
    error mitigation techniques for NISQ applications." npj Quantum
    Information 7 (2020): 1-12.
    [2] Bi, C., Fishbein, K., Bouhrara, M. et al. "Stabilization of
    parameter estimates from multiexponential decay through extension
    into higher dimensions." Sci Rep 12, 5773 (2022).
"""

from __future__ import annotations

from numpy import array, exp, inf, ndarray, ones, sqrt
from scipy.optimize import curve_fit

from zne.utils.grouping import group_elements_gen

from .extrapolator import OLSExtrapolator, ReckoningResult


################################################################################
## GENERAL
################################################################################
class MultiExponentialExtrapolator(OLSExtrapolator):
    """Multi-exponential ordinary-least-squares (OLS) extrapolator.

    Args:
        num_terms: The number of exponential terms `amplitude * exp(-rate * x)`
            added together in the regression model.
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
        return self.num_terms * 2 + 1

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
            sigma=self._compute_sigma(y_data, sigma_y),
            absolute_sigma=True,
            p0=[2 ** (-i) for i in range(self.num_terms * 2 + 1)],
            bounds=([-inf] + [-inf, 0] * self.num_terms, inf),  # Note: only decay considered
            max_nfev=None,
        )
        value = self._model(0, *coefficients)
        entries = ones(self.num_terms * 2 + 1)
        entries[2::2] = 0  # Note: decay rate coefficients not relevant for x=0
        variance = entries @ covariance_matrix @ entries
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
        shift = coefficients[0]
        exp_coefficients = coefficients[1:]
        exponential = sum(
            amplitude * exp(-rate * x)  # Note: decay for positive values of `rate`
            for amplitude, rate in group_elements_gen(exp_coefficients, group_size=2)
        )
        return exponential + shift


################################################################################
## FACADES
################################################################################
class MonoExponentialExtrapolator(MultiExponentialExtrapolator):
    """Mono-exponential ordinary-least-squares (OLS) extrapolator."""

    def __init__(self):
        super().__init__(num_terms=1)


class BiExponentialExtrapolator(MultiExponentialExtrapolator):
    """Bi-exponential ordinary-least-squares (OLS) extrapolator.

    Note: The convergence of this model is unstable. Proceed with caution.
    """

    def __init__(self):
        super().__init__(num_terms=2)


class ExponentialExtrapolator(MonoExponentialExtrapolator):
    """Exponential ordinary-least-squares (OLS) extrapolator."""
