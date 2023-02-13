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

from itertools import product
from unittest.mock import Mock, patch

from numpy.random import default_rng
from pytest import approx, fixture, mark, raises
from qiskit.circuit import Barrier, CircuitInstruction, ParameterVector, QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info.operators import Operator
from qiskit.transpiler.passes import RemoveBarriers

from zne.noise_amplification.folding_amplifier import GlobalFoldingAmplifier

MOCK_TARGET_PATH = (
    "zne.noise_amplification.folding_amplifier.global_folding_amplifier.GlobalFoldingAmplifier"
)


################################################################################
## MODULE FIXTURES
################################################################################
@fixture(scope="module")
def noise_amplifier():
    return GlobalFoldingAmplifier()


@fixture(scope="module")
def get_sub_circuit():
    def factory_method(circuit, sub_folding_option, num_foldings=1, random_seed=0):
        noise_amplifier = GlobalFoldingAmplifier(
            sub_folding_option=sub_folding_option, random_seed=random_seed
        )
        return noise_amplifier._get_sub_folding(circuit, num_foldings)

    return factory_method


@fixture(scope="module")
def patch_amplifier_with_mock():
    def factory_method(method_name=None, **kwargs):
        method_name = method_name or ""
        return patch(MOCK_TARGET_PATH + method_name, **kwargs)

    return factory_method


@fixture(scope="module")
def patch_amplifier_with_multiple_mocks():
    def factory_method(**kwargs):
        return patch.multiple(MOCK_TARGET_PATH, **kwargs)

    return factory_method


################################################################################
## PUBLIC METHODS TESTS
################################################################################
def test_amplify_circuit_noise(
    noise_amplifier, circuit, get_random_circuit, patch_amplifier_with_multiple_mocks
):
    # TODO: rewrite test with class refactor
    mocks = {
        "_validate_noise_factor": Mock(),
        "_compute_folding_nums": Mock(return_value=(1, 2)),
        "_apply_full_folding": Mock(return_value=get_random_circuit(2)),
        "_apply_sub_folding": Mock(return_value=get_random_circuit(3)),
    }
    circuit_mock_target = (
        "zne.noise_amplification.folding_amplifier.global_folding_amplifier"
        ".QuantumCircuit.copy_empty_like"
    )
    with patch_amplifier_with_multiple_mocks(**mocks):
        with patch(circuit_mock_target, return_value=get_random_circuit(1)) as _:
            _ = noise_amplifier.amplify_circuit_noise(circuit, 3)
    mocks["_validate_noise_factor"].assert_called_once_with(3)
    # circuit_copy_mock.assert_called_once_with()
    mocks["_compute_folding_nums"].assert_called_once_with(3, len(circuit))
    # mocks["_apply_full_folding"].assert_called_once_with(get_random_circuit(1), circuit, 1)
    # mocks["_apply_sub_folding"].assert_called_once_with(get_random_circuit(2), circuit, 2)
    # assert noisy_circuit == get_random_circuit(3)


################################################################################
## PRIVATE METHODS TESTS
################################################################################
@mark.parametrize(
    "circuit_seed, num_foldings",
    cases := tuple(
        product(
            [0, 5, 66, 1081, 1082],
            [0, 1, 2, 3],
        )
    ),
    ids=[f"QuantumCircuit<{cs}>-{nf}" for cs, nf in cases],
)
def test_apply_full_folding(noise_amplifier, get_random_circuit, circuit_seed, num_foldings):
    circuit = get_random_circuit(circuit_seed)
    noisy_circuit = circuit.copy_empty_like()
    noisy_circuit = noise_amplifier._apply_full_folding(noisy_circuit, circuit, num_foldings)
    noisy_operation = (operation for operation in noisy_circuit)
    num_gates = 0
    for i in range(2 * num_foldings + 1):
        if i % 2 == 0:
            for original_operation in circuit:
                assert next(noisy_operation) == original_operation
                num_gates += 1
        else:
            for original_operation in circuit.inverse():
                assert next(noisy_operation) == original_operation
                num_gates += 1
        instruction, qargs, cargs = next(noisy_operation)
        assert instruction == Barrier(circuit.num_qubits)
        assert qargs == noisy_circuit.qubits
        assert cargs == []
    assert 2 * num_foldings + 1 == num_gates / len(circuit)


@mark.parametrize(
    "noisy_circuit",
    cases := [
        random_circuit(2, 3, seed=0),
        random_circuit(2, 6, seed=5),
    ],
    ids=[f"{type(c).__name__}<{len(c)}>" for c in cases],
)
def test_apply_sub_folding_wo_folding(noise_amplifier, circuit, noisy_circuit):
    assert noisy_circuit == noise_amplifier._apply_sub_folding(noisy_circuit, circuit, 0)


@mark.parametrize(
    "sub_circuit, num_foldings",
    cases := tuple(
        zip(
            [
                random_circuit(2, 3, seed=0),
                random_circuit(2, 6, seed=5),
            ],
            [1, 3],
        )
    ),
    ids=[f"{type(c).__name__}<{len(c)}>-{nf}" for c, nf in cases],
)
def test_apply_sub_folding(
    noise_amplifier,
    circuit,
    get_random_circuit,
    patch_amplifier_with_mock,
    sub_circuit,
    num_foldings,
):
    noisy_circuit_in = get_random_circuit(3)
    with patch_amplifier_with_mock(
        method_name="._get_sub_folding", return_value=sub_circuit
    ) as mock:
        noisy_circuit_out = noise_amplifier._apply_sub_folding(
            noisy_circuit_in.copy(), circuit, num_foldings
        )
        mock.assert_called_once_with(circuit, num_foldings)
    original_circuit_length = len(noisy_circuit_in)
    assert noisy_circuit_out.data[:original_circuit_length] == noisy_circuit_in.data
    extended_circuit_length = original_circuit_length + len(sub_circuit)
    noisy_circuit_slice = noisy_circuit_out.data[original_circuit_length:extended_circuit_length]
    assert noisy_circuit_slice == sub_circuit.inverse().data
    assert noisy_circuit_out.data[extended_circuit_length:] == sub_circuit.data


@mark.parametrize(
    "circuit, num_foldings",
    cases := tuple(
        product(
            [
                random_circuit(2, 3, seed=0),
                random_circuit(2, 3, seed=5),
                random_circuit(2, 6, seed=66),
                random_circuit(2, 6, seed=1081),
            ],
            [1, 2, 3],
        )
    ),
    ids=[f"{type(c).__name__}<{len(c)}>-{nf}" for c, nf in cases],
)
class TestGetSubFolding:
    def test_sub_folding_from_last(self, get_sub_circuit, circuit, num_foldings):
        sub_circuit = get_sub_circuit(circuit, "from_last", num_foldings)
        sub_data = (operation for operation in sub_circuit)
        original_data = (operation for operation in circuit[-num_foldings:])
        for _ in range(num_foldings):
            o_instruction, o_qargs, o_cargs = next(original_data)
            # instruction, qargs, cargs = next(sub_data)
            # assert instruction == Barrier(len(o_qargs))
            # assert qargs == o_qargs
            # assert cargs == []
            instruction, qargs, cargs = next(sub_data)
            assert instruction == o_instruction
            assert qargs == o_qargs
            assert cargs == o_cargs
        with raises(StopIteration):
            next(original_data)
        with raises(StopIteration):
            next(sub_data)

    def test_sub_folding_from_first(self, get_sub_circuit, circuit, num_foldings):
        sub_circuit = get_sub_circuit(circuit, "from_first", num_foldings)
        sub_data = (operation for operation in sub_circuit)
        original_data = (operation for operation in circuit[:num_foldings])
        for _ in range(num_foldings):
            o_instruction, o_qargs, o_cargs = next(original_data)
            # instruction, qargs, cargs = next(sub_data)
            # assert instruction == Barrier(len(o_qargs))
            # assert qargs == o_qargs
            # assert cargs == []
            instruction, qargs, cargs = next(sub_data)
            assert instruction == o_instruction
            assert qargs == o_qargs
            assert cargs == o_cargs
        with raises(StopIteration):
            next(original_data)
        with raises(StopIteration):
            next(sub_data)

    @mark.parametrize("seed", cases := [1, 5, 66], ids=[f"{s}" for s in cases])
    def test_get_sub_folding_random(self, get_sub_circuit, circuit, num_foldings, seed):
        sub_circuit = get_sub_circuit(circuit, "random", num_foldings, random_seed=seed)
        sub_data = (operation for operation in sub_circuit)
        idxs = sorted(default_rng(seed).choice(len(circuit), size=num_foldings, replace=False))
        original_data = (circuit.data[i] for i in idxs)
        for _ in range(num_foldings):
            o_instruction, o_qargs, o_cargs = next(original_data)
            # instruction, qargs, cargs = next(sub_data)
            # assert instruction == Barrier(len(o_qargs))
            # assert qargs == o_qargs
            # assert cargs == []
            instruction, qargs, cargs = next(sub_data)
            assert instruction == o_instruction
            assert qargs == o_qargs
            assert cargs == o_cargs
        with raises(StopIteration):
            next(original_data)
        with raises(StopIteration):
            next(sub_data)


class TestParametrizedCircuits:
    @fixture(scope="class")
    def parametrized_circuit(self):
        circuit = QuantumCircuit(2)
        params = ParameterVector("P", 4)
        circuit.ry(params[0], 0)
        circuit.rz(params[0], 1)
        circuit.crx(params[1], 0, 1)
        circuit.rz(params[2], 0)
        circuit.cu(params[3], params[0], params[1], params[0], 1, 0)
        circuit.ry(params[3], 1)
        circuit.crx(params[3], 0, 1)
        return circuit

    @fixture(scope="function")
    def noisy_circuit(self, noise_amplifier, parametrized_circuit):
        noisy_circuit = parametrized_circuit.copy_empty_like()
        noisy_circuit = noise_amplifier._apply_full_folding(noisy_circuit, parametrized_circuit, 1)
        return noisy_circuit

    @mark.parametrize(
        "sub_folding_option, sub_folding_index",
        cases := tuple(
            zip(
                ["from_last", "from_first", "random"],
                [-1, 0, 3],
            )
        ),
        ids=["from_last", "from_first", "random"],
    )
    def test_get_sub_folding_with_parameters(
        self,
        get_sub_circuit,
        parametrized_circuit,
        sub_folding_option,
        sub_folding_index,
    ):
        sub_circuit = get_sub_circuit(
            parametrized_circuit, sub_folding_option, num_foldings=1, random_seed=1
        )
        assert sub_circuit.data[0] == parametrized_circuit.data[sub_folding_index]
        assert len(sub_circuit._parameter_table) == 1

    def test_apply_full_folding_circuit_parameters(self, parametrized_circuit, noisy_circuit):
        noisy_operation = (operation for operation in noisy_circuit)
        barrier = CircuitInstruction(Barrier(noisy_circuit.num_qubits), noisy_circuit.qubits, [])
        for circuit in [parametrized_circuit, parametrized_circuit.inverse(), parametrized_circuit]:
            for original_instruction, _, _ in circuit:
                instruction, _, _ = next(noisy_operation)
                assert instruction.params == original_instruction.params
            assert next(noisy_operation) == barrier


################################################################################
## INTEGRATION TESTS
################################################################################
@mark.parametrize(
    "circuit, noise_factor, sub_folding_option",
    cases := tuple(
        product(
            [
                random_circuit(5, 3, seed=0),
                random_circuit(5, 3, seed=5),
                random_circuit(5, 6, seed=66),
                random_circuit(5, 6, seed=1081),
            ],
            [1.5, 3.3, 17 / 3],
            ["from_last", "from_first", "random"],
        )
    ),
    ids=[f"{type(c).__name__}<{len(c)}>-{nf}-{sfo}" for c, nf, sfo in cases],
)
class TestIntegration:
    @mark.filterwarnings("ignore::UserWarning")
    def test_noise_factor_of_folded_circuit(self, circuit, noise_factor, sub_folding_option):
        noise_amplifier = GlobalFoldingAmplifier(sub_folding_option=sub_folding_option)
        noisy_circuit = noise_amplifier.amplify_circuit_noise(circuit.copy(), noise_factor)
        noisy_circuit = RemoveBarriers()(noisy_circuit)
        num_instructions = len(circuit)
        num_foldings = round(num_instructions * (noise_factor - 1) / 2.0)
        closest_noise_factor = 2 * num_foldings / num_instructions + 1
        assert len(noisy_circuit) / len(circuit) == approx(closest_noise_factor)
        assert Operator(noisy_circuit).equiv(Operator(circuit))
