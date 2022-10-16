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


from pytest import fixture

from zne.extrapolation import LinearExtrapolator, PolynomialExtrapolator


class TestLinearExtrapolator:

    ################################################################################
    ## FIXTURES
    ################################################################################
    @fixture(scope="function")
    def extrapolator(self):
        return LinearExtrapolator()

    ################################################################################
    ## TESTS
    ################################################################################
    def test_is_polynomial_extrapolator(self, extrapolator):
        assert isinstance(extrapolator, PolynomialExtrapolator)

    def test_degree(self, extrapolator):
        assert extrapolator.degree == 1
