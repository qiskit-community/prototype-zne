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

"""Serialization utils module."""

from __future__ import annotations

from datetime import datetime
from json import JSONEncoder, dump, dumps
from typing import Any

from numpy import ndarray
from qiskit.primitives import EstimatorResult


class DumpEncoder(JSONEncoder):
    """JSON encoder with extra methods for dumping."""

    @classmethod
    def dump(
        cls,
        obj: Any,
        file: str | None = None,
        indent: int | None = None,
    ) -> None:
        """Dump object to file using self as JSON encoder."""
        if file is None:  # pragma: no cover
            file = f"{datetime.utcnow().isoformat()}Z.json"
        with open(file, "w", encoding="utf8") as fp:  # pylint: disable=invalid-name
            return dump(obj, fp, indent=indent, cls=cls)

    @classmethod
    def dumps(cls, obj: Any, indent: int | None = None) -> str:
        """Dump object to string using self as JSON encoder."""
        return dumps(obj, indent=indent, cls=cls)


class ReprEncoder(DumpEncoder):
    """JSON encoder that falls back to `repr` if TypeError is raised."""

    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return repr(o)


class NumPyEncoder(DumpEncoder):
    """JSON encoder for NumPy's :class:`numpy.ndarray` objects."""

    def default(self, o):
        if isinstance(o, ndarray):
            return o.tolist()
        return super().default(o)


class EstimatorResultEncoder(NumPyEncoder, ReprEncoder):
    """JSON encoder for :class:`EstimatorResult` objects."""

    def default(self, o):
        if isinstance(o, EstimatorResult):
            return {"values": o.values, "metadata": o.metadata}
        return super().default(o)
