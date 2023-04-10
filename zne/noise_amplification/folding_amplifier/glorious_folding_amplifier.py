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

"""Glorious Global Folding Noise Amplfiier (Temporary)"""

import math
from collections import namedtuple

from ..noise_amplifier import DAGNoiseAmplifier

Folding = namedtuple("Folding", ("full", "partial", "effective_noise_factor"))
# noise_factor = approximate noise_factor


class GloriousFoldingAmplifier(DAGNoiseAmplifier):
    """Interface for folding amplifier strategies."""

    def _compute_folding_nums(self, noise_factor: float, num_nodes: int) -> Folding:
        """Compute number of foldings.

        Args:
            noise_factor: The original noise_factor input.
            num_nodes: total number of foldable nodes for input DAG

        Returns:
            Folding: named tuple containing full foldings, number of gates to partially fold and
            effective noise factor of the operation
        """
        noise_factor = self._validate_noise_factor(noise_factor)
        foldings = (noise_factor - 1) / 2
        full = int(foldings)
        partial_foldings = foldings - full
        partial = self._compute_best_estimate(partial_foldings * num_nodes, partial_foldings)
        effective_noise_factor = (
            (num_nodes - partial) * self._folding_to_noise_factor(full)
            + partial
            * (
                self._folding_to_noise_factor(full)
                + self._folding_to_noise_factor(partial_foldings)
            )
        ) / num_nodes
        return Folding(full, partial, effective_noise_factor)

    def _compute_best_estimate(self, num_partial_gates: float, partial_foldings: float) -> float:
        """Computes best estimates from possible candidates for number of partial folded gates

        Args:
            num_partial_gates: Original float of calculated partial gates
            partial_foldings: Extra foldings required

        Returns:
            float: returns closest estimated number of gates required to be partially folded
            to achieve the user expected noise_factor
        """
        possible_estimates = [math.floor(num_partial_gates), math.ceil(num_partial_gates)]
        if abs(possible_estimates[0] - partial_foldings) < abs(
            possible_estimates[1] - partial_foldings
        ):
            return possible_estimates[0]
        return possible_estimates[1]

    def _folding_to_noise_factor(self, foldings: float) -> float:
        return 2 * foldings + 1

    def _validate_noise_factor(self, noise_factor: float) -> float:
        """Normalizes and validates noise factor.

        Args:
            noise_factor: The original noisefactor input.

        Returns:
            float: Normalised noise_factor input.

        Raises:
            ValueError: If input noise_factor value is not of type float.
            TypeError: If input noise_factor value is not of type float.
        """
        try:
            noise_factor = float(noise_factor)
        except ValueError:
            raise ValueError(  # pylint: disable=raise-missing-from
                f"Expected positive float value, received {noise_factor} instead."
            )
        except TypeError:
            raise TypeError(  # pylint: disable=raise-missing-from
                f"Expected positive float value, received {noise_factor} instead."
            )
        if noise_factor < 1:
            raise ValueError(
                f"Expected positive float noise_factor >= 1, received {noise_factor} instead."
            )
        return noise_factor
