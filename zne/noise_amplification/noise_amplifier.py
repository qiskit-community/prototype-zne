# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Interface for noise amplification strategies."""

from abc import ABC, abstractmethod

from qiskit.circuit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler import PassManager, TransformationPass

from ..immutable_strategy import ImmutableStrategy


class NoiseAmplifier(ImmutableStrategy, ABC):
    """Interface for noise amplification strategies."""

    @abstractmethod
    def amplify_circuit_noise(self, circuit: QuantumCircuit, noise_factor: float) -> QuantumCircuit:
        """Noise amplification strategy over :class:`~qiskit.circuit.QuantumCircuit`.

        Args:
            circuit: The original quantum circuit.
            noise_factor: The noise amplification factor by which to amplify the circuit noise.

        Returns:
            The noise amplified quantum circuit
        """

    @abstractmethod
    def amplify_dag_noise(self, dag: DAGCircuit, noise_factor: float) -> DAGCircuit:
        """Noise amplification strategy over :class:`~qiskit.dagcircuit.DAGCircuit`.

        Args:
            dag: The original dag circuit.
            noise_factor: The noise amplification factor by which to amplify the circuit noise.

        Returns:
            The noise amplified dag circuit
        """

    def build_transpiler_pass(self, noise_factor: float) -> TransformationPass:
        """Builds transpiler pass to perform noise amplification as specified in the strategy.

        Args:
            noise_factor: The noise factor used to amplify circuit noise.

        Returns:
            NoiseAmplificationPass: Instance of TransformationPass.
        """

        class NoiseAmplificationPass(TransformationPass):
            """Noise amplification transpiler pass."""

            def __init__(self, noise_amplifier: NoiseAmplifier) -> None:
                super().__init__()
                self._noise_amplifier: NoiseAmplifier = noise_amplifier

            @property
            def noise_amplifier(self) -> NoiseAmplifier:
                """Underlying noise amplifier."""
                return self._noise_amplifier

            def run(self, dag: DAGCircuit) -> DAGCircuit:
                return self.noise_amplifier.amplify_dag_noise(dag, noise_factor)

        return NoiseAmplificationPass(noise_amplifier=self)

    def build_pass_manager(self, noise_factor: float) -> PassManager:
        """Builds a pass manager holding a single transpiler pass for noise amplification.

        Args:
            noise_factor: The noise factor used to amplify circuit noise.

        Returns:
            PassManager: Wrapper for :class:`NoiseAmplificationPass`.
        """
        transpiler_pass: TransformationPass = self.build_transpiler_pass(noise_factor)
        return PassManager(transpiler_pass)


class CircuitNoiseAmplifier(NoiseAmplifier):
    """Interface for noise amplification strategies over :class:`~qiskit.dagcircuit.DAGCircuit`."""

    def amplify_dag_noise(self, dag: DAGCircuit, noise_factor: float) -> DAGCircuit:
        circuit: QuantumCircuit = dag_to_circuit(dag)
        circuit = self.amplify_circuit_noise(circuit, noise_factor)
        return circuit_to_dag(circuit)


class DAGNoiseAmplifier(NoiseAmplifier):
    """Interface for noise amplification strategies over :class:`~qiskit.dagcircuit.DAGCircuit`."""

    def amplify_circuit_noise(
        self, circuit: QuantumCircuit, noise_factor: float
    ) -> QuantumCircuit:  # pragma: no cover
        dag: DAGCircuit = circuit_to_dag(circuit)
        dag = self.amplify_dag_noise(dag, noise_factor)
        return dag_to_circuit(dag)
