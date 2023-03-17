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

"""Type definitions for the Zero Noise Extrapolation (ZNE) Estimator class."""

from typing import Any, Dict, Sequence, Tuple, Union

from qiskit import QuantumCircuit

Metadata = Dict[str, Any]
EstimatorResultData = Dict[str, Union[float, Metadata]]
ParameterVector = Sequence[float]  # TODO: qiskit.circuit::ParameterVector
CircuitKey = tuple
NoiseFactor = float
ZNECacheKey = Tuple[CircuitKey, NoiseFactor]
ZNECache = Dict[ZNECacheKey, QuantumCircuit]
