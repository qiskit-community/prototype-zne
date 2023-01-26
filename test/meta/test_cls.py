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


from unittest.mock import Mock, patch

from pytest import fixture, mark, raises
from qiskit.primitives import BaseEstimator

from zne import ZNEStrategy
from zne.meta import zne
from zne.meta.cls import _get_zne_strategy, _set_zne_strategy

from .. import TYPES


class TestZNE:
    ################################################################################
    ## FIXTURES
    ################################################################################
    @fixture(scope="function")
    def Estimator(self):
        class Estimator(BaseEstimator):
            def _call(self):
                pass

            def _run(self):
                pass

        return Estimator

    @fixture(scope="function")
    def ZNEE(self, Estimator):
        return zne(Estimator)

    ################################################################################
    ## TESTS
    ################################################################################
    def test_zne_cls(self, Estimator):
        mocks = {p: Mock(return_value=p) for p in ("zne_init", "zne_call", "zne_run")}
        with patch.multiple("zne.meta.cls", **mocks):
            ZNEE = zne(Estimator)
        assert ZNEE.__init__ == "zne_init"
        mocks["zne_init"].assert_called_once()
        assert ZNEE.__call__ == "zne_call"
        mocks["zne_call"].assert_called_once()
        assert ZNEE._run == "zne_run"
        mocks["zne_run"].assert_called_once()
        assert hasattr(ZNEE, "zne_strategy")
        assert isinstance(ZNEE.zne_strategy, property)

    @mark.parametrize("obj", TYPES)
    def test_zne_cls_type_error(self, obj):
        with raises(TypeError):
            zne(obj)
        with raises(TypeError):
            zne(type(obj))

    def test_zne_strategy(self, ZNEE, Estimator):
        estimator = ZNEE()

        # None zne_strategy
        estimator.zne_strategy = None
        assert isinstance(estimator.zne_strategy, ZNEStrategy)
        assert estimator.zne_strategy is estimator._zne_strategy

        # Invalid zne_strategy
        with raises(TypeError):
            estimator.zne_strategy = "ERROR"

        # Custom zne_strategy
        zne_strategy = ZNEStrategy()
        estimator.zne_strategy = zne_strategy
        assert estimator.zne_strategy is zne_strategy
        assert estimator.zne_strategy is estimator._zne_strategy

        # Unset zne_strategy
        estimator = Estimator()  # instantiation before class update
        Estimator.zne_strategy = property(_get_zne_strategy, _set_zne_strategy)
        with raises(AttributeError):
            estimator._zne_strategy
        assert isinstance(estimator.zne_strategy, ZNEStrategy)
        assert estimator.zne_strategy is estimator._zne_strategy
