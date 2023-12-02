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

"""Noise amplification strategy via circuit/circuit-inverse repetition."""


from qiskit.circuit import QuantumCircuit

from .folding_amplifier import FoldingAmplifier


class GlobalFoldingAmplifier(FoldingAmplifier):
    """Alternatingly composes the circuit and its inverse as many times as indicated by the
    ``noise_factor``.

    If ``noise_factor`` is not an odd integer, a sub part of the full circle is folded such that the
    resultant noise scaling :math:`\\lambda` equals :math:`\\lambda=(2n+1)+2s/d`, where :math:`d`
    are the number of layers of the original circuit, :math:`n` is the number of global circuit
    foldings, and :math:`s` is the number of gates that are sub-folded [1].

    The gates of the full circuit that are used for the sub-folding can be the first :math:`s`
    gates, the last :math:`s` gates or a random selection of :math:`s` gates. This is specified by
    ``sub_folding_option``.

    Note that all instance objects and their attributes are immutable by construction. If another
    strategy with different options needs to be utilized, a new instance of the class should be
    created.

    References:
        [1] T. Giurgica-Tiron et al. (2020).
            Digital zero noise extrapolation for quantum error mitigation.
            `<https://ieeexplore.ieee.org/document/9259940>`
    """

    def amplify_circuit_noise(self, circuit: QuantumCircuit, noise_factor: float) -> QuantumCircuit:
        self._validate_noise_factor(noise_factor)
        num_full_foldings, num_sub_foldings = self._compute_folding_nums(noise_factor, len(circuit))
        noisy_circuit = circuit.copy_empty_like()
        noisy_circuit = self._apply_full_folding(noisy_circuit, circuit, num_full_foldings)
        noisy_circuit = self._apply_sub_folding(noisy_circuit, circuit, num_sub_foldings)
        return noisy_circuit

    def _apply_full_folding(
        self, noisy_circuit: QuantumCircuit, original_circuit: QuantumCircuit, num_foldings: int
    ) -> QuantumCircuit:
        """Fully folds the original circuit a number of ``num_foldings`` times.

        Args:
            noisy_circuit: The noise amplified circuit to which the gates are added.
            original_circuit: The original circuit without foldings.
            num_foldings: Number of times the circuit should be folded.

        Returns:
            The noise amplified circuit.
        """
        noise_factor: int = self.folding_to_noise_factor(num_foldings)  # type: ignore
        for i in range(noise_factor):
            if i % 2 == 0:
                noisy_circuit.compose(original_circuit, inplace=True)
            else:
                noisy_circuit.compose(original_circuit.inverse(), inplace=True)
            noisy_circuit = self._apply_barrier(noisy_circuit)
        return noisy_circuit

    def _apply_sub_folding(
        self, noisy_circuit: QuantumCircuit, original_circuit: QuantumCircuit, num_foldings: int
    ) -> QuantumCircuit:
        """Folds a subset of gates of the original circuit.

        Args:
            noisy_circuit: The noise amplified circuit to which the gates are added.
            original_circuit: The original circuit without foldings.
            num_foldings: Number of gates to be folded.

        Returns:
            The noise amplified circuit.
        """
        if num_foldings == 0:
            return noisy_circuit
        sub_circuit: QuantumCircuit = self._get_sub_folding(original_circuit, num_foldings)
        noisy_circuit.compose(sub_circuit.inverse(), inplace=True)
        noisy_circuit.compose(sub_circuit, inplace=True)
        return noisy_circuit

    def _get_sub_folding(self, circuit: QuantumCircuit, size: int) -> QuantumCircuit:
        """Returns sub circuit to be folded.

        Args:
            circuit: The original circuit without foldings.
            size: Number of gates to be sub-folded.

        Returns:
            The sub circuit.
        """
        sub_circuit = circuit.copy_empty_like()
        if self._sub_folding_option == "from_first":
            sub_data = circuit.data[:size]
        elif self._sub_folding_option == "from_last":
            sub_data = circuit.data[-size:]
        else:
            instruction_idxs = sorted(self._rng.choice(len(circuit), size=size, replace=False))
            sub_data = [circuit.data[i] for i in instruction_idxs]
        for instruction, qargs, cargs in sub_data:
            # sub_circuit.barrier(qargs)  # TODO: avoid sub-folded gates simplification
            sub_circuit.append(instruction, qargs, cargs)
        return sub_circuit
