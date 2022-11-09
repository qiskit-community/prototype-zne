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


from math import isclose

from pytest import mark, raises

from zne.extrapolation import (
    CubicExtrapolator,
    LinearExtrapolator,
    PolynomialExtrapolator,
    QuadraticExtrapolator,
    QuarticExtrapolator,
)


################################################################################
## AUXILIARY
################################################################################
def fit_regression_model_test_parameters(max_degree):
    for degree in range(1, max_degree + 1):  # All degrees up to max
        for d in range(1, degree + 1):  # All curves of degree less than or equal
            poly = lambda x: x**d
            for extra in range(5):  # Differet number of data points
                data = [(x, poly(x), 0) for x in range(1, degree + 2 + extra)]
                for target in [0, degree + 2 + extra]:  # Extrapolation to the left and right
                    yield (degree, tuple(data), target, poly(target))


################################################################################
## EXTRPOLATORS
################################################################################
class TestPolynomialExtrapolator:

    ################################################################################
    ## TESTS
    ################################################################################
    @mark.parametrize(
        "degree", cases := range(1, 5 + 1), ids=[f"degree = {degree}" for degree in cases]
    )
    def test_degree(self, degree):
        extrapolator = PolynomialExtrapolator(degree=degree)
        assert extrapolator.degree == degree

    @mark.parametrize(
        "degree", cases := range(0, -5, -1), ids=[f"degree = {degree}" for degree in cases]
    )
    def test_degree_value_error(self, degree):
        with raises(ValueError):
            PolynomialExtrapolator(degree)

    @mark.parametrize(
        "degree", cases := range(1, 5 + 1), ids=[f"degree = {degree}" for degree in cases]
    )
    def test_min_points(self, degree):
        extrapolator = PolynomialExtrapolator(degree=degree)
        assert extrapolator.min_points == degree + 1

    @mark.parametrize(
        "degree, data, target, expected",
        [*fit_regression_model_test_parameters(5)],
    )
    def test_fit_regression_model(self, degree, data, target, expected):
        extrapolator = PolynomialExtrapolator(degree=degree)
        model, metadata = extrapolator._fit_regression_model(data)
        prediction, variance = model(target)
        assert isclose(prediction, expected, abs_tol=1e-4, rel_tol=1e-4)
        assert variance is None
        assert metadata == {}


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
        extrapolator = cls()
        assert isinstance(extrapolator, PolynomialExtrapolator)
        for key, value in configs.items():
            assert getattr(extrapolator, key) == value
