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

from numpy import allclose, random
from pytest import mark, raises

from zne.extrapolation import (
    CubicExtrapolator,
    LinearExtrapolator,
    PolynomialExtrapolator,
    QuadraticExtrapolator,
    QuarticExtrapolator,
)
from zne.utils.unset import UNSET

################################################################################
## AUXILIARY
################################################################################
ATOL: float = 1e-2
RTOL: float = 1e-5


def extrapolate_zero_test_cases(max_degree):
    for degree in range(1, max_degree + 1):  # All degrees up to max
        for coefficients in (
            [1 for _ in range(degree + 1)],
            [c for c in range(degree + 1)],
            [1 + c for c in range(degree + 1)],
            [1 - c for c in range(degree + 1)],
        ):  # Different curves
            poly = lambda x: sum(c * (x**p) for p, c in enumerate(coefficients))
            for extra in range(5):  # Different number of data points
                x_data = [1 + x for x in range(degree + 1 + extra)]
                y_data = [poly(x) + random.normal(0, 1e-4) for x in x_data]
                sigma_y = [random.normal(0.1, 1e-4) for _ in y_data]
                expected = poly(0)
                yield degree, x_data, y_data, sigma_y, expected


################################################################################
## EXTRAPOLATORS
################################################################################
class TestPolynomialExtrapolator:

    ################################################################################
    ## TESTS
    ################################################################################
    @mark.parametrize(
        "degree", cases := range(1, 5 + 1), ids=[f"degree = {degree!r}" for degree in cases]
    )
    def test_degree(self, degree):
        """Test degree."""
        extrapolator = PolynomialExtrapolator(degree=degree)
        assert isinstance(extrapolator.degree, int)
        assert extrapolator.degree == degree
        extrapolator = PolynomialExtrapolator(degree=str(degree))
        assert isinstance(extrapolator.degree, int)
        assert extrapolator.degree == degree
        extrapolator = PolynomialExtrapolator(degree=float(degree))
        assert isinstance(extrapolator.degree, int)
        assert extrapolator.degree == degree

    @mark.parametrize(
        "degree",
        cases := [d for d in NO_INTS if not isinstance(d, (str, float))],
        ids=[f"degree = {degree!r}" for degree in cases],
    )
    def test_degree_type_error(self, degree):
        """Test degree type error."""
        with raises(TypeError):
            PolynomialExtrapolator(degree)

    @mark.parametrize(
        "degree",
        cases := list(range(0, -5, -1)) + [str(float(d)) for d in range(1, 5 + 1)],
        ids=[f"degree = {degree!r}" for degree in cases],
    )
    def test_degree_value_error(self, degree):
        """Test degree value error."""
        with raises(ValueError):
            PolynomialExtrapolator(degree)

    @mark.parametrize(
        "degree", cases := range(1, 5 + 1), ids=[f"degree = {degree}" for degree in cases]
    )
    def test_min_points(self, degree):
        """Test min points."""
        extrapolator = PolynomialExtrapolator(degree=degree)
        assert extrapolator.min_points == degree + 1

    @mark.parametrize(
        "degree, x_data, y_data, sigma_y, expected",
        [*extrapolate_zero_test_cases(5)],
    )
    def test_extrapolate_zero(self, degree, x_data, y_data, sigma_y, expected):
        """Test extrapolate zero."""
        extrapolator = PolynomialExtrapolator(degree)
        value, std_error, metadata = extrapolator.extrapolate_zero(x_data, y_data, sigma_y=sigma_y)
        assert allclose(value, expected, atol=ATOL, rtol=RTOL)
        assert isinstance(std_error, float)  # TODO: test value
        for key in ["coefficients", "covariance_matrix", "residuals", "R2"]:
            assert metadata.get(key, UNSET) is not UNSET  # TODO: test values

    @mark.parametrize("degree", range(1, 5))
    def test_extrapolate_zero_min_points(self, degree):
        """Test extrapolate zero min points."""
        extrapolator = PolynomialExtrapolator(degree=degree)
        x_data = [1] * (degree + 1)
        y_data = range(degree + 1)
        with raises(ValueError):
            extrapolator.extrapolate_zero(x_data, y_data)


################################################################################
## FACADES
################################################################################
class TestFacades:
    @mark.parametrize(
        "cls, configs",
        [
            (LinearExtrapolator, {"degree": 1}),
            (QuadraticExtrapolator, {"degree": 2}),
            (CubicExtrapolator, {"degree": 3}),
            (QuarticExtrapolator, {"degree": 4}),
        ],
    )
    def test_two_qubit_amplifier(self, cls, configs):
        """Test polynomial extrapolator facades."""
        extrapolator = cls()
        assert isinstance(extrapolator, PolynomialExtrapolator)
        for key, value in configs.items():
            assert getattr(extrapolator, key) == value
