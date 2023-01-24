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
from qiskit.dagcircuit import DAGCircuit


def apply_folding(noisy_dag: DAGCircuit, original_dag: DAGCircuit, copies: int = 2) -> DAGCircuit:
    """Initial function for now, will be evolved and documented more in depth"""

    for _ in range(copies):
        noisy_dag.compose(original_dag, inplace=True)
        noisy_dag.apply_operation_back(Barrier(noisy_dag.num_qubits()), qargs=noisy_dag.qubits)
    return noisy_dag


def dag_duplicator(dag_circuit: DAGCircuit) -> DAGCircuit:
    """Initial function for now, will be evolved and documented more in depth"""

    return apply_folding(noisy_dag=dag_circuit.copy_empty_like(), original_dag=dag_circuit)
