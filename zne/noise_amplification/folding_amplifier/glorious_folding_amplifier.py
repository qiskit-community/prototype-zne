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

"""Glorious Global Folding Noise Amplfiier (Temporary)"""

from collections import namedtuple
from collections.abc import Set
from math import ceil, floor
from typing import Tuple, Union

from numpy import isclose
from qiskit.circuit import Operation
from qiskit.circuit.library import Barrier
from qiskit.dagcircuit import DAGCircuit, DAGOpNode

from ..noise_amplifier import DAGNoiseAmplifier

Folding = namedtuple("Folding", ("full", "partial", "effective_noise_factor"))
# noise_factor = approximate noise_factor


class GloriousFoldingAmplifier(DAGNoiseAmplifier):
    """Interface for folding amplifier strategies."""

    def __init__(self, barriers: bool = True, tolerance: float = 0.05) -> None:
        self._set_barriers(barriers)
        self._set_tolerance(tolerance)

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

    @property
    def tolerance(self) -> float:
        """Tolerance setter"""
        return self._tolerance

    def _set_tolerance(self, tolerance: float) -> None:
        """Set Tolerance property"""
        self._tolerance = float(tolerance)

    ################################################################################
    # AUXILIARY
    ################################################################################
    def _compute_folding_nums(self, noise_factor: float, num_nodes: int) -> Folding:
        """Compute number of foldings.

        Args:
            noise_factor: The original noise_factor input.
            num_nodes: total number of foldable nodes for input DAG

        Returns:
            Folding: named tuple containing full foldings, number of gates to partially fold and
            effective noise factor of the operation
        """

        foldings = (noise_factor - 1) / 2
        full_foldings = int(foldings)
        partial_foldings = foldings - full_foldings

        gates_to_partial_fold = self._compute_best_estimated_gates(num_nodes, partial_foldings)

        effective_foldings = full_foldings + gates_to_partial_fold / num_nodes
        effective_noise_factor = 2 * effective_foldings + 1

        if isclose(effective_noise_factor, noise_factor, atol=self.tolerance, equal_nan=False):
            print("Warning!!!")
        print(
            "Folding with effective noise factor of",
            effective_noise_factor,
            "instead of",
            noise_factor,
            ". Effective folding accuracy:",
            effective_noise_factor / noise_factor * 100,
        )
        return Folding(full_foldings, gates_to_partial_fold, effective_noise_factor)

    def _compute_best_estimated_gates(self, num_nodes: float, partial_foldings: float) -> float:
        """Computes best estimates from possible candidates for number of partial folded gates

        Args:
            num_nodes: total number of foldable nodes for input DAG
            partial_foldings: Extra foldings required

        Returns:
            float: returns closest estimated number of gates required to be partially folded
            to achieve the user expected noise_factor
        """
        lower_estimate = floor(num_nodes * partial_foldings)
        lower_diff = abs(lower_estimate - partial_foldings)
        upper_estimate = ceil(num_nodes * partial_foldings)
        upper_diff = abs(upper_estimate - partial_foldings)
        if lower_diff < upper_diff:
            return lower_estimate
        return upper_estimate

    def _compute_folding_mask(
        self,
        folding_nums: Folding,
        dag: DAGCircuit,
        gates_to_fold: Set[Union[str, int] | None] = None,
    ) -> list:
        """Computes folding mask based on folding_nums and gates_to_fold

        Args:
            folding_nums: namedTuple with full foldings, partial gates and effective_noise_factor
            dag: The original dag circuit without foldings.
            gates_to_fold: Set of gates to fold supplied by user

        Returns:
            list: list mask for applying folding operation.
        """
        partial_folding_mask = []
        counter = folding_nums.partial
        if gates_to_fold is None:  # For global folding
            for node in dag.topological_op_nodes():
                if counter != 0:
                    partial_folding_mask.append(1)
                    counter -= 1
                else:
                    partial_folding_mask.append(0)
            return partial_folding_mask
        for node in dag.topological_op_nodes():  # For local folding
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

    def _validate_noise_factor(self, noise_factor: float) -> float:
        """Normalizes and validates noise factor.

        Args:
            noise_factor: The original noisefactor input.

        Returns:
            float: Normalised noise_factor input.

        Raises:
            ValueError: If input noise_factor value is not of type float.
            TypeError: If input noise_factor value is not of type float.
        """
        try:
            noise_factor = float(noise_factor)
        except ValueError:
            raise ValueError(  # pylint: disable=raise-missing-from
                f"Expected positive float value, received {noise_factor} instead."
            )
        except TypeError:
            raise TypeError(  # pylint: disable=raise-missing-from
                f"Expected positive float, received {type(noise_factor)} instead."
            )
        if noise_factor < 1:
            raise ValueError(
                f"Expected positive float noise_factor >= 1, received {noise_factor} instead."
            )
        return noise_factor
