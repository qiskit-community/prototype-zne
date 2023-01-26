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

from unittest.mock import Mock

from numpy import array
from pytest import fixture, mark, raises
from qiskit.primitives import EstimatorResult

from zne.meta.job import ZNEJob
from zne.zne_strategy import ZNEStrategy


################################################################################
## FIXTURES
################################################################################
@fixture(scope="module")
def base_job():
    return "base_job"


@fixture(scope="module")
def zne_strategy():
    return "zne_strategy"


@fixture(scope="module")
def target_num_experiments():
    return "target_num_experiments"


################################################################################
## TESTS
################################################################################
def test_init(base_job, zne_strategy, target_num_experiments):
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    assert job.base_job == base_job
    assert job.zne_strategy == zne_strategy
    assert job.target_num_experiments == target_num_experiments


def test_porperties(base_job, zne_strategy, target_num_experiments):
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    assert job.base_job is job._base_job
    assert job.zne_strategy is job._zne_strategy
    assert job.target_num_experiments is job._target_num_experiments


@mark.parametrize(
    "target_num_experiments, num_noise_factors",
    [
        (1, 1),
        (1, 2),
        (2, 1),
        (2, 2),
    ],
)
def test_result(target_num_experiments, num_noise_factors):
    # Results
    values = [0] * target_num_experiments
    noisy_values = values * num_noise_factors
    result = EstimatorResult(values=array(values), metadata=[{}] * len(values))
    noisy_result = EstimatorResult(values=array(noisy_values), metadata=[{}] * len(noisy_values))

    # Jobs
    base_job = Mock()
    base_job.result = Mock(return_value=noisy_result)
    zne_strategy = ZNEStrategy(noise_factors=range(1, num_noise_factors + 1))
    zne_strategy.mitigate_noisy_result = Mock(return_value=result)
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)

    # Testing
    if zne_strategy.performs_zne:
        assert job.result() is result
    else:
        assert job.result() is noisy_result


@mark.parametrize(
    "target_num_experiments, num_noise_factors",
    [
        (1, 1),
        (1, 2),
        (2, 1),
        (2, 2),
    ],
)
def test_result_runtime_error(target_num_experiments, num_noise_factors):
    # Results
    values = [0] * (target_num_experiments + 1)  # Introducing discrepancy
    noisy_values = values * num_noise_factors
    result = EstimatorResult(values=array(values), metadata=[{}] * len(values))
    noisy_result = EstimatorResult(values=array(noisy_values), metadata=[{}] * len(noisy_values))

    # Jobs
    base_job = Mock()
    base_job.result = Mock(return_value=noisy_result)
    zne_strategy = ZNEStrategy(noise_factors=range(1, num_noise_factors + 1))
    zne_strategy.mitigate_noisy_result = Mock(return_value=result)
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)

    # Testing
    with raises(RuntimeError):
        job.result()


################################################################################
## NESTED JOB DELEGATION
################################################################################
@mark.parametrize(
    "attr",
    "When things are in danger someone has to give them up so that others may keep them".split(),
)
def test_getattribute(zne_strategy, target_num_experiments, attr):
    base_job = Mock()
    setattr(base_job, attr, f"value of {attr}")
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    assert getattr(job, attr) is getattr(base_job, attr)


@mark.parametrize("attr", ZNEJob._ZNE_ATTRIBUTES)
def test_getattribute_zne(base_job, zne_strategy, target_num_experiments, attr):
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    assert getattr(job, attr) is not getattr(base_job, attr, f"base_{attr}")


@mark.parametrize(
    "attr",
    "All we have to decide is what to do with the time that is given to us".split(),
)
def test_setattr(zne_strategy, target_num_experiments, attr):
    base_job = Mock()
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    setattr(job, attr, f"value of {attr}")
    assert getattr(job, attr) is getattr(base_job, attr)


@mark.parametrize(
    "attr",
    [
        attr
        for attr in ZNEJob._ZNE_ATTRIBUTES
        if not isinstance(getattr(ZNEJob, attr, None), property)
    ],
)
def test_setattr_zne(base_job, zne_strategy, target_num_experiments, attr):
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    setattr(job, attr, f"value of {attr}")
    assert getattr(job, attr) is object.__getattribute__(job, attr)
    assert getattr(job, attr) is not getattr(base_job, attr, f"base_{attr}")


@mark.parametrize(
    "attr",
    "And some things that should not have been forgotten were lost".split(),
)
def test_delattr(zne_strategy, target_num_experiments, attr):
    base_job = Mock()
    setattr(base_job, attr, f"value of {attr}")
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    delattr(job, attr)
    NOT_FOUND = Mock()
    assert getattr(base_job, attr, NOT_FOUND) is NOT_FOUND


@mark.parametrize(
    "attr",
    [
        attr
        for attr in ZNEJob._ZNE_ATTRIBUTES
        if not isinstance(getattr(ZNEJob, attr, None), property)
        and not isinstance(getattr(ZNEJob, attr, None), type(lambda: ...))
    ],
)
def test_delattr_zne(zne_strategy, target_num_experiments, attr):
    base_job = Mock()
    base_attr = Mock()
    setattr(base_job, attr, base_attr)
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    delattr(job, attr)
    NOT_FOUND = Mock()
    assert getattr(job, attr, NOT_FOUND) is NOT_FOUND
    assert getattr(base_job, attr, NOT_FOUND) is base_attr


################################################################################
## DUMMY ABSTRACT METHOD IMPLEMENTATION
################################################################################
def test_submit(zne_strategy, target_num_experiments):
    base_job = Mock()
    SUBMITTED = Mock()
    base_job.submit = Mock(return_value=SUBMITTED)
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    submit = object.__getattribute__(job, "submit")  # Bypass nested delegation logic
    assert submit() is SUBMITTED


def test_status(zne_strategy, target_num_experiments):
    base_job = Mock()
    STATUS = Mock()
    base_job.status = Mock(return_value=STATUS)
    job = ZNEJob(base_job, zne_strategy, target_num_experiments)
    status = object.__getattribute__(job, "status")  # Bypass nested delegation logic
    assert status() is STATUS
