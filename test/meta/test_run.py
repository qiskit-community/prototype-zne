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

from pytest import fixture, mark, raises

from zne.meta.job import ZNEJob
from zne.meta.run import zne_run
from zne.zne_strategy import ZNEStrategy


class TestZNERun:
    ################################################################################
    ## FIXTURES
    ################################################################################
    @fixture(scope="function")
    def self(_self):
        self = Mock()
        self.zne_strategy = ZNEStrategy()
        return self

    @fixture(scope="function")
    def run_options(_self):
        return {"Forrest": "Gump", "Charriots": "Fire"}

    ################################################################################
    ## TESTS
    ################################################################################
    def test_base_run_noop_zne_strategy(_self, self, run_options):
        base_run = Mock()
        run = zne_run(base_run)
        self.zne_strategy = ZNEStrategy(noise_factors=range(1, 4))
        _ = run(
            self,
            circuits="circuits",
            observables="observables",
            parameter_values="parameter_values",
            zne_strategy=None,
            **run_options,
        )
        base_run.assert_called_once_with(
            self,
            circuits="circuits",
            observables="observables",
            parameter_values="parameter_values",
            **run_options,
        )

    def test_base_run_default_zne_strategy(_self, self, run_options):
        base_run = Mock()
        run = zne_run(base_run)
        self.zne_strategy = ZNEStrategy(noise_factors=range(1, 4))
        build_noisy_circuits = Mock(return_value="noisy_circuits")
        self.zne_strategy.build_noisy_circuits = build_noisy_circuits
        map_to_noisy_circuits = Mock(side_effect=lambda x: "noisy_" + x)
        self.zne_strategy.map_to_noisy_circuits = map_to_noisy_circuits
        _ = run(
            self,
            circuits="circuits",
            observables="observables",
            parameter_values="parameter_values",
            **run_options,
        )
        build_noisy_circuits.assert_called_once_with("circuits")
        map_to_noisy_circuits.assert_any_call("observables")
        map_to_noisy_circuits.assert_any_call("parameter_values")
        assert map_to_noisy_circuits.call_count == 2
        base_run.assert_called_once_with(
            self,
            circuits="noisy_circuits",
            observables="noisy_observables",
            parameter_values="noisy_parameter_values",
            **run_options,
        )

    def test_base_run_custom_zne_strategy(_self, self, run_options):
        base_run = Mock()
        run = zne_run(base_run)
        zne_strategy = ZNEStrategy(noise_factors=range(1, 7))
        build_noisy_circuits = Mock(return_value="noisy_circuits")
        zne_strategy.build_noisy_circuits = build_noisy_circuits
        map_to_noisy_circuits = Mock(side_effect=lambda x: "noisy_" + x)
        zne_strategy.map_to_noisy_circuits = map_to_noisy_circuits
        _ = run(
            self,
            circuits="circuits",
            observables="observables",
            parameter_values="parameter_values",
            zne_strategy=zne_strategy,
            **run_options,
        )
        build_noisy_circuits.assert_called_once_with("circuits")
        map_to_noisy_circuits.assert_any_call("observables")
        map_to_noisy_circuits.assert_any_call("parameter_values")
        assert map_to_noisy_circuits.call_count == 2
        base_run.assert_called_once_with(
            self,
            circuits="noisy_circuits",
            observables="noisy_observables",
            parameter_values="noisy_parameter_values",
            **run_options,
        )

    def test_zne_strategy_type_error(_self, self, run_options):
        base_run = Mock()
        run = zne_run(base_run)
        with raises(TypeError):
            run(
                self,
                circuits="circuits",
                observables="observables",
                parameter_values="parameter_values",
                zne_strategy="zne_strategy",
                **run_options,
            )

    def test_zne_job(_self, self, run_options):
        base_run = Mock(return_value="job")
        run = zne_run(base_run)
        job = run(
            self,
            circuits="circuits",
            observables="observables",
            parameter_values="parameter_values",
            **run_options,
        )
        assert isinstance(job, ZNEJob)
        assert job.base_job == "job"
        assert job.zne_strategy is self.zne_strategy
        assert job.target_num_experiments == len("circuits")


@mark.parametrize("run", [None, Ellipsis, True, 0, 1.0, 1j, "run"])
def test_type_error(run):
    with raises(TypeError):
        zne_run(run)
