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

from .glorious_folding_amplifier import Folding, GloriousFoldingAmplifier


class GloriousLocalFoldingAmplifier(GloriousFoldingAmplifier):
    """Amplifies noise in the circuit by said gate and its inverse alternatingly as many times as
    indicated by noise_factor. The gates that should be folded can be specified by
    ``gates_to_fold``. By default, all gates of the circuit are folded.

    References:
        [1] T. Giurgica-Tiron et al. (2020).
            Digital zero noise extrapolation for quantum error mitigation.
            `<https://ieeexplore.ieee.org/document/9259940>`
    """

    def __init__(self, gates_to_fold: Set[Union[str, int]], barriers: bool = True) -> None:
        self.gates_to_fold = self._validate_gates_to_fold(gates_to_fold)
        self.barriers = barriers

    ################################################################################
    ## INTERFACE IMPLEMENTATION
    ################################################################################
    def amplify_dag_noise(  # pylint: disable=arguments-differ
        self, dag: DAGCircuit, noise_factor: float
    ) -> DAGCircuit:
        if not self.gates_to_fold:
            return dag
        # TODO: find number of nodes
        num_foldable_nodes = self._compute_foldable_nodes(dag, self.gates_to_fold)
        folding_nums = self._compute_folding_nums(noise_factor, num_foldable_nodes)
        num_foldings = self._compute_folding_mask(folding_nums, dag, self.gates_to_fold)
        noisy_dag = dag.copy_empty_like()
        for node, num in zip(dag.topological_op_nodes(), num_foldings):
            noisy_dag = self._apply_folded_operation_back(noisy_dag, node, num)
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
            node: The DAGOpNode to apply folded.
            num_foldings: Number of times the circuit should be folded.

        Returns:
            DAGCircuit: The noise amplified DAG circuit.
        """
        if num_foldings == 0:
            dag.apply_operation_back(node.op)
            return dag
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

    def _compute_foldable_nodes(self, dag: DAGCircuit, gates_to_fold: Set[Union[str, int]]) -> int:
        """Computes number of foldable gates from gates_to_fold supplied by user

        Args:
            dag: The original dag circuit without foldings.
            gates_to_fold: Set of gates to fold supplied by user

        Returns:
            int: Number of effective gates to fold
        """
        num_foldable_nodes = 0
        for node in dag.topological_op_nodes():
            if node.op.num_qubits in gates_to_fold:
                num_foldable_nodes += 1
            if node.name in gates_to_fold:
                num_foldable_nodes += 1
        return num_foldable_nodes

    def _compute_folding_mask(
        self,
        folding_nums: Folding,
        dag: DAGCircuit,
        gates_to_fold: Set[Union[str, int]],
    ) -> list:
        """Computes folding mask based on folding_nums and gates_to_fold

        Args:
            folding_nums: namedTuple with full foldings, partial gates and effective_noise_factor
            dag: The original dag circuit without foldings.
            gates_to_fold: Set of gates to fold supplied by user

        Returns:
            list: list mask with number of foldings per node
        """
        partial_folding_mask = []
        counter = folding_nums.partial
        for node in dag.topological_op_nodes():
            print(node.op)
            if node.name in gates_to_fold:
                if counter != 0:
                    partial_folding_mask.append(folding_nums.full + 1)
                    counter -= 1
                else:
                    partial_folding_mask.append(folding_nums.full)
            elif node.op.num_qubits in gates_to_fold and counter != 0:
                if counter != 0:
                    partial_folding_mask.append(folding_nums.full + 1)
                    counter -= 1
                else:
                    partial_folding_mask.append(folding_nums.full)
            else:
                partial_folding_mask.append(0)
        return partial_folding_mask

    ################################################################################
    ## VALIDATION
    ################################################################################
    def _validate_gates_to_fold(self, gates_to_fold: Set[Union[str, int]]) -> set[int | str]:
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
