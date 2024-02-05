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
from test import ITERS, NO_INTS_NONE
from unittest.mock import Mock, call, patch

from numpy.random import default_rng
from pytest import approx, fixture, mark, raises, warns
from qiskit.circuit import CircuitInstruction, ParameterVector, QuantumCircuit
from qiskit.circuit.barrier import Barrier
from qiskit.circuit.library.standard_gates import CCXGate, CXGate, HGate, RZGate, XGate
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info.operators import Operator
from qiskit.transpiler.passes import RemoveBarriers

from zne.noise_amplification import (
    CxAmplifier,
    LocalFoldingAmplifier,
    MultiQubitAmplifier,
    TwoQubitAmplifier,
)

MOCK_TARGET_PATH = (
    "zne.noise_amplification.folding_amplifier.local_folding_amplifier.LocalFoldingAmplifier"
)


################################################################################
## MODULE FIXTURES
################################################################################
@fixture(scope="module")
def noise_amplifier():
    return LocalFoldingAmplifier()


@fixture(scope="module")
def noise_factor():
    return 3


@fixture(scope="module")
def patch_amplifier_with_mock():
    def factory_method(method_name=None, **kwargs):
        method_name = method_name or ""
        return patch(MOCK_TARGET_PATH + method_name, **kwargs)

    return factory_method


@fixture(scope="module")
def patch_amplifier_with_multiple_mocks(**kwargs):
    def factory_method(**kwargs):
        return patch.multiple(MOCK_TARGET_PATH, **kwargs)

    return factory_method


################################################################################
## INIT TESTS
################################################################################
def test_init_default_kwargs(patch_amplifier_with_mock):
    with patch_amplifier_with_mock(method_name="._set_gates_to_fold") as mock:
        LocalFoldingAmplifier()
    mock.assert_called_once_with(None)


def test_init_custom_kwargs(patch_amplifier_with_mock):
    with patch_amplifier_with_mock(method_name="._set_gates_to_fold") as mock:
        LocalFoldingAmplifier(gates_to_fold=2)
    mock.assert_called_once_with(2)


################################################################################
## PROPERTIES and SETTER TESTS
################################################################################
@mark.parametrize("gates_to_fold", cases := [1, 2, 3], ids=[f"{c}" for c in cases])
def test_set_gates_to_fold_int(gates_to_fold):
    noise_amplifier = LocalFoldingAmplifier()
    noise_amplifier._set_gates_to_fold(gates_to_fold)
    assert noise_amplifier.gates_to_fold == frozenset((gates_to_fold,))


@mark.parametrize("gates_to_fold", cases := ["h", "cx", "ccx"], ids=[f"{c}" for c in cases])
def test_set_gates_to_fold_str(gates_to_fold):
    noise_amplifier = LocalFoldingAmplifier()
    noise_amplifier._set_gates_to_fold(gates_to_fold)
    assert noise_amplifier.gates_to_fold == frozenset((gates_to_fold,))


@mark.parametrize(
    "gates_to_fold",
    cases := [["x"], (2,), ["h", 2, "ccx"], ("rz", 1, 3, "i")],
    ids=[f"{c}" for c in cases],
)
def test_set_gates_to_fold_sequence(gates_to_fold):
    noise_amplifier = LocalFoldingAmplifier()
    noise_amplifier._set_gates_to_fold(gates_to_fold)
    assert noise_amplifier.gates_to_fold == frozenset(gates_to_fold)


def test_set_gates_to_fold_none(noise_amplifier):
    noise_amplifier = LocalFoldingAmplifier()
    noise_amplifier._set_gates_to_fold(None)
    assert noise_amplifier.gates_to_fold is None


@mark.parametrize(
    "gates_to_fold",
    cases := [t for t in NO_INTS_NONE if t not in ITERS],
    ids=[str(type(t).__name__) for t in cases],
)
def test_set_gates_to_fold_type_error(gates_to_fold):
    with raises(TypeError):
        LocalFoldingAmplifier()._set_gates_to_fold(gates_to_fold)


@mark.parametrize(
    "gates_to_fold",
    cases := [(2, 1.0), ("h", 2, None), ("rz", 1j, 3, "i")],
    ids=[f"{c}" for c in cases],
)
def test_validate_gates_to_fold_type_error(gates_to_fold):
    with raises(TypeError):
        LocalFoldingAmplifier()._validate_gates_to_fold(frozenset(gates_to_fold))


@mark.parametrize("gates_to_fold", cases := [(1, 0), (-2, "h")], ids=[f"{c}" for c in cases])
def test_validate_gates_to_fold_value_error(gates_to_fold):
    with raises(ValueError):
        LocalFoldingAmplifier()._validate_gates_to_fold(frozenset(gates_to_fold))


@mark.parametrize(
    "gates_to_fold", cases := [(1, "areeq"), ("pedro", "h")], ids=[f"{c}" for c in cases]
)
def test_validate_gates_to_fold_warning(gates_to_fold):
    with warns(UserWarning):
        LocalFoldingAmplifier()._validate_gates_to_fold(frozenset(gates_to_fold))


################################################################################
## PUBLIC METHODS TESTS
################################################################################
def test_amplify_circuit_noise(
    patch_amplifier_with_multiple_mocks, noise_amplifier, get_random_circuit, circuit, noise_factor
):
    # TODO: new test after refactor
    # TODO: test barriers are added
    example_foldings = list(range(len(circuit)))
    example_circuits = [get_random_circuit(i) for i in range(len(circuit) + 1)]
    mocks = {
        "_validate_noise_factor": Mock(),
        "_build_foldings_per_gate": Mock(return_value=example_foldings),
        "_append_folded": Mock(side_effect=example_circuits[1:]),
    }
    circuit_mock_target = (
        "zne.noise_amplification.folding_amplifier.local_folding_amplifier"
        ".QuantumCircuit.copy_empty_like"
    )
    with patch_amplifier_with_multiple_mocks(**mocks):
        with patch(circuit_mock_target, return_value=example_circuits[0]) as _:
            _ = noise_amplifier.amplify_circuit_noise(circuit, noise_factor)
    mocks["_validate_noise_factor"].assert_called_once_with(noise_factor)
    mocks["_build_foldings_per_gate"].assert_called_once_with(circuit, noise_factor)
    # circuit_copy_mock.assert_called_once_with()
    calls = [
        call(c, o, f)
        for c, o, f in zip(example_circuits[:-1], circuit.data, example_foldings)
        if f != 0
    ]
    assert mocks["_append_folded"].call_count == len(calls)
    # mocks["_append_folded"].assert_has_calls(calls, any_order=False)
    # assert noisy_circuit == example_circuits[-1]


################################################################################
## PRIVATE METHODS TESTS
################################################################################
@mark.parametrize(
    "foldings, mask, expected",
    cases := [
        ([], [False, False, False], [0, 0, 0]),
        ([5, 6], [True, True], [5, 6]),
        ([2, 1, 2], [False, False, True, False, True, True], [0, 0, 2, 0, 1, 2]),
    ],
    ids=[f"{len(f)}-{len(m)}-{len(e)}" for f, m, e in cases],
)
def test_build_foldings_per_gate(
    noise_amplifier,
    patch_amplifier_with_multiple_mocks,
    foldings,
    mask,
    expected,
):
    noise_factor = 3
    circuit = QuantumCircuit(2)
    for i, _ in enumerate(mask):
        circuit.h(i % circuit.num_qubits)
    mocks = {
        "_check_gate_folds": Mock(side_effect=mask),
        "_build_foldings": Mock(return_value=foldings),
    }
    with patch_amplifier_with_multiple_mocks(**mocks):
        gate_foldings = noise_amplifier._build_foldings_per_gate(circuit, noise_factor)
    calls = [call(operation) for operation in circuit.data]
    assert mocks["_check_gate_folds"].call_count == len(calls)
    mocks["_check_gate_folds"].assert_has_calls(calls, any_order=False)
    mocks["_build_foldings"].assert_called_once_with(noise_factor, mask.count(True))
    assert len(gate_foldings) == len(mask)
    assert gate_foldings == expected


@mark.parametrize(
    "folding_nums, sub_foldings",
    cases := [
        ([0, 0], []),
        ([2, 3], [0, 0, 1, 0, 1, 1]),
    ],
    ids=[f"{len(f)}-{len(m)}" for f, m in cases],
)
def test_build_foldings(
    noise_amplifier,
    patch_amplifier_with_multiple_mocks,
    folding_nums,
    sub_foldings,
):
    num_full_foldings, num_sub_foldings = folding_nums
    num_gates_to_fold = len(sub_foldings)
    noise_factor = 3
    mocks = {
        "_compute_folding_nums": Mock(return_value=folding_nums),
        "_build_sub_foldings": Mock(return_value=sub_foldings),
    }
    with patch_amplifier_with_multiple_mocks(**mocks):
        foldings = noise_amplifier._build_foldings(noise_factor, num_gates_to_fold)
    mocks["_compute_folding_nums"].assert_called_once_with(noise_factor, num_gates_to_fold)
    mocks["_build_sub_foldings"].assert_called_once_with(num_sub_foldings, num_gates_to_fold)
    assert foldings == [num_full_foldings + sf for sf in sub_foldings]


class TestCheckGateFolds:
    @mark.parametrize("num_qubits", cases := [0, 1, 3], ids=[f"{c}" for c in cases])
    def test_check_gate_folds_barrier(self, noise_amplifier, num_qubits):
        operation = CircuitInstruction(Barrier(num_qubits), tuple(range(num_qubits)), ())
        assert noise_amplifier._check_gate_folds(operation) is False

    @mark.parametrize(
        "operation",
        cases := [
            CircuitInstruction(HGate(), (1,), ()),
            CircuitInstruction(CXGate(), (0, 1), ()),
            CircuitInstruction(RZGate(0), (0, 1), ()),
            CircuitInstruction(XGate(), (0,), ()),
            CircuitInstruction(CCXGate(), (0, 1, 2), ()),
        ],
        ids=[f"<{o[0].name}>" for o in cases],
    )
    def test_check_gate_folds_none(self, noise_amplifier, operation):
        noise_amplifier = LocalFoldingAmplifier(gates_to_fold=None)
        assert noise_amplifier._check_gate_folds(operation) is True

    @mark.parametrize(
        "operation, gates_to_fold, expected",
        cases := [
            (CircuitInstruction(HGate(), (1,), ()), 1, True),
            (CircuitInstruction(CXGate(), (0, 1), ()), [1, 2], True),
            (CircuitInstruction(RZGate(0), (0, 1), ()), 1, False),
            (CircuitInstruction(XGate(), (0,), ()), 2, False),
            (CircuitInstruction(CCXGate(), (0, 1, 2), ()), [2, 3], True),
            (CircuitInstruction(CCXGate(), (0, 1, 2), ()), [1, 2], False),
        ],
        ids=[f"<{o[0].name}>-{gtf}-{e}" for o, gtf, e in cases],
    )
    def test_check_gate_folds_num_qubits(self, operation, gates_to_fold, expected):
        noise_amplifier = LocalFoldingAmplifier(gates_to_fold=gates_to_fold)
        assert noise_amplifier._check_gate_folds(operation) is expected

    @mark.parametrize(
        "operation, gates_to_fold, expected",
        cases := [
            (CircuitInstruction(HGate(), (1,), ()), "h", True),
            (CircuitInstruction(CXGate(), (0, 1), ()), ["h", "cx"], True),
            (CircuitInstruction(RZGate(0), (0, 1), ()), "h", False),
            (CircuitInstruction(XGate(), (0,), ()), ["h", "cx"], False),
            (CircuitInstruction(CCXGate(), (0, 1, 2), ()), "ccx", True),
        ],
        ids=[f"<{o[0].name}>-{gtf}-{e}" for o, gtf, e in cases],
    )
    def test_check_gate_folds_instruction_names(self, operation, gates_to_fold, expected):
        noise_amplifier = LocalFoldingAmplifier(gates_to_fold=gates_to_fold)
        assert noise_amplifier._check_gate_folds(operation) is expected


@mark.parametrize(
    "num_foldings, num_instructions",
    cases := tuple(
        product(
            [0, 1, 3],
            [3, 7],
        )
    ),
    ids=[f"{nf}-{ni}" for nf, ni in cases],
)
class TestBuildSubFoldings:
    def test_sub_foldings_from_first(self, num_foldings, num_instructions):
        noise_amplifier = LocalFoldingAmplifier(sub_folding_option="from_first")
        sub_foldings_list = noise_amplifier._build_sub_foldings(num_foldings, num_instructions)
        assert len(sub_foldings_list) == num_instructions
        assert sum(sub_foldings_list) == num_foldings
        assert sub_foldings_list == [1] * num_foldings + [0] * (num_instructions - num_foldings)

    def test_sub_foldings_from_last(self, num_foldings, num_instructions):
        noise_amplifier = LocalFoldingAmplifier(sub_folding_option="from_last")
        sub_foldings_list = noise_amplifier._build_sub_foldings(num_foldings, num_instructions)
        assert len(sub_foldings_list) == num_instructions
        assert sum(sub_foldings_list) == num_foldings
        assert sub_foldings_list == [0] * (num_instructions - num_foldings) + [1] * num_foldings

    @mark.parametrize("seed", cases := [1, 5, 66], ids=[f"{c}" for c in cases])
    def test_build_sub_foldings_random(self, num_foldings, num_instructions, seed):
        noise_amplifier = LocalFoldingAmplifier(sub_folding_option="random", random_seed=seed)
        sub_foldings_list = noise_amplifier._build_sub_foldings(num_foldings, num_instructions)
        assert len(sub_foldings_list) == num_instructions
        assert sum(sub_foldings_list) == num_foldings
        idxs = default_rng(seed).choice(num_instructions, size=num_foldings, replace=False)
        assert sub_foldings_list == [1 if i in idxs else 0 for i in range(num_instructions)]


@mark.parametrize(
    "seed , num_foldings",
    cases := tuple(
        product(
            [1, 2, 3],
            [0, 1, 3],
        )
    ),
    ids=[f"Instruction<{s}>-{nf}" for s, nf in cases],
)
def test_append_folded(noise_amplifier, circuit, get_random_circuit, seed, num_foldings):
    operation = get_random_circuit(seed).data[0]
    noisy_circuit = noise_amplifier._append_folded(circuit.copy(), operation, num_foldings)
    assert noisy_circuit.data[: len(circuit)] == circuit.data
    operation_gen = (operation for operation in noisy_circuit[len(circuit) :])
    instruction, qargs, cargs = operation
    barrier = CircuitInstruction(Barrier(len(qargs)), qargs, [])
    inverse = CircuitInstruction(instruction.inverse(), qargs, cargs)
    for _ in range(num_foldings):
        assert next(operation_gen) == barrier
        assert next(operation_gen) == operation
        assert next(operation_gen) == barrier
        assert next(operation_gen) == inverse
    assert next(operation_gen) == barrier
    assert next(operation_gen) == operation
    assert next(operation_gen) == barrier


@mark.parametrize("num_foldings", [0.0, 0.5, 1.0, -1.0])
def test_append_folded_type_error(circuit, noise_amplifier, num_foldings):
    with raises(TypeError):
        noise_amplifier._append_folded(circuit, circuit.data[0], num_foldings)


@mark.parametrize("num_foldings", [-1, -2])
def test_append_folded_value_error(circuit, noise_amplifier, num_foldings):
    with raises(ValueError):
        noise_amplifier._append_folded(circuit, circuit.data[0], num_foldings)


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

    def test_append_folded_parameters(self, noise_amplifier, parametrized_circuit, noise_factor):
        example_operation = parametrized_circuit.data[-1]
        noisy_circuit = noise_amplifier._append_folded(
            parametrized_circuit.copy(), example_operation, noise_factor
        )
        instruction_gen = (
            instruction for instruction, _, _ in noisy_circuit[len(parametrized_circuit) :]
        )
        original_instruction, _, _ = example_operation
        for i in range(noise_factor):
            if i % 2 == 0:
                next(instruction_gen)
                assert next(instruction_gen).params == original_instruction.params
            else:
                next(instruction_gen)
                assert next(instruction_gen).params == original_instruction.inverse().params


################################################################################
## INTEGRATION TESTS
################################################################################
@mark.parametrize(
    "circuit, noise_factor, gates_to_fold, sub_folding_option",
    cases := tuple(
        product(
            [
                random_circuit(5, 3, seed=0),
                random_circuit(5, 3, seed=5),
                random_circuit(5, 6, seed=66),
                random_circuit(5, 6, seed=1081),
            ],
            [1.5, 3.3, 17 / 3],
            [None, 1, [2, "h", "rz", "u2", "u3"]],
            ["from_last", "from_first", "random"],
        )
    ),
    ids=[f"{type(c).__name__}<{len(c)}>-{nf}-{gtf}-{sfo}" for c, nf, gtf, sfo in cases],
)
class TestIntegration:
    @mark.filterwarnings("ignore::UserWarning")
    def test_noise_factor_of_folded_circuit(
        self, circuit, noise_factor, gates_to_fold, sub_folding_option
    ):
        noise_amplifier = LocalFoldingAmplifier(
            gates_to_fold=gates_to_fold, sub_folding_option=sub_folding_option
        )
        noisy_circuit = noise_amplifier.amplify_circuit_noise(circuit.copy(), noise_factor)
        noisy_circuit = RemoveBarriers()(noisy_circuit)
        num_gates_to_fold = [
            noise_amplifier._check_gate_folds(operation) for operation in circuit.data
        ].count(True)
        num_instructions_folded = [
            noise_amplifier._check_gate_folds(operation) for operation in noisy_circuit.data
        ].count(True)
        num_foldings = round(num_gates_to_fold * (noise_factor - 1) / 2.0)
        closest_noise_factor = 2 * num_foldings / num_gates_to_fold + 1
        assert num_instructions_folded / num_gates_to_fold == approx(closest_noise_factor)
        assert Operator(noisy_circuit).equiv(Operator(circuit))


################################################################################
## FACADES
################################################################################
class TestFacades:
    @mark.parametrize(
        "cls, configs",
        [
            (CxAmplifier, {"gates_to_fold": "cx"}),
            (TwoQubitAmplifier, {"gates_to_fold": 2}),
        ],
    )
    def test_amplifier_facade(self, cls, configs):
        amplifier = cls()
        assert isinstance(amplifier, LocalFoldingAmplifier)
        for key, value in configs.items():
            assert getattr(amplifier, key) == frozenset([value])

    def test_multi_qubit_amplifier(self):
        amplifier = MultiQubitAmplifier()
        assert isinstance(amplifier, LocalFoldingAmplifier)
        assert amplifier.gates_to_fold is None
        circuit = QuantumCircuit(4)
        circuit.h(0)
        circuit.z(3)
        circuit.cx(0, 1)
        circuit.x(1)
        circuit.ccx(0, 1, 2)
        circuit.y(2)
        circuit.ecr(2, 3)
        circuit.measure_all()
        for operation in circuit.data:
            instruction = operation[0]
            skipped_instructions = {"barrier", "measure"}
            expected = instruction.num_qubits > 1 and instruction.name not in skipped_instructions
            assert amplifier._check_gate_folds(operation) == expected
