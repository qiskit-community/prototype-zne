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

from inspect import signature
from random import seed as set_random_seed
from random import shuffle
from unittest.mock import Mock

from pytest import fixture, mark

from zne import NOISE_AMPLIFIER_LIBRARY
from zne.immutable_strategy import ImmutableStrategy

STRATEGIES = {**NOISE_AMPLIFIER_LIBRARY}

INIT_OPTIONS = [
    ((), {}),
    ((), {"hello": "world"}),
    ((1, 2), {}),
    ((1.1, 2.2), {"Qiskit": True}),
    (("A", 12), {"pain": None, "gain": None}),
]


class TestImmutableStrategy:

    ################################################################################
    ## FIXTURES
    ################################################################################
    @fixture
    def DummyStrategy(self):
        class DummyStrategy(ImmutableStrategy):
            _save_init_options = Mock()

            def __init__(self, *args, **kwargs):
                pass

        return DummyStrategy

    @fixture
    def get_init_options(self):
        def factory_method(cls):
            init_signature = signature(cls.__init__)
            init_keys = init_signature.parameters.keys()
            init_options = {k: f"Mock({k})" for k in init_keys if k != "self"}
            return init_options

        return factory_method

    @fixture
    def shuffle_init_options(self, get_init_options):
        def factory_method(cls, seed=None):
            set_random_seed(seed)
            ordered_options = get_init_options(cls)
            items = list(ordered_options.items())
            shuffle(items)
            return dict(items)

        return factory_method

    ################################################################################
    ## TESTS
    ################################################################################
    @mark.parametrize(
        "init_args, init_kwargs",
        [
            ((), {}),
            ((), {"hello": "world"}),
            ((1, 2), {}),
            ((1.1, 2.2), {"Qiskit": True}),
            (("A", 12), {"pain": None, "gain": None}),
        ],
    )
    def test_new(self, init_args, init_kwargs, DummyStrategy):
        strategy = DummyStrategy(*init_args, **init_kwargs)
        strategy._save_init_options.assert_called_once_with(*init_args, **init_kwargs)

    @mark.parametrize("init_args, init_kwargs", INIT_OPTIONS)
    def test_save_init_options(self, init_args, init_kwargs, DummyStrategy):
        strategy = DummyStrategy()
        assert strategy._init_options == {}
        strategy._save_init_options(*init_args, **init_kwargs)
        assert strategy._init_options == {}

    @mark.parametrize("Strategy", STRATEGIES.values(), ids=STRATEGIES.keys())
    def test_name(self, Strategy):
        strategy = Strategy()
        assert strategy.name == Strategy.__name__

    @mark.parametrize("Strategy", STRATEGIES.values(), ids=STRATEGIES.keys())
    def test_options(self, Strategy, shuffle_init_options):
        options = shuffle_init_options(Strategy, seed=0)
        strategy = Strategy.__new__(Strategy, **options)
        options.pop("warn_user", None)
        assert strategy.options == dict(sorted(options.items()))

    @mark.parametrize("Strategy", STRATEGIES.values(), ids=STRATEGIES.keys())
    def test_repr(self, Strategy):
        strategy = Strategy()
        options = dict({"example": "option"})
        strategy._init_options = options
        assert repr(strategy) == f"<{Strategy.__name__}:{options}>"

    @mark.parametrize("Strategy", STRATEGIES.values(), ids=STRATEGIES.keys())
    def test_eq(self, Strategy, shuffle_init_options):
        options_1 = shuffle_init_options(Strategy, seed=0)
        options_2 = shuffle_init_options(Strategy, seed=1)
        assert Strategy.__new__(Strategy, **options_1) == Strategy.__new__(Strategy, **options_2)
