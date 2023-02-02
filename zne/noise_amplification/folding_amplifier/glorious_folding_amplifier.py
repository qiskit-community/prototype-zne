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

"""Glorious DAG Folding Noise Amplification (Temporary)"""

import copy

from qiskit.circuit.library import Barrier
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit

from ..noise_amplifier import DAGNoiseAmplifier


class GloriousFoldingAmplifier(DAGNoiseAmplifier):
    """Alternatingly composes the circuit and its inverse as many times as indicated
    by the ``noise_factor``.
    """

    def amplify_dag_noise(self, dag: DAGCircuit, noise_factor: float) -> DAGCircuit:
        self._validate_noise_factor(noise_factor)
        num_full_foldings = self._compute_folding_nums(noise_factor)
        return self._apply_full_folding(dag, num_full_foldings)

    def _apply_full_folding(
        self,
        dag: DAGCircuit,
        num_foldings: int,
    ) -> DAGCircuit:
        """Fully folds the original DAG circuit a number of ``num_foldings`` times."""
        barrier = Barrier(dag.num_qubits())
        inverse_dag = self._invert_dag(dag)
        noisy_dag = copy.deepcopy(dag)
        for _ in range(num_foldings):
            noisy_dag.apply_operation_back(barrier, qargs=noisy_dag.qubits)
            noisy_dag.compose(inverse_dag, inplace=True)
            noisy_dag.apply_operation_back(barrier, qargs=noisy_dag.qubits)
            noisy_dag.compose(dag, inplace=True)
        # noisy_dag.apply_operation_back(barrier, qargs=noisy_dag.qubits)
        return noisy_dag

    def _invert_dag(self, dag_to_inverse: DAGCircuit) -> DAGCircuit:
        """Inverts a dag circuit on a copy of the original dag"""
        dag_to_inverse = dag_to_circuit(dag_to_inverse).inverse()
        return circuit_to_dag(dag_to_inverse)

    def _validate_noise_factor(self, noise_factor: float) -> None:
        """Validates noise factor."""
        if noise_factor < 1:
            raise ValueError(
                f"{self.name} expects a positive float noise_factor >= 1."
                f"Received {noise_factor} instead."
            )
        if noise_factor % 2 == 0:
            raise ValueError(
                f"{self.name} expects a positive odd noise_factor. "
                f"Received {noise_factor} instead."
            )

    def _compute_folding_nums(self, noise_factor: float) -> int:
        """Compute num foldings."""
        return int((noise_factor - 1) / 2)
