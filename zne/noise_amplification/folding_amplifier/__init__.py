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

from .global_folding_amplifier import GlobalFoldingAmplifier
from .local_folding_amplifier import (
    CxAmplifier,
    LocalFoldingAmplifier,
    MultiQubitAmplifier,
    TwoQubitAmplifier,
)

__all__ = [
    "GlobalFoldingAmplifier",
    "LocalFoldingAmplifier",
    "CxAmplifier",
    "TwoQubitAmplifier",
    "MultiQubitAmplifier",
]
