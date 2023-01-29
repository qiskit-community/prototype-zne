# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Initial Function implmention. Will be evolved and documented more in depth"""
from qiskit.circuit.library import Barrier
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit


def _folding_to_noise_factor(folding: int) -> int:
    """Converts number of foldings to noise factor."""
    return 2 * folding + 1


def _inverse_dag(dag_to_inverse: DAGCircuit) -> DAGCircuit:
    """Inverts dag circuit"""
    dag_to_inverse = dag_to_circuit(dag_to_inverse).inverse()
    return circuit_to_dag(dag_to_inverse)


def apply_folding(original_dag: DAGCircuit, num_foldings: int = 1) -> DAGCircuit:
    """Build dag circuit by composing copies of an input dag circuit."""
    noisy_dag = original_dag.copy_empty_like()
    noise_factor = _folding_to_noise_factor(num_foldings)
    for idx in range(noise_factor):
        if idx % 2 == 0:
            noisy_dag.compose(_inverse_dag(original_dag), inplace=True)
        else:
            noisy_dag.compose(original_dag, inplace=True)

        noisy_dag.apply_operation_back(Barrier(noisy_dag.num_qubits()), qargs=noisy_dag.qubits)
    return noisy_dag
