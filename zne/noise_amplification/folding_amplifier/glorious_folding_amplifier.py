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

from ..noise_amplifier import DAGNoiseAmplifier


class GloriousFoldingAmplifier(DAGNoiseAmplifier):
    """Interface for folding amplifier strategies."""

    def _compute_num_foldings(self, noise_factor: float) -> int:
        """Compute number of foldings.

        Args:
            noise_factor: The original noise_factor input.
        Returns:
            int: Number of foldings calculated from noise_factor.
        """
        noise_factor = self._validate_noise_factor(noise_factor)
        return int((noise_factor - 1) / 2)

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
        if noise_factor % 2 == 0:
            raise ValueError(
                f"Expected positive odd noise_factor, received {noise_factor} instead."
            )
        return noise_factor
