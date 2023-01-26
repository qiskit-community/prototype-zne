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

from os.path import join as join_path
from tempfile import TemporaryDirectory

from numpy import array
from pytest import mark, raises
from qiskit.primitives import EstimatorResult

from zne.utils.serialization import (
    DumpEncoder,
    EstimatorResultEncoder,
    NumPyEncoder,
    ReprEncoder,
)


@mark.parametrize(
    "obj, expected",
    [
        (0, "0"),
        ([0], "[0]"),
        ((0,), "[0]"),
        ([0, 1], "[0, 1]"),
        ((0, 1), "[0, 1]"),
        (["0", "1"], '["0", "1"]'),
        (("0", "1"), '["0", "1"]'),
        ([[], 1], "[[], 1]"),
        (([], 1), "[[], 1]"),
        ([[0], 1], "[[0], 1]"),
        (([0], 1), "[[0], 1]"),
        ({"key": "value"}, '{"key": "value"}'),
        ({0: 1}, '{"0": 1}'),
        ({0: (1,)}, '{"0": [1]}'),
        ({0: [1]}, '{"0": [1]}'),
    ],
)
class TestDumpEncoder:
    def test_dump(self, obj, expected):
        with TemporaryDirectory() as tmpdir:
            file_path = join_path(tmpdir, "zne-dump")
            DumpEncoder.dump(obj, file=file_path)
            with open(file_path) as f:
                contents = f.read()
            assert contents == expected

    def test_dumps(self, obj, expected):
        assert DumpEncoder.dumps(obj) == expected


class TestReprEncoder:
    @mark.parametrize(
        "repr_str",
        cases := [
            "",
            "dummy",
            "some spaces here",
            "`~!@#$%^&*()-_=+[]\\\"{}|;:',<.>/?",
        ],
        ids=cases,
    )
    def test_default(self, repr_str):
        class DummyRepr:
            def __repr__(self):
                return repr_str

        obj = DummyRepr()
        enc = ReprEncoder()
        assert enc.default(obj) == repr(obj)


class TestNumPyEncoder:
    @mark.parametrize(
        "array_like",
        cases := [
            [0, 1, 2],
            (0, 1, 2),
        ],
        ids=[type(c) for c in cases],
    )
    def test_default(self, array_like):
        a = array(array_like)
        enc = NumPyEncoder()
        assert enc.default(a) == a.tolist()

    def test_default_type_error(self):
        with raises(TypeError):
            _ = NumPyEncoder().default({"call": "super"})


class TestEstimatorResultEncoder:
    @mark.parametrize(
        "values, metadata",
        zip(
            [
                array([]),
                array([1]),
                array([1, 2]),
            ],
            [
                [],
                [{"variance": 0}],
                [{"variance": 0}, {"variance": 1}],
            ],
        ),
    )
    def test_default(self, values, metadata):
        result = EstimatorResult(values=values, metadata=metadata)
        enc = EstimatorResultEncoder()
        assert enc.default(result) == {"values": result.values, "metadata": result.metadata}

    def test_numpy_subclass(self):
        enc = EstimatorResultEncoder()
        assert isinstance(enc, NumPyEncoder)
        a = array([0, 1, 2])
        assert enc.default(a) == a.tolist()

    def test_repr_subclass(self):
        enc = EstimatorResultEncoder()
        assert isinstance(enc, ReprEncoder)
        obj = {"call": "super"}
        assert enc.default(obj) == repr(obj)
