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
import copy

from qiskit.circuit.library import Barrier
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit


def _inverse_dag(dag_to_inverse: DAGCircuit) -> DAGCircuit:
    """Inverts dag circuit"""
    dag_to_inverse = dag_to_circuit(dag_to_inverse).inverse()
    return circuit_to_dag(dag_to_inverse)


def apply_folding(original_dag: DAGCircuit, num_foldings: int) -> DAGCircuit:
    """Build dag circuit by composing copies of an input dag circuit."""
    noisy_dag = copy.deepcopy(original_dag)
    inverse_dag = _inverse_dag(original_dag)
    for _ in range(num_foldings):
        noisy_dag.apply_operation_back(Barrier(noisy_dag.num_qubits()), qargs=noisy_dag.qubits)
        noisy_dag.compose(inverse_dag, inplace=True)
        noisy_dag.apply_operation_back(Barrier(noisy_dag.num_qubits()), qargs=noisy_dag.qubits)
        noisy_dag.compose(original_dag, inplace=True)
    return noisy_dag
