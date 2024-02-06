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

"""Zero Noise Extrapolation (ZNE) prototype for error mitigation on
Qiskit's Estimator primitive."""

from .extrapolation import EXTRAPOLATOR_LIBRARY
from .meta import ZNEJob, zne
from .noise_amplification import NOISE_AMPLIFIER_LIBRARY
from .zne_strategy import ZNEStrategy

__copyright__ = "(C) Copyright IBM 2022"
__version__ = "1.3.1"


__all__ = [
    "__copyright__",
    "__version__",
    "zne",
    "ZNEJob",
    "ZNEStrategy",
    "EXTRAPOLATOR_LIBRARY",
    "NOISE_AMPLIFIER_LIBRARY",
]
