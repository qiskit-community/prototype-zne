# Reference guide

This guide is for those who just want to use the package. If you want to extend the module or documentation, read [this other guide](/CONTRIBUTING.md) instead. See here for [installation instructions](/INSTALL.md).


## Table of contents

1. [Technique](#technique)
    - [Overview](#overview)
    - [Procedure](#procedure)
    - [Beyond](#beyond)
2. [Using the module](#using-the-module)
    - [Compatibility](#compatibility)
    - [ZNE configuration](#zne-configuration)
    - [ZNE metadata](#zne-metadata)
    - [Custom ZNE strategies](#custom-zne-strategies)
3. [Current limitations](#current-limitations)
    - [Noise Amplification](#noise-amplification)
    - [Max experiments](#max-experiments)
    - [Measurement gates](#measurement-gates)
4. [Troubleshooting](#troubleshooting)


## Technique

### Overview

### Procedure

### Beyond


## Using the module

This module works by injecting _zero noise extrapolation_ (ZNE) capabilities in any given implementation of the _Estimator_ primitive (i.e. implementing the official `BaseEstimator` interface from Qiskit). Once this functionality is in place, it can be controlled through a `ZNEStrategy` object that encapsulates all necessary information for customizing the error mitigation process. Therefore, by design, the resulting `ZNEEstimator` is used in an identical way as the one it is based on, except for declaring the ZNE configuration options.

For an introduction and instructions to the _Estimator_ primitive, refer to the [this tutorial](/docs/tutorials/0-estimator.ipynb). For information on how to use it on real quantum hardware visit the[Qiskit IBM Runtime documentation](https://qiskit.org/documentation/partners/qiskit_ibm_runtime/) and the [Qiskit IBM Runtime repo](https://github.com/Qiskit/qiskit-ibm-runtime) on GitHub. Other demo [tutorials](/docs/tutorials) are also available in the present repo.

For a more detailed, hands-on, explanation of the functionalities in this module consult [this tutorial](./tutorials/1-zne.ipynb).

### Compatibility
To inject the ZNE functionality into a pre-existing `Estimator` class following the official _Estimator_ specification (i.e. Qiskit's `BaseEstimator`), simply do the following:
```python
from zne import zne

ZNEEstimator = zne(Estimator)
estimator = ZNEEstimator(...)  # Same args as `Estimator`
```

Notice, however, that error mitigation techniques only make sense in the context of noisy computations; therefore using ZNE on noisless platforms (e.g. simulators), although technically possible, will not produce better results.

If no ZNE config options are provided (i.e. `zne_strategy`), the `ZNEEstimator` class behaves exactly like its parent `Estimator` class.

### ZNE configuration
In order to perform ZNE error mitigation, we simply declare its configuration options through a `ZNEStrategy` object, and pass it along to the `ZNEEstimator` during instantiation:
```python
from zne import ZNEStrategy
from zne.extrapolation import LinearExtrapolator
from zne.noise_amplification import CxAmplifier

zne_strategy = ZNEStrategy(
    noise_amplifier=CxAmplifier(),
    noise_factors=(1, 3, 5),
    extrapolator=LinearExtrapolator(),
)

# For some `circuit` and `observable`
job = estimator.run(circuit, observable, zne_strategy=zne_strategy)
result = job.result()
```
where the `noise_amplifier` strategy is an object in charge of performing noise amplification on the input circuits according to the provided `noise_factors`; and the `extrapolator` strategy is another object used for extrapolating the noisy results to the zero noise limit. For more information on these, check out our guide on how to [configure ZNE](./tutorials/1-zne.ipynb).

This package also provides libraries of pre-programmed [extrapolators](/zne/extrapolation) and [noise amplifiers](/zne/noise_amplification) which can be conveniently retrieved in dictionary form as showcased below. For more information, inspect the relevant modules (linked).
```python
from zne import EXTRAPOLATOR_LIBRARY, NOISE_AMPLIFIER_LIBRARY
```

### ZNE metadata
If ZNE error mitigation is performed, the `ZNEEstimator` object will add relevant information about the ZNE process to the returned `EstimatorResult` metadata field. Note that `result.values` now contains the mitigated (i.e. zero noise extrapolated) expectation values. The measured expectation values at different noise factor values that have been used for the extrapolation are instead stored in `result.metadata[0]['zne']['noise_amplification']['values']`. For example:
```
EstimatorResult: {
  "values": [
    0.9265950520833337
  ],
  "metadata": [
    {
      "zne": {
        "noise_amplification": {
          "noise_amplifier": "<CxAmplifier:{'noise_factor_relative_tolerance': 0.01, 'random_seed': None, 'sub_folding_option': 'from_first'}>",
          "noise_factors": [
            1,
            3,
            5
          ],
          "values": [
            0.89453125,
            0.822265625,
            0.759765625
          ],
          "variance": [
            0.1998138427734375,
            0.3238792419433594,
            0.4227561950683594
          ],
          "shots": [
            1024,
            1024,
            1024
          ]
        },
        "extrapolation": {
          "extrapolator": "LinearExtrapolator"
        }
      }
    }
  ]
}
```

### Custom ZNE strategies
This prototype has been devised specifically to allow users to create their custom noise amplification and extrapolation techniques. This can be easily done through custom implementations of the `NoiseAmplifier` and `Extrapolator` abstract classes respectively:
```python
from zne.extrapolation import Extrapolator, ReckoningResult
from zne.noise_amplification import NoiseAmplifier


############################  NOISE AMPLIFIER  ############################
class CustomAmplifier(NoiseAmplifier):
    def amplify_circuit_noise(self, circuit, noise_factor):
        return circuit.copy()  # Dummy, nonperforming

    def amplify_dag_noise(self, dag, noise_factor):
      return super().amplify_dag_noise(dag, noise_factor)


############################  EXTRAPOLATOR  ############################
class CustomExtrapolator(Extrapolator):
    @property
    def min_points(self):
        return 2
    
    def _extrapolate_zero(self, x_data, y_data, sigma_x, sigma_y):
        value = 1.0
        std_error = 1.0
        metadata = {"meta": "data"}
        return ReckoningResult(value, std_error, metadata)  # Dummy, nonperforming
```
where we only need to implement a number of (performing) methods with the appropriate [function signature](https://stackoverflow.com/a/72789014/12942875):
- __[NoiseAmplifier]__ Amplify circuit noise:
    ```python
    @abstractmethod
    def amplify_circuit_noise(self, circuit: QuantumCircuit, noise_factor: float) -> QuantumCircuit:
        """Noise amplification strategy.

        Args:
            circuit: The original circuit.
            noise_factor: The noise amplification factor by which to amplify the circuit noise.

        Returns:
            The noise amplified circuit
        """
    ```
- __[NoiseAmplifier]__ Amplify circuit noise:
    ```python
    def amplify_dag_noise(self, dag: DAGCircuit, noise_factor: float) -> DAGCircuit:
        """Noise amplification strategy over :class:`~qiskit.dagcircuit.DAGCircuit`.

        Args:
            dag: The original dag circuit.
            noise_factor: The noise amplification factor by which to amplify the circuit noise.

        Returns:
            The noise amplified dag circuit
        """
    ```
- __[Extrapolator]__ Minimum data points necessary for extrapolation:
    ```python
    @property
    @abstractmethod
    def min_points(self) -> int:
        """The minimum number of points required for extrapolation."""
    ```
- __[Extrapolator]__ Extrapolate to zero:
    ```python
    @abstractmethod
    def _extrapolate_zero(
        self,
        x_data: ndarray[Any, dtype], 
        y_data: ndarray[Any, dtype], 
        sigma_x: ndarray[Any, dtype],
        sigma_y: ndarray[Any, dtype],
    ) -> ReckoningResult:
        """Extrapolate to zero by fitting a regression model to the provided data.

        Args:
            x_data: A sequence of X values for the data points to fit.
            y_data: A sequence of Y values for the data points to fit.
            sigma_x: A sequence of std errors along the X axis for the data points to fit.
                If `None`, ones of `x_data` size is assumed.
            sigma_y: A sequence of std errors along the Y axis for the data points to fit.
                If `None`, ones of `y_data` size is assumed.

        Returns:
            A ReckoningResult object with the extrapolated value, std error, and metadata.
        """
    ```

If only one of `NoiseAmplifier.amplify_circuit_noise` or `NoiseAmplifier.amplify_dag_noise`
is implemented, delegating the implementation of the other to the parent class 
(i.e. `super()`) will default to executing the first with the appropriate type conversion.

Finally, we simply pass instances of these to the constructor through the `ZNEStrategy` object:
```python
zne_strategy = ZNEStrategy(
    noise_amplifier=CustomAmplifier(),
    noise_factors=(1, 3),
    extrapolator=CustomExtrapolator(),
)
```

Notice that the `CustomAmplifier` and `CustomExtrapolator` classes can be as complex as the model developer wants to make them (e.g. custom `__init__`) as long as they provide a valid implementation of the above mentioned abstract methods.


## Current limitations

### Noise Amplification and transpilation
Currently, noise amplification is performed before [transpilation](https://qiskit.org/documentation/apidoc/transpiler.html); which means that, generally speaking, the error is going to be over-amplified with respect to what could in theory be achieved by performing the noise amplification after optimizing the gates for the target architecture, and logical quantum state.

In a future release, noise amplification will be performed after transpilation by default, such that all base instructions in the circuit are folded by the correct amount whenever the noise factor is not an odd integer. However, there might be use cases where noise amplification before transpilation is preferred. For example, one might want to locally fold a user-defined instruction that consists of several basis gates (e.g. a Pauli twirling sequence). In these cases, one should specify that noise amplification needs to be performed before transpilation.

When randomly sub-folding (i.e. partial-folding) gates in global folding, these gates may simplify more than what we aimed at with the selected noise factor, leading to inaccuracies in the noise amplification process. Similarly, they may simplify less, meaning that the original and inverse circuits simplify more than the partial folding, hence leading to an over-representation of the noise.

There are three solutions for this:

1. Inserting gates everywhere to avoid any simplification whatsoever. This is avoided as it would prevent gate simplification altogether, raising the baseline noise, reaching noise saturation earlier, and decreasing the effectiveness of the entire mitigation process.
2. Making a randomness assumption and stating that, _on average_, the simplification on the partial and full foldings will be roughly the same quantitatively.
3. Performing noise amplification after the simplification (i.e. optimization) process in the transpilation pipeline.

### Non-exact noise factors
Certain noise amplifiers cannot reach the exact noise factors requested by the user, and will approximate them the best they can. If this approximation is not good enough (according to a tunable tolerance), a warning will be raised. Extrapolation though, will be performed based on the requested noise factors, instead of the approximated ones, which might result in inaccuracies. As of the current implementation, there is no way to retrieve the actual noise factors.

### Un-uniform noise distributed across gates
When amplifying the circuit noise by non odd integer noise factors, a subpart of the original circuit is folded one additional time. In some cases this can lead to jumps in the expectation value curve. These discontinuities can happen whenever the noise contribution is not uniformly distributed among all gates of the circuit. To remedy this behavior we suggest folding only the two-qubit gates which are considerably more noisy than single-qubit gates. However, even with this restriction, jumps can still be observed in certain cases and it is still an open question how and when these discontinuities arise.

### Measurement gates
If operators other than the Pauli-Z operator have to be measured as part of the expectation value computation, additional gates such as the Hadarmard or S gate are appended to the circuit. These measurement gates are currently not amplified by the ZNE estimator. However, single-qubit gates will in general only have a minor contribution to the overall noise introduced by the circuit, i.e., two-qubit gate errors will likely dominate. Therefore, this should not pose an issue for the performance of ZNE.

### Random sub-folding
Note that when performing random sub-folding, only one random realization of the sub-folding is selected and used for the expectation value computation. Averaging the expectation value over many random sub-folding realizations is currently not supported.

### Max experiments
The way ZNE is performed is by building several equivalent quantum circuits (i.e. representing the same logical quantum state) representing different noise factors, and obtaining the corresponding expectation value for each of those corresponding noisy states. After that, the zero noise expectation value is extrapolated from the noisy results.

This means that, for `n` noise factors and `m` circuit-observable combinations, the total number of experiments submitted for computation will be `n * m`; and therefore, the max number of experiments that we will be able to compute will be cut down by a factor of `n` from what the parent class allows.


## Troubleshooting

If you run into problems while using this package, we encourage a careful reading of the error messages first. Efforts have been made to make this messages as descriptive and helpful as possible; nonetheless, if still unable to solve the problem, you are welcome to [open an issue](https://github.com/qiskit-community/prototype-zne/issues) on the GitHub repository. When doing so, please provide a detailed explanation of what is happening and what needs to be done to reproduce the faulty behavior.
