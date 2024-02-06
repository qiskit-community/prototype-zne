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

"""Estimator Job with embeded ZNE parsing."""

from __future__ import annotations

from typing import Any

from qiskit.primitives import EstimatorResult
from qiskit.providers import JobV1 as Job

from ..zne_strategy import ZNEStrategy


class ZNEJob(Job):
    """Estimator Job with embeded ZNE parsing."""

    def __init__(  # pylint: disable=super-init-not-called
        self,
        base_job: Job,
        zne_strategy: ZNEStrategy,
        target_num_experiments: int,
    ) -> None:
        self._base_job: Job = base_job
        self._zne_strategy: ZNEStrategy = zne_strategy
        self._target_num_experiments: int = target_num_experiments

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def base_job(self) -> Job:
        """Base Job for noisy results."""
        return self._base_job

    @property
    def zne_strategy(self) -> ZNEStrategy:
        """ZNE strategy object."""
        return self._zne_strategy

    @property
    def target_num_experiments(self) -> int:
        """Expected number of results after ZNE is performed."""
        return self._target_num_experiments

    ################################################################################
    ## ZNE
    ################################################################################
    def result(self) -> EstimatorResult:
        """Return the results of the job."""
        result: EstimatorResult = self.base_job.result()
        if self.zne_strategy.performs_zne:
            result = self.zne_strategy.mitigate_noisy_result(result)
        if len(result.values) != self.target_num_experiments:
            # TODO: consider warning instead -> should be in integration tests
            raise RuntimeError(
                "Number of experiments in EstimatorResult object does not match "
                "the requested number of experiments."
            )
        return result

    ################################################################################
    ## NESTED JOB DELEGATION
    ################################################################################
    _ZNE_ATTRIBUTES: set = {
        "base_job",
        "_base_job",
        "zne_strategy",
        "_zne_strategy",
        "target_num_experiments",
        "_target_num_experiments",
        "result",
    }

    def __getattribute__(self, name: str) -> Any:
        if name == "_ZNE_ATTRIBUTES" or name in self._ZNE_ATTRIBUTES:
            return super().__getattribute__(name)
        return getattr(self.base_job, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._ZNE_ATTRIBUTES:
            return super().__setattr__(name, value)
        return setattr(self.base_job, name, value)

    def __delattr__(self, name: str) -> None:
        if name in self._ZNE_ATTRIBUTES:
            return super().__delattr__(name)
        return delattr(self.base_job, name)

    ################################################################################
    ## DUMMY ABSTRACT METHOD IMPLEMENTATION
    ################################################################################
    def submit(self):
        """Submit the job to the backend for execution."""
        return self.base_job.submit()

    def status(self):
        """Return the status of the job, among the values of ``JobStatus``."""
        return self.base_job.status()
