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

from pytest import mark, raises

from zne.meta.call import zne_call


################################################################################
## DECORATOR
################################################################################
def test_zne_call():
    call = zne_call(Mock())
    with raises(TypeError):
        call("self", "circuits", "observables")


@mark.parametrize("call", [None, Ellipsis, True, 0, 1.0, 1j, "call"])
def test_type_error(call):
    with raises(TypeError):
        zne_call(call)
