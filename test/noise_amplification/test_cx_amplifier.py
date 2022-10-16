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

from itertools import product

from pytest import fixture, mark
from qiskit.circuit.random import random_circuit

from zne.noise_amplification import CxAmplifier


class TestCxAmplifier:

    ################################################################################
    ## FIXTURES
    ################################################################################
    @fixture(scope="class")
    def noise_amplifier(self):
        return CxAmplifier(warn_user=False)

    ################################################################################
    ## TESTS
    ################################################################################
    @mark.parametrize(
        "circuit_seed, noise_factor",
        cases := tuple(
            product(
                [0, 5, 66, 1081, 1082],
                [1, 3, 5],
            )
        ),
        ids=[f"QuantumCircuit<{cs}>-{nf}" for cs, nf in cases],
    )
    def test_amplify_circuit_noise(self, noise_amplifier, circuit_seed, noise_factor):
        circuit = random_circuit(2, 2, seed=circuit_seed)
        noisy_circuit = noise_amplifier.amplify_circuit_noise(circuit, noise_factor)
        operation_gen = (operation for operation in noisy_circuit)
        for original_operation in circuit:
            original_instruction, original_qargs, _ = original_operation
            for _ in range(noise_factor if original_instruction.name == "cx" else 1):
                assert next(operation_gen) == original_operation
                instruction, qargs, _ = next(operation_gen)
                assert instruction.name == "barrier"
                assert qargs == original_qargs
