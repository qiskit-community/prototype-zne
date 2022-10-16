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


from itertools import product
from unittest.mock import Mock, patch

from pytest import mark
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info.operators import Operator
from qiskit.transpiler import TransformationPass

from zne import NOISE_AMPLIFIER_LIBRARY
from zne.noise_amplification import CircuitNoiseAmplifier, DAGNoiseAmplifier


@mark.parametrize(
    "NoiseAmplifier",
    NOISE_AMPLIFIER_LIBRARY.values(),
    ids=NOISE_AMPLIFIER_LIBRARY.keys(),
)
class TestNoiseAmplifier:
    @mark.parametrize(
        "circuit, noise_factor",
        cases := tuple(
            product(
                [
                    random_circuit(5, 3, seed=0),
                    random_circuit(5, 3, seed=5),
                    random_circuit(5, 6, seed=66),
                    random_circuit(5, 6, seed=1081),
                ],
                [1, 3, 5],
            )
        ),
        ids=[f"{type(c).__name__}<{len(c)}>-{nf}" for c, nf in cases],
    )
    @mark.filterwarnings("ignore::UserWarning")
    def test_circuit_equivalence(self, NoiseAmplifier, circuit, noise_factor):
        noisy_circuit = NoiseAmplifier().amplify_circuit_noise(circuit.copy(), noise_factor)
        assert Operator(noisy_circuit).equiv(Operator(circuit))

    ################################################################################
    ## TESTS
    ################################################################################
    @mark.parametrize("noise_factor", [1, 1.2, 2.4, -3.14])
    def test_build_transpiler_pass(self, NoiseAmplifier, noise_factor):
        DAG = f"DAG:{noise_factor}"
        AMP_DAG = f"AMP_DAG:{noise_factor}"
        noise_amplifier = NoiseAmplifier()
        noise_amplifier.amplify_dag_noise = Mock(return_value=AMP_DAG)
        transpiler_pass = noise_amplifier.build_transpiler_pass(noise_factor)
        assert isinstance(transpiler_pass, TransformationPass)
        assert AMP_DAG == transpiler_pass.run(DAG)
        noise_amplifier.amplify_dag_noise.assert_called_once_with(DAG, noise_factor)

    @mark.parametrize("noise_factor", [1, 1.2, 2.4, -3.14])
    def test_build_pass_manager(self, NoiseAmplifier, noise_factor):
        target = "zne.noise_amplification.noise_amplifier"
        target_pass_builder = target + ".NoiseAmplifier.build_transpiler_pass"
        target_pass_manager_class = target + ".PassManager"
        TRANSPILER_PASS = f"<NoiseAmplificationPass:{noise_factor}>"
        with patch(target_pass_builder, return_value=TRANSPILER_PASS) as pass_builder, patch(
            target_pass_manager_class
        ) as pass_manager_class:
            _ = NoiseAmplifier().build_pass_manager(noise_factor)
        pass_builder.assert_called_once_with(noise_factor)
        pass_manager_class.assert_called_once_with(TRANSPILER_PASS)

    @mark.parametrize("noise_factor", [1, 1.2, 2.4, -3.14])
    def test_amplify_dag_noise(self, NoiseAmplifier, noise_factor):
        if issubclass(NoiseAmplifier, CircuitNoiseAmplifier):
            DAG = f"DAG:{noise_factor}"
            CIRCUIT = f"CIRCUIT:{noise_factor}"
            AMP_CIRCUIT = f"AMP_CIRCUIT:{noise_factor}"
            AMP_DAG = f"AMP_DAG:{noise_factor}"
            noise_amplifier = NoiseAmplifier()
            noise_amplifier.amplify_circuit_noise = Mock(return_value=AMP_CIRCUIT)
            target = "zne.noise_amplification.noise_amplifier"
            with patch(target + ".dag_to_circuit", return_value=CIRCUIT) as dag_to_circuit, patch(
                target + ".circuit_to_dag",
                return_value=AMP_DAG,
            ) as circuit_to_dag:
                assert AMP_DAG == noise_amplifier.amplify_dag_noise(DAG, noise_factor)
            dag_to_circuit.assert_called_once_with(DAG)
            noise_amplifier.amplify_circuit_noise.assert_called_once_with(CIRCUIT, noise_factor)
            circuit_to_dag.assert_called_once_with(AMP_CIRCUIT)

    @mark.parametrize("noise_factor", [1, 1.2, 2.4, -3.14])
    def test_amplify_circuit_noise(self, NoiseAmplifier, noise_factor):
        if issubclass(NoiseAmplifier, DAGNoiseAmplifier):
            CIRCUIT = f"CIRCUIT:{noise_factor}"
            DAG = f"DAG:{noise_factor}"
            AMP_DAG = f"AMP_DAG:{noise_factor}"
            AMP_CIRCUIT = f"AMP_CIRCUIT:{noise_factor}"
            noise_amplifier = NoiseAmplifier()
            noise_amplifier.amplify_dag_noise = Mock(return_value=AMP_DAG)
            target = "zne.noise_amplification.noise_amplifier"
            with patch(
                target + ".dag_to_circuit", return_value=AMP_CIRCUIT
            ) as dag_to_circuit, patch(
                target + ".circuit_to_dag",
                return_value=DAG,
            ) as circuit_to_dag:
                assert AMP_CIRCUIT == noise_amplifier.amplify_circuit_noise(CIRCUIT, noise_factor)
            circuit_to_dag.assert_called_once_with(CIRCUIT)
            noise_amplifier.amplify_dag_noise.assert_called_once_with(DAG, noise_factor)
            dag_to_circuit.assert_called_once_with(AMP_DAG)
