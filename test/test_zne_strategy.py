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

from collections.abc import Sequence
from itertools import count, product
from test import TYPES
from unittest.mock import Mock, patch

from numpy import array
from pytest import fixture, mark, raises, warns
from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.primitives import EstimatorResult
from qiskit.providers import Backend
from qiskit.transpiler import PassManager, StagedPassManager

from zne.extrapolation import EXTRAPOLATOR_LIBRARY, Extrapolator, LinearExtrapolator
from zne.noise_amplification import NOISE_AMPLIFIER_LIBRARY, CxAmplifier, NoiseAmplifier
from zne.utils.typing import isreal
from zne.zne_strategy import NOISE_AMPLIFICATION_STAGE, ZNEStrategy


class TestZNEStrategy:
    ################################################################################
    ## FIXTURE
    ################################################################################
    @fixture(scope="function")
    def amplifier_mock(self):
        amplifier = Mock(NoiseAmplifier)
        amplifier.amplify_circuit_noise.side_effect = count()
        return amplifier

    @fixture(scope="function")
    def extrapolator_mock(self):
        def infer(target, data):
            _, y, _ = zip(*data)
            return 1, 0, {}

        extrapolator = Mock(Extrapolator)
        extrapolator.infer.side_effect = infer
        return extrapolator

    ################################################################################
    ## NEW
    ################################################################################
    def test_noop(self):
        zne_strategy = ZNEStrategy.noop()
        assert zne_strategy.is_noop

    ################################################################################
    ## INIT
    ################################################################################
    def test_defaults(self):
        DEFAULT_NOISE_AMPLIFIER = CxAmplifier()
        DEFAULT_NOISE_FACTORS = (1,)
        DEFAULT_EXTRAPOLATOR = LinearExtrapolator()
        DEFAULT_TRANSPILER_LEVEL = 1
        DEFAULT_TRANSPILER = None
        zne_strategy = ZNEStrategy()
        assert zne_strategy.noise_amplifier == DEFAULT_NOISE_AMPLIFIER
        assert zne_strategy.noise_factors == DEFAULT_NOISE_FACTORS
        assert zne_strategy.extrapolator == DEFAULT_EXTRAPOLATOR
        assert zne_strategy.transpilation_level == DEFAULT_TRANSPILER_LEVEL
        assert zne_strategy.transpiler == DEFAULT_TRANSPILER

    @mark.parametrize(
        "NoiseAmplifier, noise_factors, Extrapolator, transpilation_level, transpiler",
        cases := list(
            product(
                NOISE_AMPLIFIER_LIBRARY.values(),
                [(1,), (1, 3), (1, 3, 5)],
                EXTRAPOLATOR_LIBRARY.values(),
                [None, 0, 1, 2, 3],
                [None, StagedPassManager()],
            )
        ),
        ids=[f"{na.name}-{nf}-{e.name}" for na, nf, e, _, _ in cases],
    )
    def test_zne_strategy(
        self, NoiseAmplifier, noise_factors, Extrapolator, transpilation_level, transpiler
    ):
        noise_amplifier = NoiseAmplifier()
        extrapolator = Extrapolator()
        zne_strategy = ZNEStrategy(
            noise_amplifier=noise_amplifier,
            noise_factors=noise_factors,
            extrapolator=extrapolator,
            transpilation_level=transpilation_level,
            transpiler=transpiler,
        )
        assert zne_strategy.noise_amplifier is noise_amplifier
        assert zne_strategy.noise_factors == noise_factors
        assert zne_strategy.extrapolator is extrapolator
        assert zne_strategy.transpilation_level == transpilation_level
        assert zne_strategy.transpiler is transpiler

    @mark.parametrize("obj", TYPES, ids=[str(type(t).__name__) for t in TYPES])
    def test_type_error(self, obj):
        with raises(TypeError):
            _ = ZNEStrategy(noise_amplifier=obj)
        with raises(TypeError):
            _ = ZNEStrategy(extrapolator=obj)
        if not isinstance(obj, Sequence):
            with raises(TypeError):
                _ = ZNEStrategy(noise_factors=obj)
        if not isinstance(obj, (int, type(None))):
            with raises(TypeError):
                _ = ZNEStrategy(transpilation_level=obj)
        if obj is not None:
            with raises(TypeError):
                _ = ZNEStrategy(transpiler=obj)

    @mark.parametrize(
        "noise_factors, expected",
        cases := list(
            zip(
                [(1,), (3,), (1, 3), (1, 3, 5), [1, 3, 5], [1.2, 3, 5.4]],
                [(1,), (3,), (1, 3), (1, 3, 5), (1, 3, 5), (1.2, 3, 5.4)],
            )
        ),
        ids=[f"{nf}" for nf, _ in cases],
    )
    def test_noise_factors(self, noise_factors, expected):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        assert zne_strategy.noise_factors == expected
        assert zne_strategy.num_noise_factors == len(expected)

    @mark.parametrize(
        "noise_factors, expected",
        cases := list(
            zip(
                [(1, 5, 3), (3.3, 1.2, 5.4)],
                [(1, 3, 5), (1.2, 3.3, 5.4)],
            )
        ),
        ids=[f"{nf}" for nf, _ in cases],
    )
    def test_noise_factors_sort(self, noise_factors, expected):
        with warns(UserWarning):
            zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        assert zne_strategy.noise_factors == expected
        assert zne_strategy.num_noise_factors == len(expected)

    @mark.parametrize(
        "noise_factors, expected",
        cases := list(
            zip(
                [(1, 1), (1, 3, 1, 5), (5, 5, 3), (2.4, 2.4)],
                [(1,), (1, 3, 5), (3, 5), (2.4,)],
            )
        ),
        ids=[f"{nf}" for nf, _ in cases],
    )
    def test_noise_factors_duplicates(self, noise_factors, expected):
        with warns(UserWarning):
            zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        assert zne_strategy.noise_factors == expected
        assert zne_strategy.num_noise_factors == len(expected)

    @mark.parametrize(
        "noise_factors",
        cases := [(), []],
        ids=[f"{type(c)}" for c in cases],
    )
    def test_noise_factors_empty_error(self, noise_factors):
        with raises(ValueError):
            _ = ZNEStrategy(noise_factors=noise_factors)

    @mark.parametrize(
        "noise_factors",
        cases := ["1", True, False, float("NaN"), [1, 3, "5"]],
        ids=[f"{type(c)}" for c in cases],
    )
    def test_noise_factors_real_type_error(self, noise_factors):
        if not isinstance(noise_factors, Sequence):
            noise_factors = [noise_factors]
        with raises(TypeError):
            _ = ZNEStrategy(noise_factors=noise_factors)

    @mark.parametrize(
        "noise_factors",
        cases := [0, 0.9999, -1, -0.5],
        ids=[f"{c}" for c in cases],
    )
    def test_noise_factors_value_error(self, noise_factors):
        if not isinstance(noise_factors, Sequence):
            noise_factors = [noise_factors]
        with raises(ValueError):
            _ = ZNEStrategy(noise_factors=noise_factors)

    def test_validate_transpiler(self):
        # None
        zne_strategy = ZNEStrategy(transpiler=None)
        assert zne_strategy.transpiler is None

        # StagedPassManager
        transpiler = StagedPassManager()
        zne_strategy = ZNEStrategy(transpiler=transpiler)
        assert zne_strategy.transpiler is transpiler

        # PassManager
        transpiler = PassManager()
        zne_strategy = ZNEStrategy(transpiler=transpiler)
        assert zne_strategy.transpiler.stages == ("transpilation",)
        assert zne_strategy.transpiler.transpilation is transpiler

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @mark.parametrize("noise_factors", [(1, 3), (1.2,), (2.1, 4.5)])
    def test_performs_noise_amplification_true(self, noise_factors):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        assert zne_strategy.performs_noise_amplification

    @mark.parametrize("noise_factors", [(1,), [1]])
    def test_performs_noise_amplification_false(self, noise_factors):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        assert not zne_strategy.performs_noise_amplification

    @mark.parametrize("noise_factors", [(1, 3), (1.2, 2.4)])
    def test_performs_zne_true(self, noise_factors):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        assert zne_strategy.performs_zne

    @mark.parametrize("noise_factors", [(1,), (2.1,)])
    def test_performs_zne_false(self, noise_factors):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        assert not zne_strategy.performs_zne

    @mark.parametrize("noise_factors", [(1,), (2.1,), (1, 3), (2.1, 4.5)])
    def test_is_noop(self, noise_factors):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        if tuple(noise_factors) == (1,):
            assert zne_strategy.is_noop
        else:
            assert not zne_strategy.is_noop

    ################################################################################
    ## TRANSPILATION
    ################################################################################
    @staticmethod
    def test_noise_amplification_stage_name():
        assert NOISE_AMPLIFICATION_STAGE == "noise_amplification"

    @mark.parametrize(
        "noise_factors",
        cases := [(1,), (3,), (1, 3), (1, 3, 5)],
        ids=[f"{nf}" for nf in cases],
    )
    def test_build_transpilers(self, noise_factors):
        backend = Backend()
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)

        target_generate = (
            "build_noisy_transpiler"
            if zne_strategy.performs_noise_amplification
            else "build_noiseless_transpiler"
        )

        def side_effect(*args):
            if zne_strategy.performs_noise_amplification:
                _, nf = args
                return f"TRANSPILER<{nf}>"
            return "TRANSPILER<1>"

        mock_generate = Mock(side_effect=side_effect)
        setattr(zne_strategy, target_generate, mock_generate)
        transpilers = zne_strategy.build_transpilers(backend)
        for nf in zne_strategy.noise_factors:
            if zne_strategy.performs_noise_amplification:
                mock_generate.assert_any_call(backend, nf)
            else:
                mock_generate.assert_any_call(backend)
            assert side_effect(backend, nf) in transpilers
        assert len(transpilers) == zne_strategy.num_noise_factors
        assert mock_generate.call_count == zne_strategy.num_noise_factors

    @mark.parametrize(
        "noise_factor",
        cases := [1, 3, 5, 2.4, 1.2],
        ids=[f"{c}" for c in cases],
    )
    def test_build_noisy_transpiler(self, noise_factor):
        backend = Backend()
        zne_strategy = ZNEStrategy()

        noise_amplifier = Mock()
        noise_amplifier.build_pass_manager = Mock(
            return_value=(noise_amplification := f"NOISE-AMPLIFICATION<{noise_factor}>")
        )
        zne_strategy.noise_amplifier = noise_amplifier

        mock_generate = Mock(return_value=(transpiler := Mock()))
        zne_strategy.build_noiseless_transpiler = mock_generate

        zne_strategy.build_noisy_transpiler(backend, noise_factor)

        mock_generate.assert_called_once_with(backend)
        noise_amplifier.build_pass_manager.assert_called_once_with(noise_factor)
        assert getattr(transpiler, NOISE_AMPLIFICATION_STAGE) == noise_amplification

    @mark.parametrize("obj", TYPES, ids=[str(type(t).__name__) for t in TYPES])
    def test_build_noisy_transpiler_type_error(self, obj):
        zne_strategy = ZNEStrategy()
        if not isreal(obj):
            with raises(TypeError):
                _ = zne_strategy.build_noisy_transpiler(Backend(), obj)

    def test_build_noiseless_transpiler(self):
        return_value = "<NOISLESS-TRANSPILER>"

        # Transpiler with noise_amplification stage
        transpiler = StagedPassManager([NOISE_AMPLIFICATION_STAGE])
        zne_strategy = ZNEStrategy(transpiler=transpiler)
        mock_clear = Mock(return_value=return_value)
        zne_strategy._clear_noise_amplification_stage = mock_clear
        result = zne_strategy.build_noiseless_transpiler(Backend())
        mock_clear.assert_called_once_with(transpiler, warn_user=True)
        assert result == return_value

        # No transpiler
        transpiler = StagedPassManager()
        zne_strategy = ZNEStrategy(transpiler=transpiler)
        mock_insert = Mock(return_value=return_value)
        zne_strategy._insert_void_noise_amplification_stage = mock_insert
        result = zne_strategy.build_noiseless_transpiler(Backend())
        mock_insert.assert_called_once_with(transpiler)
        assert result == return_value

    @mark.parametrize(
        "transpilation_level", cases := [None, 0, 1, 2, 3], ids=[f"{c}" for c in cases]
    )
    def test_build_default_transpiler(self, transpilation_level):
        backend = Backend()
        zne_strategy = ZNEStrategy(transpilation_level=transpilation_level)

        return_value = f"TRANSPILER-{transpilation_level}"
        with patch(
            "zne.zne_strategy.generate_preset_pass_manager", return_value=return_value
        ) as mock_generate:
            transpiler = zne_strategy.build_default_transpiler(backend)
        if transpilation_level is None:
            assert isinstance(transpiler, StagedPassManager)
            assert len(transpiler.passes()) == 0
        else:
            mock_generate.assert_called_once_with(transpilation_level, backend=backend)
            assert transpiler == return_value

    @mark.parametrize("obj", TYPES, ids=[str(type(t).__name__) for t in TYPES])
    def test_build_default_transpiler_type_error(self, obj):
        zne_strategy = ZNEStrategy()
        with raises(TypeError):
            zne_strategy.build_default_transpiler(obj)

    def test_clear_noise_amplification_stage(self):
        stages = {NOISE_AMPLIFICATION_STAGE: PassManager()}

        # None
        spm = StagedPassManager([NOISE_AMPLIFICATION_STAGE])
        clear_spm = ZNEStrategy._clear_noise_amplification_stage(spm)
        for stage in spm.stages:
            if stage != NOISE_AMPLIFICATION_STAGE:
                assert getattr(clear_spm, stage) is getattr(spm, stage)
        assert clear_spm is not spm
        assert getattr(clear_spm, NOISE_AMPLIFICATION_STAGE) is None

        # Not None
        spm = StagedPassManager(stages, **stages)
        clear_spm = ZNEStrategy._clear_noise_amplification_stage(spm)
        for stage in spm.stages:
            if stage != NOISE_AMPLIFICATION_STAGE:
                assert getattr(clear_spm, stage) is getattr(spm, stage)
        assert clear_spm is not spm
        assert getattr(clear_spm, NOISE_AMPLIFICATION_STAGE) is None
        assert getattr(spm, NOISE_AMPLIFICATION_STAGE) is not None

    def test_clear_noise_amplification_stage_user_warning(self):
        stages = {NOISE_AMPLIFICATION_STAGE: PassManager()}
        spm = StagedPassManager(stages, **stages)
        with warns(UserWarning):
            _ = ZNEStrategy._clear_noise_amplification_stage(spm, warn_user=True)

    def test_clear_noise_amplification_stage_value_error(self):
        spm = StagedPassManager()
        with raises(ValueError):
            _ = ZNEStrategy._clear_noise_amplification_stage(spm)

    def test_insert_void_noise_amplification_stage(self):
        stages = {
            "alpha": PassManager(),
            "beta": PassManager(),
            "gamma": PassManager(),
            "scheduling": PassManager(),
            "omega": PassManager(),
        }
        spm = StagedPassManager(stages, **stages)
        noise_spm = ZNEStrategy()._insert_void_noise_amplification_stage(spm)
        assert NOISE_AMPLIFICATION_STAGE in noise_spm.stages
        for stage in set(noise_spm.stages):
            assert getattr(noise_spm, stage) is getattr(spm, stage, None)

    def test_insert_void_noise_amplification_stage_value_error(self):
        spm = StagedPassManager([NOISE_AMPLIFICATION_STAGE])
        with raises(ValueError):
            _ = ZNEStrategy()._insert_void_noise_amplification_stage(spm)

    @mark.parametrize(
        "stages, expected",
        cases := tuple(
            zip(
                [
                    (),
                    ("alpha",),
                    ("alpha", "omega"),
                    ("alpha", "scheduling"),
                    ("scheduling",),
                    ("scheduling", "omega"),
                    ("scheduling", "scheduling"),
                ],
                [
                    (NOISE_AMPLIFICATION_STAGE,),
                    ("alpha", NOISE_AMPLIFICATION_STAGE),
                    ("alpha", "omega", NOISE_AMPLIFICATION_STAGE),
                    ("alpha", NOISE_AMPLIFICATION_STAGE, "scheduling"),
                    (NOISE_AMPLIFICATION_STAGE, "scheduling"),
                    (NOISE_AMPLIFICATION_STAGE, "scheduling", "omega"),
                    (NOISE_AMPLIFICATION_STAGE, "scheduling", "scheduling"),
                ],
            )
        ),
        ids=[i for i, _ in enumerate(cases)],
    )
    def test_build_noisy_stages(self, stages, expected):
        assert expected == ZNEStrategy._build_noisy_stages(stages)

    ################################################################################
    ## NOISE AMPLIFICATION
    ################################################################################
    def test_amplify_circuit_noise(self, amplifier_mock):
        noise_factors = (1, 2, 3)
        zne_strategy = ZNEStrategy(noise_factors=noise_factors, noise_amplifier=amplifier_mock)
        circuit = QuantumCircuit(2)
        assert zne_strategy.amplify_circuit_noise(circuit, 1) == 0
        amplifier_mock.amplify_circuit_noise.assert_called_once_with(circuit, 1)
        assert zne_strategy.amplify_circuit_noise(circuit, 1) == 0  # Check cache
        amplifier_mock.amplify_circuit_noise.reset_mock()
        assert zne_strategy.amplify_circuit_noise(circuit, 1.2) == 1
        amplifier_mock.amplify_circuit_noise.assert_called_once_with(circuit, 1.2)
        assert zne_strategy.amplify_circuit_noise(circuit, 1.2) == 1  # Check cache
        circuit.h(0)
        amplifier_mock.amplify_circuit_noise.reset_mock()
        assert zne_strategy.amplify_circuit_noise(circuit, 2.4) == 2
        amplifier_mock.amplify_circuit_noise.assert_called_once_with(circuit, 2.4)
        assert zne_strategy.amplify_circuit_noise(circuit, 2.4) == 2  # Check cache
        # Overflow cache
        CACHE_MAXSIZE = 256
        for nf in range(CACHE_MAXSIZE):
            expected = nf + 3
            assert zne_strategy.amplify_circuit_noise(circuit, nf) == expected
            if expected < CACHE_MAXSIZE:  # Check CACHE_MAXSIZE is correct
                assert zne_strategy.amplify_circuit_noise(circuit, nf) == expected
        assert zne_strategy.amplify_circuit_noise(circuit, nf) == CACHE_MAXSIZE + 3
        assert zne_strategy.amplify_circuit_noise(circuit, nf) == CACHE_MAXSIZE + 3 + 1

    @mark.parametrize(
        "circuits, noise_factors",
        cases := tuple(
            product(
                [
                    random_circuit(1, 1, seed=0),
                    [],
                    [random_circuit(2, 2, seed=5)],
                    [random_circuit(2, 2, seed=66), random_circuit(2, 2, seed=1081)],
                ],
                [[1], [1, 3], [1, 3, 5]],
            )
        ),
        ids=[f"{type(c).__name__}<{len(c)}>-{nf}" for c, nf in cases],
    )
    def test_build_noisy_circuits(self, amplifier_mock, circuits, noise_factors):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors, noise_amplifier=amplifier_mock)
        _ = zne_strategy.build_noisy_circuits(circuits)
        if isinstance(circuits, QuantumCircuit):
            circuits = [circuits]
        assert amplifier_mock.amplify_circuit_noise.call_count == len(circuits) * len(noise_factors)
        for circuit in circuits:
            for noise_factor in noise_factors:
                amplifier_mock.amplify_circuit_noise.assert_any_call(circuit, noise_factor)

    @mark.parametrize(
        "num_noise_factors, arg, expected",
        cases := [
            (1, None, None),
            (1, 0, (0,)),
            (1, [0], (0,)),
            (1, [1], (1,)),
            (1, [2], (2,)),
            (1, [0, 1], (0, 1)),
            (1, [0, 2], (0, 2)),
            (1, [1, 2], (1, 2)),
            (1, [0, 1, 2], (0, 1, 2)),
            (2, None, None),
            (2, 0, (0, 0)),
            (2, [0], (0, 0)),
            (2, [1], (1, 1)),
            (2, [2], (2, 2)),
            (2, [0, 1], (0, 0, 1, 1)),
            (2, [0, 2], (0, 0, 2, 2)),
            (2, [1, 2], (1, 1, 2, 2)),
            (2, [0, 1, 2], (0, 0, 1, 1, 2, 2)),
            (3, None, None),
            (3, 0, (0, 0, 0)),
            (3, [0], (0, 0, 0)),
            (3, [1], (1, 1, 1)),
            (3, [2], (2, 2, 2)),
            (3, [0, 1], (0, 0, 0, 1, 1, 1)),
            (3, [0, 2], (0, 0, 0, 2, 2, 2)),
            (3, [1, 2], (1, 1, 1, 2, 2, 2)),
            (3, [0, 1, 2], (0, 0, 0, 1, 1, 1, 2, 2, 2)),
        ],
        ids=[f"noise<{nnf}>-{id}" for nnf, id, _ in cases],
    )
    def test_map_to_noisy_circuits(self, num_noise_factors, arg, expected):
        zne_strategy = ZNEStrategy(noise_factors=[n for n in range(1, num_noise_factors + 1)])
        assert zne_strategy.map_to_noisy_circuits(arg) == expected

    ################################################################################
    ## EXTRAPOLATION
    ################################################################################
    @mark.parametrize(
        "noise_factors, values, variances, num_results, extrapolate_return",
        [
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 1, [0, {}]),
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 1, [0, {"R2": 0.1}]),
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 2, [0, {}]),
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 3, [0, {"R2": 0.1, "P": 6.5}]),
        ],
    )
    def test_mitigate_noisy_result(
        self, noise_factors, values, variances, num_results, extrapolate_return
    ):
        pred, meta = extrapolate_return
        extrapolator = Mock()
        extrapolator.extrapolate_zero = Mock(return_value=tuple(extrapolate_return))
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        zne_strategy.extrapolator = extrapolator
        metadata = [{"variance": var, "shots": 1024} for var in variances]
        noisy_result = EstimatorResult(
            values=array(values * num_results), metadata=tuple(metadata * num_results)
        )
        result = zne_strategy.mitigate_noisy_result(noisy_result)
        assert result.values.tolist() == [pred] * num_results
        metadatum = {
            "noise_amplification": {
                "noise_amplifier": zne_strategy.noise_amplifier,
                "noise_factors": tuple(noise_factors),
                "values": tuple(values),
                "variance": tuple(variances),
                "shots": tuple([md["shots"] for md in metadata]),
            },
            "extrapolation": {
                "extrapolator": zne_strategy.extrapolator,
                **meta,
            },
        }
        assert result.metadata == tuple([{"zne": metadatum} for _ in range(num_results)])

    @mark.parametrize(
        "num_noise_factors, values, variances",
        cases := [
            (1, [0], [0]),
            (1, [0, 1], [0, 1]),
            (2, [0, 0], [0, 0]),
            (2, [0, 0, 1, 1], [0, 0, 1, 1]),
            (3, [0, 0, 0], [0, 0, 0]),
            (3, [0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 1, 1]),
        ],
        ids=[f"nf<{nnf}>-val<{len(val)}>" for nnf, val, _ in cases],
    )
    def test_generate_noisy_result_groups(self, num_noise_factors, values, variances):
        zne_strategy = ZNEStrategy(noise_factors=range(1, num_noise_factors + 1))
        metadata = [{"variance": var} for var in variances]
        result = EstimatorResult(values=array(values), metadata=metadata)
        assert (
            len(tuple(zne_strategy._generate_noisy_result_groups(result)))
            == len(values) / num_noise_factors
        )
        for i, group in enumerate(zne_strategy._generate_noisy_result_groups(result)):
            lower = num_noise_factors * i
            upper = num_noise_factors * (i + 1)
            assert group.values.tolist() == values[lower:upper]
            assert group.metadata == metadata[lower:upper]

    @mark.parametrize(
        "num_noise_factors, num_experiments",
        cases := [(2, 1), (2, 3), (3, 2), (3, 4)],
        ids=[f"nf{nnf}-val{ne}" for nnf, ne in cases],
    )
    def test_generate_noisy_result_groups_value_error(self, num_noise_factors, num_experiments):
        zne_strategy = ZNEStrategy(noise_factors=range(1, num_noise_factors + 1))
        values = array([0] * num_experiments)
        metadata = [{"variance": 0.0}] * num_experiments
        result = EstimatorResult(values=values, metadata=metadata)
        with raises(ValueError):
            generator = zne_strategy._generate_noisy_result_groups(result)
            assert next(generator)

    @mark.parametrize(
        "noise_factors, values, variances, expected",
        [
            ([1, 2], [0, 1], [0, 0], ((1, 0, 0), (2, 1, 0))),
            ([1, 2.0], [0.4, 1.2], [0, None], ((1, 0.4, 0), (2.0, 1.2, 0))),
        ],
    )
    def test_regression_data_from_result_group(self, noise_factors, values, variances, expected):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        metadatum = {"shots": 1024}
        metadata = [
            {"variance": var, **metadatum} if var is not None else metadatum for var in variances
        ]
        result_group = EstimatorResult(values=array(values), metadata=tuple(metadata))
        assert zne_strategy._regression_data_from_result_group(result_group) == expected

    @mark.parametrize(
        "num_noise_factors, num_experiments",
        cases := [(1, 2), (2, 1), (3, 1), (2, 3)],
        ids=[f"nf<{nnf}>-experiments<{ne}>" for nnf, ne in cases],
    )
    def test_regression_data_from_result_group_value_error(
        self, num_noise_factors, num_experiments
    ):
        zne_strategy = ZNEStrategy(noise_factors=range(1, num_noise_factors + 1))
        values = [1] * num_experiments
        metadata = [{"variance": 0}] * num_experiments
        result_group = EstimatorResult(values=array(values), metadata=tuple(metadata))
        with raises(ValueError):
            zne_strategy._regression_data_from_result_group(result_group)

    @mark.parametrize(
        "noise_factors, values, metadata, extrapolation, expected_na",
        [
            (
                [1, 2],
                [1, 1],
                [{"variance": 0}, {"variance": 0}],
                {},
                {"noise_factors": (1, 2), "values": (1, 1), "variance": (0, 0)},
            ),
            (
                [1, 2],
                [1, 0],
                [{"variance": 0.1}, {"variance": 0.4}],
                {"R2": 0.98},
                {"noise_factors": (1, 2), "values": (1, 0), "variance": (0.1, 0.4)},
            ),
            (
                [1, 2, 3],
                [0, 1.5, 2.4],
                [
                    {"variance": 0.11, "shots": 2048},
                    {"variance": 0.1, "shots": 1024},
                    {"variance": 0.12, "shots": 4096},
                ],
                {"R2": 0.44, "P": 6.5},
                {
                    "noise_factors": (1, 2, 3),
                    "values": (0, 1.5, 2.4),
                    "variance": (0.11, 0.1, 0.12),
                    "shots": (2048, 1024, 4096),
                },
            ),
            (
                [1, 2, 3],
                [0, 1.5, 2.4],
                [
                    {"variance": 0.11, "shots": 2048},
                    {"variance": 0.1, "shots": 1024, "backend": "ibmq-nugget"},
                    {"variance": 0.12, "shots": 4096, "seconds": 3600},
                ],
                {"R2": 0.44, "P": 6.5},
                {
                    "noise_factors": (1, 2, 3),
                    "values": (0, 1.5, 2.4),
                    "variance": (0.11, 0.1, 0.12),
                    "shots": (2048, 1024, 4096),
                    "backend": (None, "ibmq-nugget", None),
                    "seconds": (None, None, 3600),
                },
            ),
        ],
    )
    def test_build_zne_metadata(self, noise_factors, values, metadata, extrapolation, expected_na):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        result_group = EstimatorResult(values=array(values), metadata=tuple(metadata))
        computed = zne_strategy.build_zne_metadata(result_group, extrapolation)
        expected_na = {
            "noise_amplifier": zne_strategy.noise_amplifier,
            **expected_na,
        }
        expected_ex = {
            "extrapolator": zne_strategy.extrapolator,
            **extrapolation,
        }
        assert computed.get("noise_amplification") == expected_na
        assert computed.get("extrapolation") == expected_ex

    @mark.parametrize(
        "num_noise_factors, num_experiments",
        cases := [(1, 2), (2, 1), (3, 1), (2, 3)],
        ids=[f"nf<{nnf}>-experiments<{ne}>" for nnf, ne in cases],
    )
    def test_build_zne_metadata_value_error(self, num_noise_factors, num_experiments):
        zne_strategy = ZNEStrategy(noise_factors=range(1, num_noise_factors + 1))
        values = array([1] * num_experiments)
        metadata = [{"variance": 0}] * num_experiments
        result_group = EstimatorResult(values=values, metadata=metadata)
        with raises(ValueError):
            zne_strategy.build_zne_metadata(result_group)
