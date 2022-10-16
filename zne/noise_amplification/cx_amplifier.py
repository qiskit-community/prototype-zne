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

"""Digital noise amplifier acting on CX gates exclusively."""

from __future__ import annotations

from .folding_amplifier import LocalFoldingAmplifier


class CxAmplifier(LocalFoldingAmplifier):
    """
    Digital noise amplifier acting on CX gates exclusively.

    Replaces each CX gate with as many CX gates as indicated by the noise_factor.

    In order to keep the same logical quantum state at the end of the circuit,
    we need noise_factor to be an odd (positive) integer.
    """

    def __init__(  # pylint: disable=too-many-arguments,duplicate-code
        self,
        sub_folding_option: str = "from_first",
        random_seed: int | None = None,
        noise_factor_relative_tolerance: float = 1e-2,
        warn_user: bool = True,
    ) -> None:
        super().__init__(
            gates_to_fold="cx",
            sub_folding_option=sub_folding_option,
            random_seed=random_seed,
            noise_factor_relative_tolerance=noise_factor_relative_tolerance,
            warn_user=warn_user,
        )
