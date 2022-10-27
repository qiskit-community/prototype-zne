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

"""Noise amplification library."""

from ..utils import build_dict_library
from .folding_amplifier import (
    CxAmplifier,
    GlobalFoldingAmplifier,
    LocalFoldingAmplifier,
    TwoQubitAmplifier,
)
from .noise_amplifier import CircuitNoiseAmplifier, DAGNoiseAmplifier, NoiseAmplifier

NOISE_AMPLIFIER_LIBRARY: dict = build_dict_library(
    GlobalFoldingAmplifier,
    LocalFoldingAmplifier,
    CxAmplifier,
    TwoQubitAmplifier,
)

__all__ = [
    "NoiseAmplifier",
    "CircuitNoiseAmplifier",
    "DAGNoiseAmplifier",
    *NOISE_AMPLIFIER_LIBRARY.keys(),
]
