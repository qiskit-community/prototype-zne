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

from test import NO_INTS, NO_REAL, TYPES
from unittest.mock import Mock, patch

from numpy.random import Generator, default_rng
from pytest import fixture, mark, raises, warns
from qiskit import QuantumCircuit

from zne.noise_amplification.folding_amplifier.global_folding_amplifier import (
    GlobalFoldingAmplifier,
)
from zne.noise_amplification.folding_amplifier.local_folding_amplifier import (
    LocalFoldingAmplifier,
)

MOCK_TARGET_PATH = "zne.noise_amplification.folding_amplifier.folding_amplifier.FoldingAmplifier"


@fixture(scope="module")
def patch_amplifier_with_multiple_mocks():
    def factory_method(**kwargs):
        return patch.multiple(MOCK_TARGET_PATH, **kwargs)

    return factory_method


@mark.parametrize(
    "NoiseAmplifier",
    (GlobalFoldingAmplifier, LocalFoldingAmplifier),
    ids=("GlobalFoldingAmplifier", "LocalFoldingAmplifier"),
)
class TestFoldingAmplifier:
    @fixture(scope="function")
    def setter_mocks(self):
        mocks = {
            "_set_sub_folding_option": Mock(),
            "_set_barriers": Mock(),
            "_prepare_rng": Mock(),
            "_set_noise_factor_relative_tolerance": Mock(),
        }
        return mocks

    ################################################################################
    ## INIT TESTS
    ################################################################################

    def test_init_default_kwargs(
        self, NoiseAmplifier, patch_amplifier_with_multiple_mocks, setter_mocks
    ):
        with patch_amplifier_with_multiple_mocks(**setter_mocks):
            NoiseAmplifier()
        setter_mocks["_set_sub_folding_option"].assert_called_once_with("from_first")
        setter_mocks["_set_barriers"].assert_called_once_with(True)
        setter_mocks["_prepare_rng"].assert_called_once_with(None)
        setter_mocks["_set_noise_factor_relative_tolerance"].assert_called_once_with(1e-2)

    def test_init_custom_kwargs(
        self, NoiseAmplifier, patch_amplifier_with_multiple_mocks, setter_mocks
    ):
        with patch_amplifier_with_multiple_mocks(**setter_mocks):
            NoiseAmplifier(
                sub_folding_option="random",
                barriers=False,
                random_seed=1,
                noise_factor_relative_tolerance=1e-1,
            )
        setter_mocks["_set_sub_folding_option"].assert_called_once_with("random")
        setter_mocks["_set_barriers"].assert_called_once_with(False)
        setter_mocks["_prepare_rng"].assert_called_once_with(1)
        setter_mocks["_set_noise_factor_relative_tolerance"].assert_called_once_with(1e-1)

    ################################################################################
    ## PROPERTIES and SETTER TESTS
    ################################################################################

    @mark.parametrize(
        "sub_folding_option",
        cases := ["from_last", "from_first", "random"],
        ids=[f"{c}" for c in cases],
    )
    def test_set_sub_folding_option(self, NoiseAmplifier, sub_folding_option):
        noise_amplifier = NoiseAmplifier()
        noise_amplifier._set_sub_folding_option(sub_folding_option)
        assert noise_amplifier.sub_folding_option == sub_folding_option

    @mark.parametrize(
        "sub_folding_option", [(t,) for t in TYPES], ids=[str(type(i).__name__) for i in TYPES]
    )
    def test_set_sub_folding_option_value_error(self, NoiseAmplifier, sub_folding_option):
        with raises(ValueError):
            NoiseAmplifier()._set_sub_folding_option(sub_folding_option)

    @mark.parametrize(
        "random_seed",
        cases := [1, 2],
        ids=[f"{c}" for c in cases],
    )
    def test_prepare_rng(self, NoiseAmplifier, random_seed):
        noise_amplifier = NoiseAmplifier()
        noise_amplifier._prepare_rng(random_seed)
        assert isinstance(noise_amplifier._rng, Generator)
        rng = default_rng(random_seed)
        assert noise_amplifier._rng.bit_generator.state == rng.bit_generator.state

    @mark.parametrize(
        "random_seed", [(t,) for t in NO_INTS], ids=[str(type(i).__name__) for i in NO_INTS]
    )
    def test_prepare_rng_type_error(self, NoiseAmplifier, random_seed):
        with raises(TypeError):
            NoiseAmplifier()._prepare_rng(random_seed)

    @mark.parametrize(
        "tolerance",
        cases := [0.1, 0.01],
        ids=[f"{c}" for c in cases],
    )
    def test_set_noise_factor_relative_tolerance(self, NoiseAmplifier, tolerance):
        noise_amplifier = NoiseAmplifier()
        noise_amplifier._set_noise_factor_relative_tolerance(tolerance)
        assert noise_amplifier._noise_factor_relative_tolerance == tolerance

    @mark.parametrize(
        "tolerance", [(t,) for t in NO_REAL], ids=[str(type(i).__name__) for i in NO_REAL]
    )
    def test_set_noise_factor_relative_tolerance_type_error(self, NoiseAmplifier, tolerance):
        with raises(TypeError):
            NoiseAmplifier()._set_noise_factor_relative_tolerance(tolerance)

    @mark.parametrize("warn_user", cases := [True, False], ids=[f"{c}" for c in cases])
    def test_set_warn_user(self, NoiseAmplifier, warn_user):
        noise_amplifier = NoiseAmplifier()
        noise_amplifier.warn_user = warn_user
        assert noise_amplifier.warn_user == warn_user

    @mark.parametrize(
        "warn_user",
        cases := [t for t in TYPES if not isinstance(t, bool)],
        ids=[str(type(c).__name__) for c in cases],
    )
    def test_set_warn_user_type_error(self, NoiseAmplifier, warn_user):
        noise_amplifier = NoiseAmplifier()
        with raises(TypeError):
            noise_amplifier.warn_user = warn_user

    @mark.parametrize(
        "barriers", cases := [True, False, 1, 0, "", "|"], ids=[f"{c}" for c in cases]
    )
    def test_set_barriers(self, NoiseAmplifier, barriers):
        noise_amplifier = NoiseAmplifier()
        noise_amplifier._set_barriers(barriers)
        assert noise_amplifier.barriers is bool(barriers)

    ################################################################################
    ## TESTS
    ################################################################################

    @mark.parametrize(
        "noise_factor",
        cases := [1, 1.2, 2, 3.5],
        ids=[f"{c}" for c in cases],
    )
    def test_validate_noise_factor(self, NoiseAmplifier, noise_factor):
        NoiseAmplifier()._validate_noise_factor(noise_factor)

    @mark.parametrize(
        "noise_factor",
        cases := [0, 0.5, -1, -2.5],
        ids=[f"{c}" for c in cases],
    )
    def test_validate_noise_factor_value_error(self, NoiseAmplifier, noise_factor):
        with raises(ValueError):
            NoiseAmplifier()._validate_noise_factor(noise_factor)

    @mark.parametrize(
        "folding, expected",
        cases := tuple(
            zip(
                [0, 1, 2],
                [1, 3, 5],
            )
        ),
        ids=[f"{f}-{e}" for f, e in cases],
    )
    def test_folding_to_noise_factor(self, NoiseAmplifier, folding, expected):
        assert NoiseAmplifier().folding_to_noise_factor(folding) == expected

    def test_warn_user_true(self, NoiseAmplifier):
        with warns(UserWarning):
            NoiseAmplifier().warn("warning")

    def test_warn_user_false(self, NoiseAmplifier):
        NoiseAmplifier(warn_user=False).warn("no warning")

    @mark.parametrize(
        "num_instructions, noise_factor, expected",
        cases := [
            (9, 1.2, (0, 1)),
            (9, 2, (0, 4)),
            (9, 3.6, (1, 3)),
            (9, 4, (1, 5)),
            (9, 17 / 3.0, (2, 3)),
            (9, 100, (49, 5)),
            (17, 1.2, (0, 2)),
            (17, 2, (0, 8)),
            (17, 3.6, (1, 5)),
            (17, 4, (1, 9)),
            (17, 100, (49, 9)),
        ],
        ids=[f"{ni}-{nf}-{cd}" for ni, nf, cd in cases],
    )
    @mark.filterwarnings("ignore::UserWarning")
    def test_compute_folding_nums(self, NoiseAmplifier, num_instructions, noise_factor, expected):
        assert NoiseAmplifier()._compute_folding_nums(noise_factor, num_instructions) == expected

    @mark.parametrize(
        "noise_factor",
        cases := [1.5, 3.05],
        ids=[f"{c}" for c in cases],
    )
    def test_compute_folding_nums_warning(self, NoiseAmplifier, noise_factor):
        with warns(UserWarning):
            assert NoiseAmplifier()._compute_folding_nums(noise_factor, 3)

    def test_compute_folding_no_foldings(self, NoiseAmplifier):
        with warns(UserWarning):
            assert NoiseAmplifier()._compute_folding_nums(3, 0) == (0, 0)

    @mark.parametrize("registers", [(), (0,), (1,), (0, 1)])
    def test_apply_barrier_true(self, NoiseAmplifier, registers):
        circuit = QuantumCircuit(2)
        original = circuit.copy()
        noise_amplifier = NoiseAmplifier(barriers=True)
        circuit = noise_amplifier._apply_barrier(circuit, *registers)
        last_instruction = circuit.data.pop()
        assert last_instruction.operation.name == "barrier"
        registers = [circuit.qubits[r] for r in registers] or circuit.qubits
        assert last_instruction.qubits == tuple(registers)
        assert circuit == original

    @mark.parametrize("registers", [(), (0,), (1,), (0, 1)])
    def test_apply_barrier_false(self, NoiseAmplifier, registers):
        circuit = QuantumCircuit(2)
        original = circuit.copy()
        noise_amplifier = NoiseAmplifier(barriers=False)
        circuit = noise_amplifier._apply_barrier(circuit, *registers)
        assert circuit == original
