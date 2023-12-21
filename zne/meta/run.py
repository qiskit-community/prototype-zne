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

"""ZNE functionality for :method:`qiskit.primitives.BaseEstimator._run` method."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from qiskit.circuit import QuantumCircuit
from qiskit.providers import JobV1 as Job
from qiskit.quantum_info.operators.base_operator import BaseOperator

from ..zne_strategy import ZNEStrategy
from .job import ZNEJob


def zne_run(run: Callable) -> Callable:
    """Add ZNE functionality to :method:`qiskit.primitives.BaseEstimator._run`."""

    if not callable(run):
        raise TypeError("Invalid `run` argument, expected callable.")

    @wraps(run)
    def _zne_run(
        self,
        circuits: tuple[QuantumCircuit, ...],
        observables: tuple[BaseOperator, ...],
        parameter_values: tuple[tuple[float, ...], ...],
        zne_strategy: ZNEStrategy | None = ...,  # type: ignore
        **run_options,
    ) -> Job:
        # Strategy
        if zne_strategy is Ellipsis:
            zne_strategy = self.zne_strategy
        elif zne_strategy is None:
            zne_strategy = ZNEStrategy.noop()
        elif not isinstance(zne_strategy, ZNEStrategy):
            raise TypeError("Invalid zne_strategy object, expected ZNEStrategy.")

        # ZNE
        target_num_experiments: int = len(circuits)
        if zne_strategy.performs_noise_amplification:
            circuits = zne_strategy.build_noisy_circuits(circuits)
            observables = zne_strategy.map_to_noisy_circuits(observables)
            parameter_values = zne_strategy.map_to_noisy_circuits(parameter_values)

        # Job
        job: Job = run(
            self,
            circuits=circuits,
            observables=observables,
            parameter_values=parameter_values,
            **run_options,
        )
        return ZNEJob(job, zne_strategy, target_num_experiments)

    return _zne_run
