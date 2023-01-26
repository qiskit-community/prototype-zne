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

"""ZNE functionality for :method:`qiskit.primitives.BaseEstimator.__init__` method."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from functools import wraps

from numpy import ndarray
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.quantum_info.operators import SparsePauliOp

from ..zne_strategy import ZNEStrategy

Sequence.register(ndarray)


def zne_init(init: Callable) -> Callable:
    """Add ZNE functionality to :method:`qiskit.primitives.BaseEstimator.__init__`."""

    if not callable(init):
        raise TypeError("Invalid `init` argument, expected callable.")

    @wraps(init)
    def _zne_init(  # pylint: disable=too-many-arguments
        self,
        circuits: Iterable[QuantumCircuit] | QuantumCircuit | None = None,
        observables: Iterable[SparsePauliOp] | SparsePauliOp | None = None,
        parameters: Iterable[Iterable[Parameter]] | None = None,
        options: dict | None = None,
        zne_strategy: ZNEStrategy | None = None,
        **kwargs,
    ) -> None:
        if circuits is not None or observables is not None or parameters is not None:
            raise TypeError(
                "The BaseEstimator `circuits`, `observables`, `parameters` kwarg are "
                "deprecated as of Qiskit Terra 0.22.0. Use the 'run' method instead.",
            )
        self.zne_strategy = zne_strategy
        return init(self, options=options, **kwargs)

    return _zne_init
