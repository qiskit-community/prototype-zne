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

"""Glorious Local DAG Folding Noise Amplification (Temporary)"""

from collections.abc import Set
from typing import Tuple, Union

from qiskit.circuit import Operation
from qiskit.circuit.library import Barrier, standard_gates
from qiskit.dagcircuit import DAGCircuit, DAGOpNode

from .glorious_folding_amplifier import GloriousFoldingAmplifier


class GloriousLocalFoldingAmplifier(GloriousFoldingAmplifier):
    """Amplifies noise in the circuit by said gate and its inverse alternatingly as many times as
    indicated by noise_factor. The gates that should be folded can be specified by
    ``gates_to_fold``. By default, all gates of the circuit are folded.

    References:
        [1] T. Giurgica-Tiron et al. (2020).
            Digital zero noise extrapolation for quantum error mitigation.
            `<https://ieeexplore.ieee.org/document/9259940>`
    """

    def __init__(
        self, gates_to_fold: Set[Union[str, int]] | int | str | None, barriers: bool = True
    ) -> None:
        self.gates_to_fold = self._validate_gates_to_fold(gates_to_fold)
        self.barriers = barriers

    ################################################################################
    ## INTERFACE IMPLEMENTATION
    ################################################################################
    def amplify_dag_noise(  # pylint: disable=arguments-differ
        self, dag: DAGCircuit, noise_factor: float
    ) -> DAGCircuit:
        num_foldings = self._compute_num_foldings(noise_factor)  # function for partial folding mask
        if not self.gates_to_fold:
            return dag
        noisy_dag = dag.copy_empty_like()
        for node in dag.topological_op_nodes():
            if node.name in self.gates_to_fold or node.op.num_qubits in self.gates_to_fold:
                noisy_dag = self._apply_folded_operation_back(noisy_dag, node, num_foldings)
            else:
                noisy_dag.apply_operation_back(node.op, qargs=node.qargs, cargs=node.cargs)
        return noisy_dag

    ################################################################################
    ## AUXILIARY
    ################################################################################
    def _apply_folded_operation_back(
        self,
        dag: DAGCircuit,
        node: DAGOpNode,
        num_foldings: int,
    ) -> DAGCircuit:
        """Folds each gate of original DAG circuit a number of ``num_foldings`` times.

        Args:
            dag: The original dag circuit without foldings.
            num_foldings: Number of times the circuit should be folded.

        Returns:
            DAGCircuit: The noise amplified DAG circuit.
        """
        original_op = node.op
        inverted_op = original_op.inverse()
        if self.barriers:
            barrier = Barrier(original_op.num_qubits)
            dag.apply_operation_back(barrier, qargs=node.qargs)
        self._apply_operation_back(dag, original_op, node.qargs, node.cargs)
        for _ in range(num_foldings):
            self._apply_operation_back(dag, inverted_op, node.qargs, node.cargs)
            self._apply_operation_back(dag, original_op, node.qargs, node.cargs)
        return dag

    def _apply_operation_back(
        self,
        dag: DAGCircuit,
        dag_op: Operation,
        qargs: Tuple = (),
        cargs: Tuple = (),
    ) -> DAGCircuit:
        dag.apply_operation_back(dag_op, qargs, cargs)
        if self.barriers:
            barrier = Barrier(dag_op.num_qubits)
            dag.apply_operation_back(barrier, qargs)
        return dag

    ################################################################################
    ## VALIDATION
    ################################################################################
    def _validate_gates_to_fold(
        self, gates_to_fold: Set[Union[str, int]] | int | str | None
    ) -> set[int | str]:
        """Validates if gates_to_fold is valid.

        Args:
            gates_to_fold: Original gates_to_fold input.
        """
        if gates_to_fold is None:
            return set()
        if isinstance(gates_to_fold, (int, str)):
            gates_to_fold = {gates_to_fold}
        VALID_GATES = set(  # pylint: disable=invalid-name
            standard_gates.get_standard_gate_name_mapping().keys()
        )
        for value in gates_to_fold:
            bad_int = isinstance(value, int) and value <= 0
            bad_str = isinstance(value, str) and value not in VALID_GATES
            if bad_int or bad_str:
                raise ValueError(f"{value!r} not a valid gate to fold option.")
        return set(gates_to_fold)
