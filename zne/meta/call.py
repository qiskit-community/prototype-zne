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

"""ZNE functionality for :method:`qiskit.primitives.BaseEstimator.__call__` method."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import wraps

from numpy import ndarray
from qiskit.circuit import QuantumCircuit
from qiskit.primitives import EstimatorResult
from qiskit.quantum_info.operators import SparsePauliOp
from qiskit.utils.deprecation import deprecate_arguments

Sequence.register(ndarray)


################################################################################
## DECORATOR
################################################################################
def zne_call(call: Callable) -> Callable:
    """Add ZNE functionality to :method:`qiskit.primitives.BaseEstimator.__call__`."""

    if not callable(call):
        raise TypeError("Invalid `call` argument, expected callable.")

    @wraps(call)
    @deprecate_arguments({"circuit_indices": "circuits", "observable_indices": "observables"})
    def _zne_call(
        self,
        circuits: Sequence[int | QuantumCircuit],
        observables: Sequence[int | SparsePauliOp],
        parameter_values: Sequence[Sequence[float]] | None = None,
        **run_options,
    ) -> EstimatorResult:
        raise TypeError(
            "The BaseEstimator.__call__ method is deprecated as of Qiskit Terra 0.22.0. "
            "Use the 'run' method instead.",
        )

    return _zne_call
