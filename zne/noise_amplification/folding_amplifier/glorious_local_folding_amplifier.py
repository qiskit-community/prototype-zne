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
from typing import Union

from qiskit.circuit.library import standard_gates
from qiskit.dagcircuit import DAGCircuit

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

    def __init__(self, gates_to_fold: Set[Union[str, int] | None], barriers: bool = True) -> None:
        self.gates_to_fold = self._validate_gates_to_fold(gates_to_fold)
        self._set_barriers(barriers)

    ################################################################################
    # ## PROPERTIES
    ################################################################################
    @property  # pylint:disable-next=duplicate-code
    def barriers(self) -> bool:
        """Barriers setter"""
        return self._barriers

    def _set_barriers(self, barriers: bool) -> None:
        """Set barriers property"""
        self._barriers = bool(barriers)

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
        noisy_dag = dag.copy()
        for node, num in zip(dag.topological_op_nodes(), num_foldings):
            noisy_dag = self._apply_folded_operation_back(noisy_dag, node, num)
        return noisy_dag

    ################################################################################
    # AUXILIARY
    ################################################################################

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

    ################################################################################
    # VALIDATION
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
