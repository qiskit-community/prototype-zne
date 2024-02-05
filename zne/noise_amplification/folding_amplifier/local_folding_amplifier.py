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

"""Noise amplification strategy via gate/inverse repetition."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from qiskit.circuit import CircuitInstruction, QuantumCircuit

from ...utils import STANDARD_GATES
from ...utils.docstrings import insert_into_docstring
from .folding_amplifier import FoldingAmplifier


################################################################################
## GENERAL
################################################################################
class LocalFoldingAmplifier(FoldingAmplifier):
    """
    Replaces gates in the circuit by said gate and its inverse alternatingly as many times as
    indicated by noise_factor. The gates that should be folded can be specified by
    ``gates_to_fold``. By default, all gates of the circuit are folded.

    If ``noise_factor`` is not an odd integer, a subset of gates of the full circule are sub-folded
    such that the resultant noise scaling :math:`\\lambda` equals :math:`\\lambda=(2n+1)+2s/d`,
    where :math:`d` are the number of layers of the original circuit, :math:`n` is the number of
    gate foldings, and :math:`s` is the number of gates that are sub-folded [1].

    The gates of the full circuit that are sub-folded can be the first :math:`s` gates, the last
    :math:`s` gates or a random selection of :math:`s` gates. This is specified by
    ``sub_folding_option``.

    Note that all instance objects and their attributes are immutable by construction. If another
    strategy with different options needs to be utilized, a new instance of the class should be
    created.

    References:
        [1] T. Giurgica-Tiron et al. (2020).
            Digital zero noise extrapolation for quantum error mitigation.
            `<https://ieeexplore.ieee.org/document/9259940>`
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        gates_to_fold: Sequence[int | str] | str | int | None = None,
        sub_folding_option: str = "from_first",
        barriers: bool = True,
        random_seed: int | None = None,
        noise_factor_relative_tolerance: float = 1e-2,
        warn_user: bool = True,
    ) -> None:
        self.warn_user: bool = warn_user
        self._set_gates_to_fold(gates_to_fold)  # TODO move to super eventually
        super().__init__(
            sub_folding_option=sub_folding_option,
            barriers=barriers,
            random_seed=random_seed,
            noise_factor_relative_tolerance=noise_factor_relative_tolerance,
            warn_user=warn_user,
        )

    # TODO: remove `insert_into_docstring`
    __init__.__doc__ = insert_into_docstring(
        FoldingAmplifier.__init__.__doc__,
        [
            (
                "Args",
                "gates_to_fold: Specifies which gates of the full circuit are folded. It \n"
                "can be an int (referring to all n-qubit gates), a str with the name of a \n"
                "gate, or a sequence of int/str. In the latter case the union of all specified \n"
                "gates will be folded.",
            ),
        ],
    )

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def gates_to_fold(self) -> frozenset[int | str] | None:
        """Set of gates that are folded.

        Specifies which gates of the full circuit are folded. By default (i.e. ``None``) all gates
        are folded). Otherwise, ``gates_to_fold`` is a sequence of strings and/or integers where
        each string indicates the name of a gate to be folded and an integer n indicates that all
        n-qubit gates should be folded. For example, (2, "h", "x") would specify that the union,
        i.e., all two-qubit gates, the hadamard gate, and the x-gate will be noise amplified.
        """
        return self._gates_to_fold

    def _set_gates_to_fold(self, gates_to_fold: Sequence[int | str] | str | int | None) -> None:
        self._gates_to_fold: frozenset[int | str] | None = self._parse_gates_to_fold(gates_to_fold)

    def _parse_gates_to_fold(
        self, gates_to_fold: Sequence[int | str] | str | int | None
    ) -> frozenset[int | str] | None:
        """Parse to immutable set.

        Args:
            gates_to_fold: Set of gates that are folded.

        Raises:
            TypeError: If gates_to_fold is neither None, int, str, or an iterable.
        """
        if gates_to_fold is None:
            return gates_to_fold
        if isinstance(gates_to_fold, (int, str)):
            gates_to_fold_set: frozenset[int | str] = frozenset((gates_to_fold,))
        elif isinstance(gates_to_fold, Iterable):
            gates_to_fold_set = frozenset(gates_to_fold)
        else:
            raise TypeError(
                f"Expected int, str, or Iterable, received {type(gates_to_fold)} instead."
            )
        self._validate_gates_to_fold(gates_to_fold_set)
        return gates_to_fold_set

    def _validate_gates_to_fold(self, gates_to_fold: frozenset[int | str]) -> None:
        """Validates gates_to_fold set.

        Args:
            gates_to_fold: Set of gates that are folded.

        Raises:
            TypeError: If gates_to_fold contains objects that are neither int nor str.
            ValueError: If gates_to_fold contains integers smaller than one.
        """
        if not all(isinstance(g, (int, str)) for g in gates_to_fold):
            raise TypeError(
                f"Expected Iterable[str | int], received {type(gates_to_fold)} instead."
            )
        for gate in gates_to_fold:
            if isinstance(gate, int) and gate < 1:
                raise ValueError(f"gates_to_fold contains {gate} which is smaller than one.")
            if isinstance(gate, str) and gate not in STANDARD_GATES:
                self.warn(f"gates_to_fold contains {gate} which is not a standard gate name.")

    ################################################################################
    ## INTERFACE
    ################################################################################
    def amplify_circuit_noise(self, circuit: QuantumCircuit, noise_factor: float) -> QuantumCircuit:
        self._validate_noise_factor(noise_factor)
        foldings: list[int] = self._build_foldings_per_gate(circuit, noise_factor)
        noisy_circuit = circuit.copy_empty_like()
        for operation, num_foldings in zip(circuit, foldings):
            if num_foldings == 0:
                noisy_circuit.append(*operation)
            else:
                noisy_circuit = self._append_folded(noisy_circuit, operation, num_foldings)
        return noisy_circuit

    def _build_foldings_per_gate(self, circuit: QuantumCircuit, noise_factor: float) -> list[int]:
        """Returns number of foldings for each gate in the circuit.

        Args:
            circuit: The original circuit.
            noise_factor: The (float) noise amplification factor by which to amplify the overall
            circuit noise.

        Returns:
            List of (int) number of foldings for each gate in the circuit.
        """
        gates_to_fold_mask = [self._check_gate_folds(operation) for operation in circuit.data]
        num_gates_to_fold: int = gates_to_fold_mask.count(True)
        foldings = self._build_foldings(noise_factor, num_gates_to_fold)
        return [foldings.pop(0) if m else 0 for m in gates_to_fold_mask]

    def _check_gate_folds(self, operation: CircuitInstruction) -> bool:
        """Checks whether circuit operation should be folded.

        Args:
            operation: A single circuit instruction of the original circuit.

        Returns:
            True if instruction should be folded, False otherwise.
        """
        instruction, qargs, _ = operation
        if instruction.name in {"barrier", "measure"}:
            return False
        num_qubits = len(qargs)
        return (
            (self._gates_to_fold is None)
            or (num_qubits in self._gates_to_fold)
            or (instruction.name in self._gates_to_fold)
        )

    def _build_foldings(self, noise_factor: float, num_gates_to_fold: int) -> list[int]:
        """Returns number of foldings for each gate to fold.

        Args:
            noise_factor: The (float) noise amplification factor by which to amplify the overall
            circuit noise.
            num_gates_to_fold: The total number of gates to fold.

        Returns:
            List of (int | None) number of foldings for each gate to fold.
        """
        num_full_foldings, num_sub_foldings = self._compute_folding_nums(
            noise_factor, num_gates_to_fold
        )
        sub_foldings: list[int] = self._build_sub_foldings(num_sub_foldings, num_gates_to_fold)
        return [num_full_foldings + sf for sf in sub_foldings]

    def _build_sub_foldings(self, num_sub_foldings: int, num_gates_to_fold: int) -> list[int]:
        """Returns sub-foldings for each gate to fold.

        Args:
            num_sub_foldings: Number of gates to be sub-folded.
            num_gates_to_fold: The number of instructions to fold.

        Returns:
            List of number of sub-foldings for each folded gate.
        """
        if num_sub_foldings == 0:
            return [0] * num_gates_to_fold
        if self.sub_folding_option == "from_first":
            return [1] * num_sub_foldings + [0] * (num_gates_to_fold - num_sub_foldings)
        if self.sub_folding_option == "from_last":
            return [0] * (num_gates_to_fold - num_sub_foldings) + [1] * num_sub_foldings
        idxs = self._rng.choice(num_gates_to_fold, size=num_sub_foldings, replace=False)
        return [1 if i in idxs else 0 for i in range(num_gates_to_fold)]

    def _append_folded(
        self, noisy_circuit: QuantumCircuit, operation: CircuitInstruction, num_foldings: int
    ) -> QuantumCircuit:
        """Folds circuit operation.

        Args:
            noisy_circuit: The noise amplified circuit to which the gate foldings are added.
            operation: A single operation of the original circuit to be folded.
            noise_factor: The corresponding noise factor.

        Returns:
            The updated noisy circuit.
        """
        # TODO: Create FoldableCircuit class extending QuantumCircuit
        # TODO: CircuitInstruction.inverse()
        self._validate_num_foldings(num_foldings)
        instruction, qargs, cargs = operation
        noisy_circuit = self._apply_barrier(noisy_circuit, qargs)
        noisy_circuit.append(instruction, qargs, cargs)
        if num_foldings > 0:
            noisy_circuit = self._apply_barrier(noisy_circuit, qargs)
            noisy_circuit.append(instruction.inverse(), qargs, cargs)
            return self._append_folded(noisy_circuit, operation, num_foldings - 1)
        noisy_circuit = self._apply_barrier(noisy_circuit, qargs)
        return noisy_circuit

    @staticmethod
    def _validate_num_foldings(num_foldings: int) -> None:
        """Validate num_foldings.

        Args:
            num_foldings: number of foldings.

        Raises:
            TypeError: If num_foldings is not int.
            ValueError: If num_foldings is negative.
        """
        if not isinstance(num_foldings, int):
            raise TypeError(f"Expected int, received {type(num_foldings)} instead.")
        if num_foldings < 0:
            raise ValueError("Number of foldings must be greater than or equal to zero.")


################################################################################
## FACADES
################################################################################
class CxAmplifier(LocalFoldingAmplifier):
    """
    Digital noise amplifier acting on CX gates exclusively.

    Replaces each CX gate locally with as many CX gates as indicated by the noise_factor.
    """

    def __init__(  # pylint: disable=too-many-arguments,duplicate-code
        self,
        sub_folding_option: str = "from_first",
        barriers: bool = True,
        random_seed: int | None = None,
        noise_factor_relative_tolerance: float = 1e-2,
        warn_user: bool = True,
    ) -> None:
        super().__init__(
            gates_to_fold="cx",
            sub_folding_option=sub_folding_option,
            barriers=barriers,
            random_seed=random_seed,
            noise_factor_relative_tolerance=noise_factor_relative_tolerance,
            warn_user=warn_user,
        )


class TwoQubitAmplifier(LocalFoldingAmplifier):
    """
    Digital noise amplifier acting on two-qubit gates exclusively.

    Replaces each two-qubit gate locally with as many gates as indicated by the noise_factor.
    """

    def __init__(  # pylint: disable=too-many-arguments,duplicate-code
        self,
        sub_folding_option: str = "from_first",
        barriers: bool = True,
        random_seed: int | None = None,
        noise_factor_relative_tolerance: float = 1e-2,
        warn_user: bool = True,
    ) -> None:
        super().__init__(
            gates_to_fold=2,
            sub_folding_option=sub_folding_option,
            barriers=barriers,
            random_seed=random_seed,
            noise_factor_relative_tolerance=noise_factor_relative_tolerance,
            warn_user=warn_user,
        )


class MultiQubitAmplifier(LocalFoldingAmplifier):
    """
    Digital noise amplifier acting on multi-qubit gates exclusively.

    Replaces each multi-qubit gate locally with as many gates as indicated by the noise_factor.
    """

    def __init__(  # pylint: disable=too-many-arguments,duplicate-code
        self,
        sub_folding_option: str = "from_first",
        barriers: bool = True,
        random_seed: int | None = None,
        noise_factor_relative_tolerance: float = 1e-2,
        warn_user: bool = True,
    ) -> None:
        super().__init__(
            gates_to_fold=None,
            sub_folding_option=sub_folding_option,
            barriers=barriers,
            random_seed=random_seed,
            noise_factor_relative_tolerance=noise_factor_relative_tolerance,
            warn_user=warn_user,
        )

    def _check_gate_folds(self, operation: CircuitInstruction) -> bool:
        instruction, qargs, _ = operation
        if instruction.name in {"barrier", "measure"}:
            return False
        num_qubits = len(qargs)
        return num_qubits > 1
