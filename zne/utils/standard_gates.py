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

"""Build dictionary library util."""

from qiskit.circuit import ControlledGate, Gate, QuantumCircuit


def build_method_to_gate_dict() -> dict:
    """Returns dictionary mapping gate names to gate classes."""
    method_to_gate = {}
    gates = Gate.__subclasses__() + ControlledGate.__subclasses__()
    for gate in gates:
        name = gate.__name__.lower()
        if name[-4:] == "gate":
            method = name[:-4]
            if hasattr(QuantumCircuit, method):
                method_to_gate[method] = gate
    return method_to_gate


STANDARD_GATES = frozenset(build_method_to_gate_dict())
