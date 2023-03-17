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

from unittest.mock import Mock

from numpy import array, equal
from pytest import fixture, mark, raises

from zne.extrapolation import Extrapolator
from zne.extrapolation.extrapolator import ReckoningResult


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

            def _extrapolate_zero(self, x_data, y_data, sigma_x, sigma_y):
                return ReckoningResult(1, 1, {})

        return MockExtrapolator

    @fixture(scope="function")
    def extrapolator(self, MockExtrapolator):
        return MockExtrapolator()

    ################################################################################
    ## TESTS
    ################################################################################
    @mark.parametrize(
        "x_data, y_data, sigma_x, sigma_y",
        [
            ([1, 2], [1, 2], None, None),
            ([1, 2], [1, 2], None, [4, 4]),
            ([1, 2], [1, 2], [4, 4], None),
            ([1, 2], [1, 2], [4, 4], [4, 4]),
            ([1, 2, 3], [1, 2, 3], None, None),
            ([1, 2, 3], [1, 2, 3], None, [4, 4, 4]),
            ([1, 2, 3], [1, 2, 3], [4, 4, 4], None),
            ([1, 2, 3], [1, 2, 3], [4, 4, 4], [4, 4, 4]),
        ],
    )
    def test_extrapolate_zero(self, extrapolator, x_data, y_data, sigma_x, sigma_y):
        """Test extrapolate zero."""
        extrapolator._extrapolate_zero = Mock()
        extrapolator.extrapolate_zero(x_data, y_data, sigma_x, sigma_y)
        extrapolator._extrapolate_zero.assert_called_once()
        call_args = extrapolator._extrapolate_zero.call_args[0]
        expected_call_args = (
            tuple(x_data),
            tuple(y_data),
            tuple(sigma_x or [1] * len(x_data)),
            tuple(sigma_y or [1] * len(y_data)),
        )
        for arg, exp in zip(call_args, expected_call_args):
            assert arg == exp

    @mark.parametrize(
        "x_data, y_data, sigma_x, sigma_y",
        [
            ([1, 2], [0, 1, 2], None, None),
            ([0, 1, 2], [1, 2], None, None),
            ([1, 2], [1, 2], [1, 1, 1], None),
            ([1, 2], [1, 2], None, [1, 1, 1]),
        ],
    )
    def test_extrapolate_zero_input_sizes(self, extrapolator, x_data, y_data, sigma_x, sigma_y):
        """Test extrapolate zero input sizes."""
        with raises(ValueError):
            extrapolator.extrapolate_zero(x_data, y_data, sigma_x, sigma_y)

    @mark.parametrize("data", [[0] * 2, [0] * 3, [0] * 4, [1] * 2, [1] * 3, [1] * 4, range(4)])
    def test_validate_data(self, extrapolator, data):
        """Test validate data."""
        result = extrapolator._validate_data(data)
        assert result == tuple(data)

    @mark.parametrize("data", [None, True, 1, 1.0, float("nan"), 1j, [1j], [None], set(), [[0]]])
    def test_validate_data_type_error(self, extrapolator, data):
        """Test validate data type error."""
        with raises(TypeError):
            extrapolator._validate_data(data)

    @mark.parametrize("data", [(1,), (1, 2)])
    def test_validate_data_min_points(self, MockExtrapolator, data):
        """Test validate data min points."""
        extrapolator = MockExtrapolator(len(data) + 1)
        print(extrapolator.min_points)
        with raises(ValueError):
            extrapolator._validate_data(data)

    @mark.parametrize(
        "sigma", [[0] * 2, [0] * 3, [0] * 4, [1] * 2, [1] * 3, [1] * 4, range(4), None]
    )
    def test_validate_sigma(self, extrapolator, sigma):
        """Test validate sigma."""
        default_size = 4
        result = extrapolator._validate_sigma(sigma, default_size)
        if sigma is None:
            sigma = [1] * default_size
        valid = array(sigma)
        assert equal(result, valid).all()
