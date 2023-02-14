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


from collections.abc import Sequence

from qiskit.circuit.library import Barrier, standard_gates
from qiskit.dagcircuit import DAGCircuit, DAGOpNode

from ..noise_amplifier import DAGNoiseAmplifier


class GloriousLocalFoldingAmplifier(DAGNoiseAmplifier):
    """Amplifies noise in the circuit by said gate and its inverse alternatingly as many times as
    indicated by noise_factor. The gates that should be folded can be specified by
    ``gates_to_fold``. By default, all gates of the circuit are folded.

    References:
        [1] T. Giurgica-Tiron et al. (2020).
            Digital zero noise extrapolation for quantum error mitigation.
            `<https://ieeexplore.ieee.org/document/9259940>`
    """

    def __init__(self, gates_to_fold: Sequence[int | str], barriers: bool = True) -> None:
        self.gates_to_fold = self._validate_gates_to_fold(gates_to_fold)
        self.barriers = barriers

    def amplify_dag_noise(  # pylint: disable=arguments-differ
        self, dag: DAGCircuit, noise_factor: float
    ) -> DAGCircuit:
        """Applies local folding to input DAGCircuit and returns amplified circuit"""
        num_full_foldings = self._compute_num_foldings(noise_factor)
        return self._apply_local_folding(dag, num_full_foldings, self.gates_to_fold)

    def _apply_local_folding(
        self,
        dag: DAGCircuit,
        num_foldings: int,
        gates_to_fold: Sequence[int | str] | None,
    ) -> DAGCircuit:
        """Applies local folding strategy and returns a noise amplified dag.

        Args:
            dag: The original dag circuit without foldings.
            num_foldings: Number of times the circuit should be folded.
            gates_to_fold: Original gates_to_fold input.

        Returns:
            DAGCircuit: The noise amplified DAG circuit.
        """
        if gates_to_fold in [0, "0", None]:
            return dag
        noisy_dag = dag.copy_empty_like()
        for node in dag.topological_op_nodes():
            if node.name in gates_to_fold or node.op.num_qubits in gates_to_fold:
                noisy_dag = self._apply_folded_operation_back(noisy_dag, node, num_foldings)
            else:
                noisy_dag.apply_operation_back(node.op, qargs=node.qargs, cargs=node.cargs)
        return noisy_dag

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
        if self.barriers:
            barrier = Barrier(node.op.num_qubits)
        dag.apply_operation_back(barrier, qargs=node.qargs)
        dag.apply_operation_back(node.op, qargs=node.qargs, cargs=node.cargs)
        inverted_node = node.op.inverse()
        for _ in range(num_foldings):
            if self.barriers:
                dag.apply_operation_back(barrier, qargs=node.qargs)
            dag.apply_operation_back(inverted_node, qargs=node.qargs, cargs=node.cargs)
            dag.apply_operation_back(barrier, qargs=node.qargs)
            if self.barriers:
                dag.apply_operation_back(node.op, qargs=node.qargs, cargs=node.cargs)
        dag.apply_operation_back(barrier, qargs=node.qargs)
        return dag

    def _compute_num_foldings(self, noise_factor: float) -> int:
        """Compute number of foldings.

        Args:
            noise_factor : The original noise_factor input.

        Returns:
            int: Number of foldings calculated from noise_factor.
        """
        noise_factor = self._validate_noise_factor(noise_factor)
        return int((noise_factor - 1) / 2)

    def _validate_gates_to_fold(
        self, gates_to_fold: Sequence[int | str] | int | str | None
    ) -> tuple[int | str, ...]:
        """Validates if gates_to_fold is valid.

        Args:
            gates_to_fold (Sequence[int | str] | None) : Original gates_to_fold input.
        """
        if gates_to_fold is None:
            return ()
        if isinstance(gates_to_fold, int):
            return (gates_to_fold,)
        if isinstance(gates_to_fold, str):
            gates_to_fold = (gates_to_fold,)
        VALID_GATES = set(  # pylint: disable=invalid-name
            standard_gates.get_standard_gate_name_mapping().keys()
        )
        for value in gates_to_fold:
            bad_int = isinstance(value, int) and value <= 0
            bad_str = isinstance(value, str) and value not in VALID_GATES
            if bad_int or bad_str:
                raise ValueError(f"{value!r} not a valid gate to fold option.")
        return tuple(gates_to_fold)

    # pylint: disable=duplicate-code

    def _validate_noise_factor(self, noise_factor: float) -> float:
        """Normalizes and validates noise factor.

        Args:
            noise_factor : The original noisefactor input.

        Returns:
            float: Normalised noisefactor input.

        Raises:
            ValueError: If input noise_factor value is not of type float.
            TypeError: If input noise_factor value is not of type float.
        """
        try:
            noise_factor = float(noise_factor)
        except ValueError:
            raise ValueError(  # pylint: disable=raise-missing-from
                f"Function call expects a positive floating value. "
                f"Received value of {noise_factor} instead."
            )
        except TypeError:
            raise TypeError(  # pylint: disable=raise-missing-from
                f"Function call expects a positive floating value. "
                f"Received value of {noise_factor} instead."
            )
        if noise_factor < 1:
            raise ValueError(  # pylint: disable=raise-missing-from
                f"Function call expects a positive float noise_factor >= 1."
                f"Received {noise_factor} instead."
            )
        if noise_factor % 2 == 0:
            raise ValueError(  # pylint: disable=raise-missing-from
                f"Function call expects a positive odd noise_factor. "
                f"Received {noise_factor} instead."
            )
        return noise_factor
