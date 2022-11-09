# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from zne import __version__


def test_version():
    assert __version__ == "1.0.0"


################################################################################
## DEFINITIONS
################################################################################
TYPES = [
    INT := 0,
    FLOAT := 0.0,
    NAN := float("NaN"),
    INF := float("Inf"),
    MINF := float("-Inf"),
    COMPLEX := complex(0, 0),
    STR := "0",
    BOOL := True,
    NONE := None,
    LST := [0],
    TPL := (0,),
    DICT := {0: 0},
]
NO_INTS = [t for t in TYPES if type(t) != type(INT)]
NO_NONE = [t for t in TYPES if type(t) != type(NONE)]
NO_INTS_NONE = [t for t in NO_INTS if type(t) != type(NONE)]
NO_REAL = [t for t in NO_INTS if type(t) != type(FLOAT) or t in (NAN, INF, MINF)]
NO_NUM = [t for t in NO_REAL if type(t) != type(COMPLEX)]
ITERS = [t for t in TYPES if t in [STR, LST, TPL, DICT]]
NO_ITERS = [t for t in TYPES if t not in ITERS]
NO_ITERS_NONE = [t for t in NO_ITERS if type(t) != type(NONE)]


################################################################################
## ALL
################################################################################
__all__ = [
    "TYPES",
    "NO_INTS",
    "NO_INTS_NONE",
    "NO_REAL",
    "NO_NUM",
    "ITERS",
    "NO_ITERS",
]
