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

"""Zero Noise Extrapolation (ZNE) strategy configuration dataclass."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from math import sqrt
from typing import Any
from warnings import warn

from numpy import array
from qiskit import QuantumCircuit
from qiskit.primitives import EstimatorResult

from .extrapolation import Extrapolator, LinearExtrapolator
from .noise_amplification import MultiQubitAmplifier, NoiseAmplifier
from .types import EstimatorResultData, Metadata  # noqa: F401
from .utils.grouping import from_common_key, group_elements_gen, merge_dicts
from .utils.typing import isreal, normalize_array
from .utils.validation import quality


class ZNEStrategy:
    """Zero Noise Extrapolation strategy.

    Args:
        noise_factors: An list of real valued noise factors that determine by what amount the
            circuits' noise is amplified.
        noise_amplifier: A noise amplification strategy implementing the :class:`NoiseAmplifier`
            interface. A dictionary of currently available options can be imported as
            ``NOISE_AMPLIFIER_LIBRARY``.
        extrapolator: An extrapolation strategy implementing the :class:`Extrapolator`
            interface. A dictionary of currently available options can be imported as
            ``EXTRAPOLATOR_LIBRARY``.

    Raises:
        TypeError: If input does not match the type specification.
        ValueError: If noise factors are empty or less than one.
    """

    _DEFINING_ATTRS = (
        "noise_factors",
        "noise_amplifier",
        "extrapolator",
    )

    def __init__(
        self,
        noise_factors: Sequence[float] | None = None,
        noise_amplifier: NoiseAmplifier | None = None,
        extrapolator: Extrapolator | None = None,
    ) -> None:
        self.noise_factors = noise_factors
        self.noise_amplifier = noise_amplifier
        self.extrapolator = extrapolator

    def __repr__(self) -> str:
        attrs_str = ", ".join(
            f"{attr}={repr(getattr(self, attr))}" for attr in self._DEFINING_ATTRS
        )
        return f"ZNEStrategy({attrs_str})"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self.__class__):
            return False
        return all(getattr(self, attr) == getattr(__o, attr) for attr in self._DEFINING_ATTRS)

    def __bool__(self) -> bool:
        return not self.is_noop

    ################################################################################
    ## CONSTRUCTORS
    ################################################################################
    @classmethod
    def noop(cls) -> ZNEStrategy:
        """Construct a no-op ZNE strategy object."""
        return cls(noise_factors=(1,))

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @quality(default=(1,))
    def noise_factors(self, noise_factors: Sequence[float]) -> tuple[float, ...]:
        """Noise factors for ZNE.

        Validation logic defined as required by `quality`.
        """
        if not isinstance(noise_factors, Sequence):
            raise TypeError(
                f"Expected `Sequence` noise factors, received `{type(noise_factors)}` instead."
            )
        noise_factors = tuple(noise_factors)
        if not noise_factors:
            raise ValueError("Noise factors must not be empty.")
        if not all(isreal(nf) for nf in noise_factors):
            raise TypeError("Noise factors must be real valued.")
        if any(nf < 1 for nf in noise_factors):
            raise ValueError("Noise factors must be greater than or equal to one.")

        unsorted_noise_factors = noise_factors
        noise_factors = tuple(sorted(noise_factors))
        if noise_factors != unsorted_noise_factors:
            warn("Unordered noise factors detected and rearranged.", UserWarning, stacklevel=3)

        duplicate_noise_factors = noise_factors
        noise_factors = tuple(sorted(set(noise_factors)))
        if noise_factors != duplicate_noise_factors:
            warn("Duplicate noise factors detected and erased.", UserWarning, stacklevel=3)

        return noise_factors

    @quality(default=MultiQubitAmplifier())
    def noise_amplifier(self, noise_amplifier: NoiseAmplifier) -> NoiseAmplifier:
        """Noise amplifier strategy for ZNE.

        Validation logic defined as required by `quality`.
        """
        if not isinstance(noise_amplifier, NoiseAmplifier):
            raise TypeError(
                f"Expected `NoiseAmplifier` object, received `{type(noise_amplifier)}` instead."
            )
        return noise_amplifier

    @quality(default=LinearExtrapolator())
    def extrapolator(self, extrapolator: Extrapolator) -> Extrapolator:
        """Extrapoaltor strategy for ZNE.

        Validation logic defined as required by `quality`.
        """
        if not isinstance(extrapolator, Extrapolator):
            raise TypeError(
                f"Expected `Extrapolator` object, received `{type(extrapolator)}` instead."
            )
        return extrapolator

    @property
    def num_noise_factors(self) -> int:
        """Number of noise factors."""
        return len(self.noise_factors)

    @property
    def performs_noise_amplification(self) -> bool:
        """Checks if noise amplification is performed."""
        return any(nf > 1 for nf in self.noise_factors)

    @property
    def performs_zne(self) -> bool:
        """Checks if zero noise extrapolation is performed."""
        return self.performs_noise_amplification and self.num_noise_factors > 1

    @property
    def is_noop(self) -> bool:
        """Checks if strategy is no-op."""
        return not self.performs_noise_amplification and not self.performs_zne

    ################################################################################
    ## NOISE AMPLIFICATION
    ################################################################################
    def amplify_circuit_noise(self, circuit: QuantumCircuit, noise_factor: float) -> QuantumCircuit:
        """Noise amplification from :class:`~.noise_amplification.NoiseAmplifier`.

        Args:
            circuit: The original quantum circuit.
            noise_factor: The noise amplification factor by which to amplify the circuit noise.

        Returns:
            The noise amplified quantum circuit
        """
        # TODO: caching
        return self.noise_amplifier.amplify_circuit_noise(circuit, noise_factor)

    # TODO: decouple indexing logic depending on this method
    # TODO: add validation
    def build_noisy_circuits(
        self,
        original_circuits: Iterable[QuantumCircuit] | QuantumCircuit,
    ) -> tuple[QuantumCircuit, ...]:
        """Construct noisy circuits for all noise factors from original circuits.

        Args:
            original_circuits: a :class:`~qiskit.circuit.QuantumCircuit` or a collection of
                :class:`~qiskit.circuit.QuantumCircuit`.

        Returns:
            A tuple containing the noise amplified circuits.
        """

        def generate_noisy_circuits(
            original_circuits: Iterable[QuantumCircuit],
        ) -> Iterator[QuantumCircuit]:
            for circuit in original_circuits:  # type: QuantumCircuit
                for noise_factor in self.noise_factors:  # type: float
                    yield self.amplify_circuit_noise(circuit, noise_factor)

        if isinstance(original_circuits, QuantumCircuit):
            original_circuits = [original_circuits]
        return tuple(generate_noisy_circuits(original_circuits))

    # TODO: decouple indexing logic depending on this method
    def map_to_noisy_circuits(self, arg: Any) -> tuple | None:
        """Map arguments for original circuits to the corresponding arguments for noisy circuits.

        Args:
            arg: Additional non-circuit arguments such as observables or parameter values.

        Returns:
            A tuple of args corresponding to the noise amplified circuits or None.
        """
        if arg is None:
            return arg
        if not isinstance(arg, Iterable):
            arg = [arg]
        mapped_arg: list = []
        for element in arg:
            mapped_arg.extend(element for _ in range(self.num_noise_factors))
        return tuple(mapped_arg)

    ################################################################################
    ## EXTRAPOLATION
    ################################################################################
    # TODO: add validation
    def mitigate_noisy_result(self, noisy_result: EstimatorResult) -> EstimatorResult:
        """Parse results from noisy circuits to error mitigated results.

        Args:
            noisy_result: The unmitigated results.

        Returns:
            The mitigated results after performing zero-noise-extrapolation.
        """
        values: list[float] = []
        metadata: list[Metadata] = []
        for result_group in self._generate_noisy_result_groups(noisy_result):
            data = self._regression_data_from_result_group(result_group)
            val, err, meta = self.extrapolator.extrapolate_zero(*data)
            common_metadata: Metadata = {"std_error": err}  # TODO: extract other common metadata
            zne_metadata: Metadata = self.build_zne_metadata(result_group, meta)
            values.append(val)
            metadata.append({**common_metadata, "zne": zne_metadata})
        return EstimatorResult(values=array(values), metadata=list(metadata))

    # TODO: decouple indexing logic depending on this method
    def _generate_noisy_result_groups(
        self, noisy_result: EstimatorResult
    ) -> Iterator[EstimatorResult]:
        """Generator function for grouping noisy results.

        Iteratively constructs an estimator result for each group of experiments containing
        the measurement results associated with every noise factor.

        Args:
            noisy_result: The estimator result with data from all the experiments performed.

        Yields:
            Estimator results grouping data for experiments with different noise factors,
            but same circuit-observable combinations.

        Raises:
            ValueError: If the number of performed experiments is not an integer multiple of
                the number of noise factors.
        """
        if len(noisy_result.values) % self.num_noise_factors != 0:
            raise ValueError("Inconsistent number of noisy experiments and noise factors.")
        for group in group_elements_gen(
            [
                {"values": v, "metadata": m}
                for v, m in zip(noisy_result.values, noisy_result.metadata)
            ],
            group_size=self.num_noise_factors,
        ):  # type: tuple[EstimatorResultData, ...]
            values, metadata = zip(*[data.values() for data in group])
            yield EstimatorResult(values=array(values), metadata=list(metadata))

    def _regression_data_from_result_group(
        self, result_group: EstimatorResult
    ) -> tuple[list[float], list[float], list[float], list[float]]:
        """Build regression data from noisy result group.

        Args:
            result_group: Estimator result grouping data for experiments with different
                noise factors, but same circuit-observable combinations.

        Returns:
            Regression data
        """
        if len(result_group.values) != self.num_noise_factors:
            raise ValueError("Inconsistent number of noisy experiments and noise factors.")
        x_data = list(self.noise_factors)  # TODO: get actual noise factors achieved
        y_data = result_group.values.tolist()
        sigma_x = [1 for _ in x_data]
        sigma_y = [sqrt(md.get("variance", 1)) for md in result_group.metadata]
        return x_data, y_data, sigma_x, sigma_y  # type: ignore

    # TODO: add validation
    def build_zne_metadata(
        self, result_group: EstimatorResult, extrapolation: Metadata | None = None
    ) -> Metadata:
        """Build ZNE metadata from extrapolation data.

        Args:
            result_group: The grouped noisy results for a single mitigated result.
            extrapolation: extrapolation metadata entries to include (e.g. extrapolation).

        Returns:
            Dictionary containing ZNE metadata.

        Raises:
            ValueError: If the number of experiments does not match the number of noise factors.
        """
        if extrapolation is None:
            extrapolation = {}
        if len(result_group.values) != self.num_noise_factors:
            raise ValueError("Inconsistent number of noisy experiments and noise factors.")
        noise_amplification: Metadata = {
            "noise_amplifier": self.noise_amplifier,
            "noise_factors": self.noise_factors,
            "values": normalize_array(result_group.values),  # TODO: simplify when tuple
        }
        for key in merge_dicts(result_group.metadata):
            value = from_common_key(result_group.metadata, key)
            noise_amplification.update({key: value})
        extrapolation = {
            "extrapolator": self.extrapolator,
            **extrapolation,
        }
        return {"noise_amplification": noise_amplification, "extrapolation": extrapolation}
