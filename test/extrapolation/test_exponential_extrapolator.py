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


from test import NO_INTS

from numpy import allclose, exp, random
from pytest import mark, raises

from zne.extrapolation import (
    BiExponentialExtrapolator,
    ExponentialExtrapolator,
    QuadExponentialExtrapolator,
    TriExponentialExtrapolator,
    UniExponentialExtrapolator,
)
from zne.utils.grouping import group_elements_gen
from zne.utils.unset import UNSET

################################################################################
## AUXILIARY
################################################################################
ATOL: float = 1e-2
RTOL: float = 1e-5


def extrapolate_zero_test_cases(max_num_terms):
    for num_terms in range(1, max_num_terms + 1):  # All num_terms up to max
        for coefficients in (
            [1 for _ in range(num_terms * 2)],
            # [1 + c for c in range(num_terms * 2)],
            # [1 / (1 + c) for c in range(num_terms * 2)],
            # [ (-1)**(c % 2) * (1 + c) for c in range(num_terms * 2)],
        ):  # Different curves
            model = lambda x: sum(a * exp(t * x) for a, t in group_elements_gen(coefficients, 2))
            for extra in range(5):  # Different number of data points
                x_data = [1 + x for x in range(num_terms * 2 + extra)]
                y_data = [model(x) + random.normal(0, 1e-4) for x in x_data]
                sigma_y = [random.normal(0.1, 1e-4) for _ in y_data]
                expected = model(0)
                yield num_terms, x_data, y_data, sigma_y, expected


################################################################################
## EXTRAPOLATORS
################################################################################
class TestExponentialExtrapolator:
    """Test polynomial extrapolator."""

    ################################################################################
    ## TESTS
    ################################################################################
    @mark.parametrize(
        "num_terms",
        cases := range(1, 5 + 1),
        ids=[f"num_terms = {num_terms!r}" for num_terms in cases],
    )
    def test_num_terms(self, num_terms):
        """Test num_terms."""
        extrapolator = ExponentialExtrapolator(num_terms=num_terms)
        assert isinstance(extrapolator.num_terms, int)
        assert extrapolator.num_terms == num_terms
        extrapolator = ExponentialExtrapolator(num_terms=str(num_terms))
        assert isinstance(extrapolator.num_terms, int)
        assert extrapolator.num_terms == num_terms
        extrapolator = ExponentialExtrapolator(num_terms=float(num_terms))
        assert isinstance(extrapolator.num_terms, int)
        assert extrapolator.num_terms == num_terms

    @mark.parametrize(
        "num_terms",
        cases := [d for d in NO_INTS if not isinstance(d, (str, float))],
        ids=[f"num_terms = {num_terms!r}" for num_terms in cases],
    )
    def test_num_terms_type_error(self, num_terms):
        """Test num_terms type error."""
        with raises(TypeError):
            ExponentialExtrapolator(num_terms)

    @mark.parametrize(
        "num_terms",
        cases := list(range(0, -5, -1)) + [str(float(d)) for d in range(1, 5 + 1)],
        ids=[f"num_terms = {num_terms!r}" for num_terms in cases],
    )
    def test_num_terms_value_error(self, num_terms):
        """Test num_terms value error."""
        with raises(ValueError):
            ExponentialExtrapolator(num_terms)

    @mark.parametrize(
        "num_terms", cases := range(1, 5 + 1), ids=[f"{num_terms=}" for num_terms in cases]
    )
    def test_min_points(self, num_terms):
        """Test min points."""
        extrapolator = ExponentialExtrapolator(num_terms=num_terms)
        assert extrapolator.min_points == num_terms * 2

    @mark.parametrize(
        "num_terms, x_data, y_data, sigma_y, expected",
        [*extrapolate_zero_test_cases(5)],
    )
    def test_extrapolate_zero(self, num_terms, x_data, y_data, sigma_y, expected):
        """Test extrapolate zero."""
        extrapolator = ExponentialExtrapolator(num_terms)
        value, std_error, metadata = extrapolator.extrapolate_zero(x_data, y_data, sigma_y=sigma_y)
        assert allclose(value, expected, atol=ATOL, rtol=RTOL)
        assert isinstance(std_error, float)  # TODO: test value
        for key in ["coefficients", "covariance_matrix", "residuals", "R2"]:
            assert metadata.get(key, UNSET) is not UNSET  # TODO: test values


################################################################################
## FACADES
################################################################################
class TestFacades:
    """Test polynomial extrapolator facades."""

    @mark.parametrize(
        "cls, configs",
        [
            (UniExponentialExtrapolator, {"num_terms": 1}),
            (BiExponentialExtrapolator, {"num_terms": 2}),
            (TriExponentialExtrapolator, {"num_terms": 3}),
            (QuadExponentialExtrapolator, {"num_terms": 4}),
        ],
    )
    def test_facades(self, cls, configs):
        """Test polynomial extrapolator facades."""
        # Note: using `strategy` decorator functionality
        assert cls() == ExponentialExtrapolator(**configs)
