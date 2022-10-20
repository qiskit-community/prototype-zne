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

"""Zero Noise Extrapolation (ZNE) strategy configuration dataclass."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from copy import copy
from dataclasses import dataclass
from functools import cached_property
from typing import Any
from warnings import warn

from numpy import array
from qiskit import QuantumCircuit
from qiskit.primitives import EstimatorResult
from qiskit.primitives.utils import _circuit_key
from qiskit.providers import Backend
from qiskit.transpiler import PassManager, StagedPassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from .extrapolation import Extrapolator, LinearExtrapolator
from .noise_amplification import CxAmplifier, NoiseAmplifier
from .types import EstimatorResultData, Metadata, RegressionDatum, ZNECache, ZNECacheKey
from .utils.grouping import from_common_key, group_elements_gen, merge_dicts
from .utils.typing import isreal

NOISE_AMPLIFICATION_STAGE: str = "noise_amplification"


@dataclass
class ZNEStrategy:
    """Zero Noise Extrapolation configuration dataclass.

    Args:
        noise_amplifier: A noise amplification strategy implementing the :class:`NoiseAmplifier`
            interface. A dictionary of currently available options can be imported as
            ``NOISE_AMPLIFIER_LIBRARY``.
        noise_factors: An list of real valued noise factors that determine by what amount the
            circuits' noise is amplified.
        extrapolator: An extrapolation strategy implementing the :class:`Extrapolator`
            interface. A dictionary of currently available options can be imported as
            ``EXTRAPOLATOR_LIBRARY``.
        transpilation_level: Default preset :class:`~qiskit.transpiler.PassManager` level.
            If ``None``, default will be empty (i.e. skip transpilation). If transpiler is
            also provided, it will take precedence over this default.
        transpiler: A :class:`~qiskit.transpiler.PassManager` object expressing the
            transpilation strategy to be performed; if ``None``, defaults will apply. Noise
            amplification will be performed:

            #. In ``noise_amplification`` stage if defined, provided that transpiler is of type
            :class:`~qiskit.transpiler.StagedPassManager` (i.e. overriding said stage but
            maintaining pre and post stages intact).
            #. Right before first ``scheduling`` stage if defined, provided that transpiler
            is of type :class:`~qiskit.transpiler.StagedPassManager` without an explicit
            ``noise_amplification`` stage (i.e. a new ``noise_amplification`` stage will be
            created right before ``scheduling``).
            #. After all specified transpilation passes otherwise.

    Raises:
        TypeError: If input does not match the type specification.
        ValueError: If noise factors are empty or less than one.
        FrozenInstanceError: On attempt to update any data field.
    """

    noise_factors: Sequence[float] = (1,)
    noise_amplifier: NoiseAmplifier = CxAmplifier()
    extrapolator: Extrapolator = LinearExtrapolator()
    transpilation_level: int | None = 1
    transpiler: PassManager | None = None

    ################################################################################
    ## NEW
    ################################################################################
    @classmethod
    def noop(cls) -> ZNEStrategy:
        """Construct a no-op ZNE strategy object."""
        return cls(noise_factors=(1,))

    ################################################################################
    ## INIT
    ################################################################################
    def __post_init__(self) -> None:
        """Input parsing and validation."""
        self._validate_noise_amplifier()
        self._validate_noise_factors()
        self._validate_extrapolator()
        self._validate_transpilation_level()
        self._validate_transpiler()

    def _validate_noise_amplifier(self) -> None:
        """Validate noise amplifier."""
        if not isinstance(self.noise_amplifier, NoiseAmplifier):
            raise TypeError(
                f"Expected NoiseAmplifier object, received {type(self.noise_amplifier)} instead."
            )

    def _validate_noise_factors(self) -> None:
        """Validate noise factors config."""
        if not isinstance(self.noise_factors, Sequence):
            raise TypeError(
                f"Expected Sequence object, received {type(self.noise_factors)} instead."
            )
        if not isinstance(self.noise_factors, tuple):
            self.noise_factors = tuple(self.noise_factors)
        if not self.noise_factors:
            raise ValueError("Noise factors must not be empty.")
        for noise_factor in self.noise_factors:  # type: float
            if not isreal(noise_factor):
                raise TypeError("Noise factors must be real valued.")
            if noise_factor < 1:
                raise ValueError("Noise factors must be greater than or equal to one.")
        noise_factors = tuple(sorted(self.noise_factors))
        if self.noise_factors != noise_factors:
            warn("Unordered noise factors detected and rearranged.", UserWarning, stacklevel=3)
            self.noise_factors = noise_factors
        noise_factors = tuple(sorted(set(self.noise_factors)))
        if self.noise_factors != noise_factors:
            warn("Duplicate noise factors detected and erased.", UserWarning, stacklevel=3)
            self.noise_factors = noise_factors

    def _validate_extrapolator(self) -> None:
        """Validate extrapolator."""
        if not isinstance(self.extrapolator, Extrapolator):
            raise TypeError(
                f"Expected Extrapolator object, received {type(self.extrapolator)} instead."
            )

    def _validate_transpilation_level(self) -> None:
        """Validate transpilation level config."""
        if not isinstance(self.transpilation_level, (int, type(None))):
            raise TypeError(
                f"Expected optional int, received {type(self.transpilation_level)} instead."
            )

    def _validate_transpiler(self) -> None:
        """Validate transpiler."""
        if isinstance(self.transpiler, (StagedPassManager, type(None))):
            pass
        elif isinstance(self.transpiler, PassManager):
            stages = {"transpilation": self.transpiler}
            transpiler = StagedPassManager(stages, **stages)
            self.transpiler = transpiler
        else:
            raise TypeError(
                f"Expected optional PassManager object, received {type(self.transpiler)} instead."
            )

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @cached_property
    def num_noise_factors(self) -> int:
        """Number of noise factors."""
        return len(self.noise_factors)

    @cached_property
    def performs_noise_amplification(self) -> bool:
        """Checks if noise amplification is performed."""
        return any(nf > 1 for nf in self.noise_factors)

    @cached_property
    def performs_zne(self) -> bool:
        """Checks if zero noise extrapolation is performed."""
        return self.performs_noise_amplification and self.num_noise_factors > 1

    @cached_property
    def is_noop(self) -> bool:
        """Checks if strategy is no-op."""
        return not self.performs_noise_amplification and not self.performs_zne

    ################################################################################
    ## TRANSPILATION (experimental)
    ################################################################################
    def build_transpilers(self, backend: Backend) -> tuple[StagedPassManager, ...]:
        """Generate noisy transpilers from configuration data for provided backend.

        Args:
            backend: target backend for the transpilers.

        Returns:
            An tuple of :class:`~qiskit.transpiler.StagedPassManager`s according to configs,
            with a ``noise_amplification`` stage, and for different noise_factors.
        """

        def build_transpiler(noise_factor: float) -> StagedPassManager:
            if self.performs_noise_amplification:
                return self.build_noisy_transpiler(backend, noise_factor)
            return self.build_noiseless_transpiler(backend)

        return tuple(build_transpiler(nf) for nf in self.noise_factors)

    def build_noisy_transpiler(self, backend: Backend, noise_factor: float) -> StagedPassManager:
        """Generate transpiler from configuration data for provided backend and noise factor.

        Args:
            backend: target backend for the transpiler.
            noise_factor: real number representing the amount that the circuit's noise
                will be amplified.

        Returns:
            An instance of :class:`~qiskit.transpiler.StagedPassManager` according to configs,
            with a ``noise_amplification`` stage.

        Raises:
            TypeError: If provided noise factor is not real valued.
        """
        if not isreal(noise_factor):
            raise TypeError("Noise factor must be real valued.")
        transpiler: StagedPassManager = self.build_noiseless_transpiler(backend)
        setattr(
            transpiler,
            NOISE_AMPLIFICATION_STAGE,
            self.noise_amplifier.build_pass_manager(noise_factor),
        )
        return transpiler

    def build_noiseless_transpiler(self, backend: Backend) -> StagedPassManager:
        """Generate noiseless transpiler from configuration data for provided backend.

        Args:
            backend: target backend for the transpiler.

        Returns:
            An new instance of :class:`~qiskit.transpiler.StagedPassManager` according to configs,
            with a void ``noise_amplification`` stage.
        """
        transpiler: StagedPassManager = (
            self.transpiler
            if self.transpiler is not None
            else self.build_default_transpiler(backend)
        )
        if NOISE_AMPLIFICATION_STAGE in transpiler.stages:
            transpiler = self._clear_noise_amplification_stage(transpiler, warn_user=True)
        else:
            transpiler = self._insert_void_noise_amplification_stage(transpiler)
        return transpiler

    def build_default_transpiler(self, backend: Backend) -> StagedPassManager:
        """Generate default transpiler from configuration data for provided backend.

        Args:
            backend: target backend for the transpiler.

        Returns:
            The default transpiler pass manager according to configs.

        Raises:
            TypeError: If backend is not of the :class:`~qiskit.providers.Backend`
        """
        if self.transpilation_level is None:
            return StagedPassManager()
        if not isinstance(backend, Backend):
            raise TypeError(f"Expected Backend object, received {type(backend)} instead.")
        return generate_preset_pass_manager(self.transpilation_level, backend=backend)

    @staticmethod
    def _clear_noise_amplification_stage(
        pass_manager: StagedPassManager, warn_user: bool = False
    ) -> StagedPassManager:
        """Set ``noise_amplification`` stage in input StagedPassManager to ``None``.

        Args:
            pass_manager: The :class:`~qiskit.transpiler.StagedPassManager` object to clear.

        Returns:
            StagedPassManager: A shallow copy of the input pass manager with its
                ``noise_amplification`` stage set to ``None``.

        Raises:
            ValueError: If ``noise_amplification`` is not present.
        """
        if NOISE_AMPLIFICATION_STAGE not in pass_manager.stages:
            raise ValueError("Missing ``noise_amplification`` stage.")
        pass_manager = copy(pass_manager)
        if getattr(pass_manager, NOISE_AMPLIFICATION_STAGE) is not None:
            setattr(pass_manager, NOISE_AMPLIFICATION_STAGE, None)
            if warn_user:
                warn("Noise amplification stage cleared.", UserWarning)
        return pass_manager

    def _insert_void_noise_amplification_stage(
        self,
        pass_manager: StagedPassManager,
    ) -> StagedPassManager:
        """Insert void ``noise_amplification`` stage to input StagedPassManager.

        #. Before first ``scheduling`` stage if any.
        #. After all other passes otherwise.

        Args:
            pass_manager: The :class:`~qiskit.transpiler.StagedPassManager` object to insert
                the stage into.

        Returns:
            StagedPassManager: A shallow copy of the input pass manager with an additional void
                ``noise_amplification`` stage.

        Raises:
            ValueError: If ``noise_amplification`` is already present.
        """
        if NOISE_AMPLIFICATION_STAGE in pass_manager.stages:
            raise ValueError("Found ``noise_amplification`` stage already present.")
        stage_names = self._build_noisy_stages(pass_manager.stages)
        stages = {stage: getattr(pass_manager, stage, None) for stage in set(stage_names)}
        return StagedPassManager(stage_names, **stages)

    @staticmethod
    def _build_noisy_stages(original_stages: Sequence[str]) -> tuple[str, ...]:
        """Build noisy stages tuple from original stages."""

        def generate_noisy_stages(original_stages: Sequence[str]) -> Iterator[str]:
            noise_amplification_stages: Iterator[str] = iter([NOISE_AMPLIFICATION_STAGE])
            for stage in original_stages:
                if stage == "scheduling":
                    yield from noise_amplification_stages
                yield stage
            yield from noise_amplification_stages

        return tuple(generate_noisy_stages(original_stages))

    ################################################################################
    ## NOISE AMPLIFICATION
    ################################################################################
    def amplify_circuit_noise(self, circuit: QuantumCircuit, noise_factor: float) -> QuantumCircuit:
        """Cached noise amplification from :class:`~.noise_amplification.NoiseAmplifier`.

        Args:
            circuit: The original quantum circuit.
            noise_factor: The noise amplification factor by which to amplify the circuit noise.

        Returns:
            The noise amplified quantum circuit
        """
        # TODO: cached method when QuantumCircuit.__hash__ is implemented
        if not hasattr(self, "_zne_cache"):
            self._zne_cache: ZNECache = {}  # pylint: disable=attribute-defined-outside-init
        CACHE_MAXSIZE = 256  # pylint: disable=invalid-name
        zne_cache: ZNECache = self._zne_cache
        cache_key: ZNECacheKey = (_circuit_key(circuit), noise_factor)
        noisy_circuit: QuantumCircuit = zne_cache.get(cache_key, None)
        if noisy_circuit is None:
            noisy_circuit = self.noise_amplifier.amplify_circuit_noise(circuit, noise_factor)
            # TODO: implement LRU (least recently used) functionality
            if len(zne_cache) < CACHE_MAXSIZE:
                zne_cache.update({cache_key: noisy_circuit})
        return noisy_circuit

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
            val, meta = self.extrapolator.extrapolate_zero(data)
            common_metadata: Metadata = {}  # TODO: extract common metadata
            zne_metadata: Metadata = self.build_zne_metadata(result_group, meta)
            values.append(val)
            metadata.append({**common_metadata, "zne": zne_metadata})
        return EstimatorResult(values=array(values), metadata=tuple(metadata))

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
            ValueError: If the number of performed experiments is not an integer mutliple of
                the number of noise factors.
        """
        if noisy_result.num_experiments % self.num_noise_factors != 0:
            raise ValueError("Inconsistent number of noisy experiments and noise factors.")
        for group in group_elements_gen(
            noisy_result.experiments, group_size=self.num_noise_factors
        ):  # type: tuple[EstimatorResultData, ...]
            values, metadata = zip(*[data.values() for data in group])
            yield EstimatorResult(values=array(values), metadata=list(metadata))

    def _regression_data_from_result_group(
        self, result_group: EstimatorResult
    ) -> tuple[RegressionDatum, ...]:
        """Build regression data from noisy result group.

        Args:
            result_group: Estimator result grouping data for experiments with different
                noise factors, but same circuit-observable combinations.

        Returns:
            Regression data
        """
        if result_group.num_experiments != self.num_noise_factors:
            raise ValueError("Inconsistent number of noisy experiments and noise factors.")
        values: list[float] = result_group.values.tolist()
        variances: list[float] = [md.get("variance", 0) for md in result_group.metadata]
        return tuple(zip(self.noise_factors, values, variances))

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
        if result_group.num_experiments != self.num_noise_factors:
            raise ValueError("Inconsistent number of noisy experiments and noise factors.")
        noise_amplification: Metadata = {
            "noise_amplifier": self.noise_amplifier,
            "noise_factors": self.noise_factors,
            "values": tuple(result_group.values.tolist()),  # TODO: simplify when tuple
        }
        for key in merge_dicts(result_group.metadata):
            value = from_common_key(result_group.metadata, key)
            noise_amplification.update({key: value})
        extrapolation = {
            "extrapolator": self.extrapolator,
            **extrapolation,
        }
        return {"noise_amplification": noise_amplification, "extrapolation": extrapolation}
