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

from unittest.mock import Mock

from pytest import fixture, mark, raises

from zne.extrapolation import Extrapolator


class TestExtrapoaltor:
    ################################################################################
    ## FIXTURES
    ################################################################################
    @fixture(scope="function")
    def MockExtrapolator(self):
        class MockExtrapolator(Extrapolator):
            def __init__(self, min_points=2) -> None:
                self._min_points = min_points

            @property
            def min_points(self):
                return self._min_points

            def _fit_regression_model(self, data):
                model = lambda _: (1, None)
                return model, {}

        return MockExtrapolator

    @fixture(scope="function")
    def extrapolator(self, MockExtrapolator):
        return MockExtrapolator()

    ################################################################################
    ## TESTS
    ################################################################################
    def test_fit_regression_model(self, extrapolator):
        extrapolator._validate_data = Mock(side_effect=lambda x: x)
        extrapolator._fit_regression_model = Mock(return_value=("model", "metadata"))
        assert extrapolator.fit_regression_model("data") == ("model", "metadata")
        extrapolator._validate_data.assert_called_once_with("data")
        extrapolator._fit_regression_model.assert_called_once_with("data")

    @mark.parametrize("prediction, variance, metadata", [(1, 0, {}), (0, None, {"m": "d"})])
    def test_infer(self, extrapolator, prediction, variance, metadata):
        if variance is not None:
            metadata = {"variance": variance, **metadata}
        model = lambda _: (prediction, variance)
        extrapolator.fit_regression_model = Mock(return_value=(model, metadata))
        pred, meta = extrapolator.infer(0, "data")
        extrapolator.fit_regression_model.assert_called_once_with("data")
        assert pred == prediction
        assert meta == metadata

    def test_extrapolate_zero(self, extrapolator):
        extrapolator.infer = Mock()
        extrapolator.extrapolate_zero("data")
        extrapolator.infer.assert_called_once_with(0, "data")

    @mark.parametrize(
        "data, expected",
        [
            ([[0, 0, 0], [0, 0, 0]], ((0, 0, 0), (0, 0, 0))),
            ([(0, 0, 0), [0, 0, 0]], ((0, 0, 0), (0, 0, 0))),
            ([[0, 0, 0], (0, 0, 0)], ((0, 0, 0), (0, 0, 0))),
            ([(0, 0, 0), (0, 0, 0)], ((0, 0, 0), (0, 0, 0))),
            (([0, 0, 0], [0, 0, 0]), ((0, 0, 0), (0, 0, 0))),
            (((0, 0, 0), [0, 0, 0]), ((0, 0, 0), (0, 0, 0))),
            (([0, 0, 0], (0, 0, 0)), ((0, 0, 0), (0, 0, 0))),
            (((0, 0, 0), (0, 0, 0)), ((0, 0, 0), (0, 0, 0))),
            ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], ((0, 0, 0), (0, 0, 0), (0, 0, 0))),
        ],
    )
    def test_validate_data(self, extrapolator, data, expected):
        assert extrapolator._validate_data(data) == expected

    @mark.parametrize(
        "data",
        [
            0,
            1.0,
            1j,
            True,
            set(),
            [0],
            [1.0],
            [1j],
            [True],
            [set()],
            [[0]],
            [[0, 0]],
            [[0, 0, 1j]],
            [[0, 0, 0], [0, 0]],
            [[0, 0, 0], [0, 0, 1j]],
        ],
    )
    def test_validate_data_type_error(self, extrapolator, data):
        with raises(TypeError):
            extrapolator._validate_data(data)

    @mark.parametrize("min_points", range(2, 9))
    def test_validate_data_value_error(self, MockExtrapolator, min_points):
        extrapolator = MockExtrapolator(min_points)
        with raises(ValueError):
            data = [(0, 0, 0)] * (min_points - 1)
            extrapolator._validate_data(data)
