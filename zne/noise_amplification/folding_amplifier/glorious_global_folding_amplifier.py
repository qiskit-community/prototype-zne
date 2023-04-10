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


"""Glorious Global DAG Folding Noise Amplification (Temporary)"""

from typing import Tuple

from qiskit.circuit.library import Barrier
from qiskit.dagcircuit import DAGCircuit

from .glorious_folding_amplifier import GloriousFoldingAmplifier


class GloriousGlobalFoldingAmplifier(GloriousFoldingAmplifier):
    """Alternatingly composes the circuit and its inverse as many times as indicated
    by the ``noise_factor``.

    References:
        [1] T. Giurgica-Tiron et al. (2020).
            Digital zero noise extrapolation for quantum error mitigation.
            `<https://ieeexplore.ieee.org/document/9259940>`
    """

    def __init__(self, barriers: bool = True) -> None:
        self._set_barriers(barriers)

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def barriers(self) -> bool:
        """Barriers setter"""
        return self._barriers

    def _set_barriers(self, barriers: bool) -> None:
        """Set barriers property"""
        self._barriers = bool(barriers)

    ################################################################################
    ## INTERFACE IMPLEMENTATION
    ################################################################################
    def amplify_dag_noise(self, dag: DAGCircuit, noise_factor: float) -> DAGCircuit:
        """Applies global folding to input DAGCircuit and returns amplified circuit"""
        num_nodes = dag.size()
        num_foldings = self._compute_folding_nums(noise_factor, num_nodes)
        return self._apply_full_folding(dag, num_foldings)  # type: ignore[arg-type]

    ################################################################################
    ## AUXILIARY
    ################################################################################
    def _apply_full_folding(
        self,
        dag: DAGCircuit,
        num_foldings: int,
    ) -> DAGCircuit:
        """Fully folds the original DAG circuit a number of ``num_foldings`` times.

        Args:
            dag: The original dag circuit without foldings.
            num_foldings: Number of times the circuit should be folded.

        Returns:
            DAGCircuit: The noise amplified DAG circuit.
        """
        noisy_dag = dag.copy_empty_like()
        inverse_dag = self._invert_dag(dag)
        if self.barriers:
            barrier = Barrier(noisy_dag.num_qubits())
            noisy_dag.apply_operation_back(barrier, noisy_dag.qubits)
        self._compose(noisy_dag, dag, noisy_dag.qubits)
        for _ in range(num_foldings):
            self._compose(noisy_dag, inverse_dag, noisy_dag.qubits)
            self._compose(noisy_dag, dag, noisy_dag.qubits)
        return noisy_dag

    def _compose(
        self, dag: DAGCircuit, dag_to_compose: DAGCircuit, qargs: Tuple = ()
    ) -> DAGCircuit:
        dag.compose(dag_to_compose, inplace=True)
        if self.barriers:
            barrier = Barrier(dag.num_qubits())
            dag.apply_operation_back(barrier, qargs)

    def _invert_dag(self, dag_to_inverse: DAGCircuit) -> DAGCircuit:
        """Inverts an input dag circuit.

        Args:
            dag_to_inverse: The original dag circuit to invert.

        Returns:
            DAGCircuit: The inverted DAG circuit.
        """
        inverse_dag = dag_to_inverse.copy_empty_like()
        for node in dag_to_inverse.topological_op_nodes():
            inverse_dag.apply_operation_front(node.op.inverse(), qargs=node.qargs, cargs=node.cargs)
        return inverse_dag
