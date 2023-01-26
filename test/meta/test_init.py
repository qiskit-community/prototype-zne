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

from pytest import fixture, mark, raises

from zne.meta.init import zne_init
from zne.zne_strategy import ZNEStrategy


class TestZNEInit:
    ################################################################################
    ## FIXTURES
    ################################################################################
    @fixture(scope="function")
    def init(_self):
        return zne_init(Mock())

    @fixture(scope="function")
    def self(_self):
        return Mock()

    ################################################################################
    ## TESTS
    ################################################################################
    def test_deprecation(_self, init):
        with raises(TypeError):
            init("self", circuits="circuits")
        with raises(TypeError):
            init("self", observables="observables")
        with raises(TypeError):
            init("self", parameters="parameters")

    def test_base_init(_self, self):
        base_init = Mock()
        init = zne_init(base_init)
        kwargs = {"Tolkien": "Silmarilion", "Moises": "Genesis"}

        # Without zne_strategy
        _ = init(self, options="options", **kwargs)
        base_init.assert_called_once_with(self, options="options", **kwargs)

        # With zne_strategy
        base_init.reset_mock()
        zne_strategy = ZNEStrategy()
        _ = init(self, options="options", zne_strategy=zne_strategy, **kwargs)
        base_init.assert_called_once_with(self, options="options", **kwargs)
        assert self.zne_strategy is zne_strategy


@mark.parametrize("init", [None, Ellipsis, True, 0, 1.0, 1j, "init"])
def test_type_error(init):
    with raises(TypeError):
        zne_init(init)
