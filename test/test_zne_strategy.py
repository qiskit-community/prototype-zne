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

from collections.abc import Sequence
from itertools import count, product
from unittest.mock import Mock

from numpy import array
from pytest import fixture, mark, raises, warns
from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.primitives import EstimatorResult

from zne.extrapolation import Extrapolator, LinearExtrapolator
from zne.noise_amplification import NoiseAmplifier
from zne.noise_amplification.folding_amplifier import MultiQubitAmplifier
from zne.zne_strategy import ZNEStrategy

from . import NO_ITERS_NONE, NO_NONE


################################################################################
## FIXTURES
################################################################################
@fixture(scope="function")
def amplifier_mock():
    """NoiseAmplifier mock object."""
    amplifier = Mock(NoiseAmplifier)
    amplifier.amplify_circuit_noise.side_effect = count()
    return amplifier


@fixture(scope="function")
def extrapolator_mock():
    """Extrapolator mock object."""

    def infer(target, data):
        _, y, _ = zip(*data)
        return 1, 0, {}

    extrapolator = Mock(Extrapolator)
    extrapolator.infer.side_effect = infer
    return extrapolator


################################################################################
## TESTS
################################################################################
def test_definition():
    assert ZNEStrategy._DEFINING_ATTRS == (
        "noise_factors",
        "noise_amplifier",
        "extrapolator",
    )


class TestInit:
    """Test ZNEStrategy initialization logic."""

    def test_defaults(self):
        """Test default configuration."""
        assert ZNEStrategy().noise_amplifier == MultiQubitAmplifier()
        assert ZNEStrategy().noise_factors == (1,)
        assert ZNEStrategy().extrapolator == LinearExtrapolator()

    @mark.parametrize(
        "noise_factors",
        [(1,), (1, 3), (1, 3, 5)],
    )
    def test_custom(
        self,
        noise_factors,
    ):
        """Test custom configuration.

        Proper inputs can be assumed since validation is tested separately.
        """
        noise_amplifier = Mock(NoiseAmplifier)
        extrapolator = Mock(Extrapolator)
        zne_strategy = ZNEStrategy(
            noise_factors=noise_factors,
            noise_amplifier=noise_amplifier,
            extrapolator=extrapolator,
        )
        assert zne_strategy.noise_factors == noise_factors
        assert zne_strategy.noise_amplifier is noise_amplifier
        assert zne_strategy.extrapolator is extrapolator


@mark.parametrize(
    "noise_factors",
    [(1,), (1, 3), (1, 3, 5)],
)
class TestMagic:
    """Test generic ZNEStrategy magic methods."""

    def test_repr(self, noise_factors):
        """Test ZNEStrategy.__repr__() magic method."""
        noise_amplifier = Mock(NoiseAmplifier)
        extrapolator = Mock(Extrapolator)
        zne_strategy = ZNEStrategy(
            noise_factors=noise_factors,
            noise_amplifier=noise_amplifier,
            extrapolator=extrapolator,
        )
        expected = "ZNEStrategy("
        expected += f"noise_factors={repr(noise_factors)}, "
        expected += f"noise_amplifier={repr(noise_amplifier)}, "
        expected += f"extrapolator={repr(extrapolator)})"
        assert repr(zne_strategy) == expected

    def test_eq(self, noise_factors):
        """Test ZNEStrategy.__eq__() magic method."""
        noise_amplifier = Mock(NoiseAmplifier)
        extrapolator = Mock(Extrapolator)
        zne_strategy = ZNEStrategy(
            noise_factors=noise_factors,
            noise_amplifier=noise_amplifier,
            extrapolator=extrapolator,
        )
        assert zne_strategy == ZNEStrategy(
            noise_factors=noise_factors,
            noise_amplifier=noise_amplifier,
            extrapolator=extrapolator,
        )
        assert zne_strategy != ZNEStrategy(
            noise_factors=(*noise_factors, 707),
            noise_amplifier=noise_amplifier,
            extrapolator=extrapolator,
        )
        assert zne_strategy != ZNEStrategy(
            noise_factors=noise_factors,
            noise_amplifier=Mock(NoiseAmplifier),
            extrapolator=extrapolator,
        )
        assert zne_strategy != ZNEStrategy(
            noise_factors=noise_factors,
            noise_amplifier=noise_amplifier,
            extrapolator=Mock(Extrapolator),
        )
        assert zne_strategy != "zne_strategy"

    def test_bool(self, noise_factors):
        noise_amplifier = Mock(NoiseAmplifier)
        extrapolator = Mock(Extrapolator)
        zne_strategy = ZNEStrategy(
            noise_factors=noise_factors,
            noise_amplifier=noise_amplifier,
            extrapolator=extrapolator,
        )
        truth_value = not zne_strategy.is_noop
        assert bool(zne_strategy) is truth_value


class TestConstructors:
    """Test ZNEStrategy constructors."""

    def test_noop(self):
        zne_strategy = ZNEStrategy.noop()
        assert zne_strategy.is_noop


class TestNoiseFactors:
    """Test ZNEStrategy `noise_factors` property."""

    def test_default(self):
        zne_strategy = ZNEStrategy()
        zne_strategy.noise_factors = None
        assert zne_strategy.noise_factors == (1,)

    @mark.parametrize(
        "noise_factors",
        cases := [(1,), (3,), (1, 3), (1, 3, 5), [1, 3, 5], [1.2, 3, 5.4]],
        ids=[f"{nf}" for nf in cases],
    )
    def test_dispatch(self, noise_factors):
        """Test proper noise factors of different types."""
        zne_strategy = ZNEStrategy()
        zne_strategy.noise_factors = noise_factors
        assert zne_strategy.noise_factors == tuple(noise_factors)

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
    def test_sort(self, noise_factors, expected):
        """Test unsorted noise factors."""
        zne_strategy = ZNEStrategy()
        with warns(UserWarning):
            zne_strategy.noise_factors = noise_factors
        assert zne_strategy.noise_factors == expected

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
    def test_duplicates(self, noise_factors, expected):
        """Test duplicate noise factors."""
        zne_strategy = ZNEStrategy()
        with warns(UserWarning):
            zne_strategy.noise_factors = noise_factors
        assert zne_strategy.noise_factors == expected

    @mark.parametrize(
        "noise_factors",
        cases := NO_ITERS_NONE,
        ids=[f"{type(c)}" for c in cases],
    )
    def test_sequence(self, noise_factors):
        """Test type error is raised if noise factors are not Sequence."""
        zne_strategy = ZNEStrategy()
        with raises(TypeError):
            zne_strategy.noise_factors = noise_factors

    @mark.parametrize(
        "noise_factors",
        cases := [(), []],
        ids=[f"{type(c)}" for c in cases],
    )
    def test_empty(self, noise_factors):
        """Test value error is raised for empty lists of noise factors."""
        zne_strategy = ZNEStrategy()
        with raises(ValueError):
            zne_strategy.noise_factors = noise_factors

    @mark.parametrize(
        "noise_factors",
        cases := ["1", True, False, float("NaN"), [1, 3, "5"]],
        ids=[f"{type(c)}" for c in cases],
    )
    def test_real(self, noise_factors):
        """Test type error is raised if noise factors are not real numbers."""
        if not isinstance(noise_factors, Sequence):
            noise_factors = [noise_factors]
        zne_strategy = ZNEStrategy()
        with raises(TypeError):
            zne_strategy.noise_factors = noise_factors

    @mark.parametrize(
        "noise_factors",
        cases := [0, 0.9999, -1, -0.5, (1, 0), (0.9, 1.2)],
        ids=[f"{c}" for c in cases],
    )
    def test_geq_one(self, noise_factors):
        """Test value error is raised if any noise factor is less than one."""
        if not isinstance(noise_factors, Sequence):
            noise_factors = [noise_factors]
        zne_strategy = ZNEStrategy()
        with raises(ValueError):
            zne_strategy.noise_factors = noise_factors


class TestNoiseAmplifier:
    """Test ZNEStrategy `noise_amplifier` property."""

    def test_default(self):
        zne_strategy = ZNEStrategy()
        zne_strategy.noise_amplifier = None
        assert zne_strategy.noise_amplifier == MultiQubitAmplifier()

    @mark.parametrize(
        "noise_amplifier",
        cases := NO_NONE,
        ids=[f"{type(c)}" for c in cases],
    )
    def test_type_error(self, noise_amplifier):
        """Test type error is raised if not `NoiseAmplifier`."""
        zne_strategy = ZNEStrategy()
        with raises(TypeError):
            zne_strategy.noise_amplifier = noise_amplifier


class TestExtrapolator:
    """Test ZNEStrategy `extrapolator` property."""

    def test_default(self):
        zne_strategy = ZNEStrategy()
        zne_strategy.extrapolator = None
        assert zne_strategy.extrapolator == LinearExtrapolator()

    @mark.parametrize(
        "extrapolator",
        cases := NO_NONE,
        ids=[f"{type(c)}" for c in cases],
    )
    def test_type_error(self, extrapolator):
        """Test type error is raised if not `NoiseAmplifier`."""
        zne_strategy = ZNEStrategy()
        with raises(TypeError):
            zne_strategy.extrapolator = extrapolator


class TestProperties:
    """Test generic ZNEStrategy properties."""

    @mark.parametrize("noise_factors", [(1,), (1, 3), (1.2,), (2.1, 4.5)])
    def test_performs_noise_amplification(self, noise_factors):
        """Test if ZNEStrategy performs noise amplification."""
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        truth_value = any(nf > 1 for nf in noise_factors)
        if truth_value:
            assert zne_strategy.performs_noise_amplification
        else:
            assert not zne_strategy.performs_noise_amplification

    @mark.parametrize("noise_factors", [(1,), (1, 3), (1.2,), (2.1, 4.5)])
    def test_performs_zne(self, noise_factors):
        """Test if ZNEStrategy performs zero noise extrapolation."""
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        truth_value = any(nf > 1 for nf in noise_factors) and len(noise_factors) > 1
        if truth_value:
            assert zne_strategy.performs_zne
        else:
            assert not zne_strategy.performs_zne

    @mark.parametrize("noise_factors", [(1,), (1, 3), (1.2,), (2.1, 4.5)])
    def test_is_noop(self, noise_factors):
        """Test if ZNEStrategy is no-op."""
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        truth_value = tuple(noise_factors) == (1,)
        if truth_value:
            assert zne_strategy.is_noop
        else:
            assert not zne_strategy.is_noop


class TestNoiseAmplification:
    """Test ZNEStrategy noise amplification logic."""

    def test_amplify_circuit_noise(self, amplifier_mock):
        noise_factors = (1, 2, 3)
        zne_strategy = ZNEStrategy(noise_factors=noise_factors, noise_amplifier=amplifier_mock)
        circuit = QuantumCircuit(2)
        assert zne_strategy.amplify_circuit_noise(circuit, 1) == 0
        amplifier_mock.amplify_circuit_noise.assert_called_once_with(circuit, 1)
        amplifier_mock.amplify_circuit_noise.reset_mock()
        assert zne_strategy.amplify_circuit_noise(circuit, 1.2) == 1
        amplifier_mock.amplify_circuit_noise.assert_called_once_with(circuit, 1.2)
        circuit.h(0)
        amplifier_mock.amplify_circuit_noise.reset_mock()
        assert zne_strategy.amplify_circuit_noise(circuit, 2.4) == 2
        amplifier_mock.amplify_circuit_noise.assert_called_once_with(circuit, 2.4)

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


class TestExtrapolation:
    """Test ZNEStrategy extrapolation logic."""

    @mark.parametrize(
        "noise_factors, values, variances, num_results, extrapolate_return",
        [
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 1, [0, 1, {}]),
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 1, [0, 1, {"R2": 0.1}]),
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 2, [0, 1, {}]),
            ([1, 2, 3], [1, 2, 3], [0, 0, 0], 3, [0, 1, {"R2": 0.1, "P": 6.5}]),
        ],
    )
    def test_mitigate_noisy_result(
        self, noise_factors, values, variances, num_results, extrapolate_return
    ):
        val, err, meta = extrapolate_return
        extrapolator = Mock(Extrapolator)
        extrapolator.extrapolate_zero = Mock(return_value=tuple(extrapolate_return))
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        zne_strategy.extrapolator = extrapolator
        metadata = [{"variance": var, "shots": 1024} for var in variances]
        noisy_result = EstimatorResult(
            values=array(values * num_results), metadata=list(metadata * num_results)
        )
        result = zne_strategy.mitigate_noisy_result(noisy_result)
        assert result.values.tolist() == [val] * num_results
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
        assert result.metadata == [{"std_error": err, "zne": metadatum} for _ in range(num_results)]

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
        "noise_factors, values, std_errors",
        [
            ([1, 2], [0, 1], [0, 0]),
            ([1, 2.0], [0.4, 1.2], [0, None]),
        ],
    )
    def test_regression_data_from_result_group(self, noise_factors, values, std_errors):
        zne_strategy = ZNEStrategy(noise_factors=noise_factors)
        metadatum = {"shots": 1024}
        metadata = [
            {"variance": err**2, **metadatum} if err is not None else metadatum
            for err in std_errors
        ]
        result_group = EstimatorResult(values=array(values), metadata=list(metadata))
        data = zne_strategy._regression_data_from_result_group(result_group)
        expected = (
            noise_factors,
            values,
            [1 for _ in noise_factors],
            [1 if err is None else err for err in std_errors],
        )
        for dat, exp in zip(data, expected):
            assert dat == exp

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
        result_group = EstimatorResult(values=array(values), metadata=list(metadata))
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
        result_group = EstimatorResult(values=array(values), metadata=list(metadata))
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
