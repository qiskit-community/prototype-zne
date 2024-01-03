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

"""Noise amplification strategy via unitary/inverse repetition."""

from __future__ import annotations

from warnings import warn

from numpy.random import Generator, default_rng
from qiskit import QuantumCircuit
from qiskit.dagcircuit import DAGCircuit

from ...utils.typing import isreal
from ..noise_amplifier import NoiseAmplifier


class FoldingAmplifier(NoiseAmplifier):
    """Interface for folding amplifier strategies."""

    def __init__(  # pylint: disable=super-init-not-called, duplicate-code, too-many-arguments
        self,
        sub_folding_option: str = "from_first",
        barriers: bool = True,
        random_seed: int | None = None,
        noise_factor_relative_tolerance: float = 1e-2,
        warn_user: bool = True,
    ) -> None:
        """
        Args:
            sub_folding_option: Specifies which gates are used for sub folding when
                ``noise_factor`` is not an odd integer. Can either be "from_last", "from_first", or
                "random".
            barriers: If True applies barriers when folding (e.g. to avoid simplification).
            random_seed: Random seed used for performing random sub-gate-folding.
            noise_factor_relative_tolerance: Relative allowed tolerance interval between
                ``noise_factor`` input and actual noise factor that was used for the amplification.
                If the discrepancy exceeds the tolerance, a warning is displayed.
            warn_user: Specifies whether user warnings are displayed.
        """
        self.warn_user: bool = warn_user
        self._set_sub_folding_option(sub_folding_option)
        self._set_barriers(barriers)
        self._prepare_rng(random_seed)
        self._set_noise_factor_relative_tolerance(noise_factor_relative_tolerance)

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def options(self) -> dict:
        """Strategy options."""
        options: dict = self._init_options
        options.pop("warn_user", None)
        return options

    @property
    def warn_user(self) -> bool:
        """Option whether warnings are displayed."""
        return self._warn_user

    @warn_user.setter
    def warn_user(self, warn_user: bool) -> None:
        if not isinstance(warn_user, bool):
            raise TypeError(f"Expected boolean, received {type(warn_user)} instead.")
        self._warn_user: bool = warn_user

    @property
    def sub_folding_option(self) -> str:
        """Option for sub-gate-folding.

        Specifies which gates of the full circuit are used for sub folding when ``noise_factor`` is
        is not an odd integer. Can either be "from_last", "from_first", or "random".
        """
        return self._sub_folding_option

    def _set_sub_folding_option(self, sub_folding_option: str) -> None:
        if sub_folding_option not in ["from_last", "from_first", "random"]:
            raise ValueError(
                f"Sub-folding option must be a string of either 'from_last', 'from_first, or "
                f"'random'. Received {sub_folding_option} instead."
            )
        self._sub_folding_option: str = sub_folding_option

    @property
    def barriers(self) -> bool:
        """Option for whether to apply barriers when folding."""
        return self._barriers

    def _set_barriers(self, barriers: bool) -> None:
        self._barriers = bool(barriers)

    def _prepare_rng(self, seed: int | None = None) -> None:
        """Sets random number generator with seed."""
        if not isinstance(seed, (type(None), int)):
            raise TypeError("Random seed must be an integer or None.")
        self._rng: Generator = default_rng(seed)

    # TODO: add property getter
    def _set_noise_factor_relative_tolerance(self, tolerance: float) -> None:
        """Sets noise factor relative tolerance."""
        if not isreal(tolerance):
            raise TypeError("Noise factor relative tolerance must be real valued.")
        self._noise_factor_relative_tolerance: float = tolerance

    ################################################################################
    ## FOLDING METHODS
    ################################################################################
    @staticmethod
    def folding_to_noise_factor(folding: float) -> float:
        """Converts number of foldings to noise factor.

        Args:
            folding: The number of foldings.

        Returns:
            The corresponding noise factor.
        """
        return 2 * folding + 1

    def warn(self, *args, **kwargs):
        """Throws user warning if enabled."""
        if self.warn_user:
            warn(*args, **kwargs)

    def _validate_noise_factor(self, noise_factor):
        """Validates noise factor.

        Args:
            noise_factor: The noise amplification factor by which to amplify the circuit noise.

        Raises:
            ValueError: If the noise factor is smaller than 1.
        """
        if noise_factor < 1:
            raise ValueError(
                f"{self.name} expects a positive float noise_factor >= 1."
                f"Received {noise_factor} instead."
            )

    def _apply_barrier(self, circuit: QuantumCircuit, *registers) -> QuantumCircuit:
        """Apply barrier to specified registers if option is set."""
        if self._barriers:
            circuit.barrier(*registers)
        return circuit

    def _compute_folding_nums(self, noise_factor: float, num_instructions: int) -> tuple[int, int]:
        """Returns required number of full foldings and sub foldings.

        Args:
            noise_factor: The noise amplification factor by which to fold the circuit.
            num_instructions: The number of instructions to fold.

        Returns:
            A tuple containing the number of full-and sub-foldings.
        """
        if num_instructions == 0:
            self.warn("Noise amplification is not performed since none of the gates are folded.")
            return 0, 0
        num_foldings = round(num_instructions * (noise_factor - 1) / 2.0)
        closest_noise_factor: float = self.folding_to_noise_factor(num_foldings / num_instructions)
        relative_error = abs(closest_noise_factor - noise_factor) / noise_factor
        if relative_error > self._noise_factor_relative_tolerance:
            warn(
                "Rounding of noise factor: Foldings are performed with noise factor "
                f"{closest_noise_factor:.2f} instead of specified noise factor "
                f"{noise_factor:.2f} which amounts to a relative error of "
                f"{relative_error * 100:.2f}%."
            )
        num_full_foldings, num_sub_foldings = divmod(num_foldings, num_instructions)
        return num_full_foldings, num_sub_foldings

    ################################################################################
    ## IMPLEMENTATION
    ################################################################################
    # pylint: disable=useless-parent-delegation
    def amplify_dag_noise(
        self, dag: DAGCircuit, noise_factor: float
    ) -> DAGCircuit:  # pragma: no cover
        return super().amplify_dag_noise(dag, noise_factor)
