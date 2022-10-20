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

"""ZNE meta programming capabilities.

Enables injecting error mitigation functionility to classes implementing the
:class:`qiskit.primitives.BaseEstimator` interface.
"""

from __future__ import annotations

from qiskit.primitives import BaseEstimator

from zne.meta.call import zne_call
from zne.meta.init import zne_init
from zne.meta.run import zne_run
from zne.zne_strategy import ZNEStrategy


def zne(cls: BaseEstimator) -> BaseEstimator:  # TODO: integration tests
    """Add ZNE functionality to input class.

    Args:
        cls: class implementing the :class:`qiskit.primitives.BaseEstimator` interface.

    Returns:
        A subclass of the input class extended with ZNE functionality.
    """
    if not isinstance(cls, type) or not issubclass(cls, BaseEstimator):
        raise TypeError("Invalid class, does not implement the BaseEstimator interface.")
    clz: BaseEstimator = type(f"ZNE{cls.__name__}", (cls,), {})
    clz.__init__ = zne_init(clz.__init__)  # TODO: update docstring
    clz.__call__ = zne_call(clz.__call__)  # TODO: deprecate
    clz._run = zne_run(clz._run)  # pylint: disable=protected-access
    clz.zne_strategy = property(_get_zne_strategy, _set_zne_strategy)
    return clz


def _get_zne_strategy(self) -> ZNEStrategy:
    try:
        return self._zne_strategy  # pylint: disable=protected-access
    except AttributeError:
        self.zne_strategy = None
        return self.zne_strategy


def _set_zne_strategy(self, zne_strategy: ZNEStrategy | None) -> None:
    if zne_strategy is None:
        zne_strategy = ZNEStrategy.noop()
    elif not isinstance(zne_strategy, ZNEStrategy):
        raise TypeError("Invalid zne_strategy object, expected ZNEStrategy.")
    self._zne_strategy = zne_strategy  # pylint: disable=protected-access
