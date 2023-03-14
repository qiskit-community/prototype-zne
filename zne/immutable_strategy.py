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

"""ZNE strategy class to provide common base functionality."""

from __future__ import annotations

from inspect import signature
from typing import Any


class ImmutableStrategy:  # Note: pending deprecation  # pragma: no cover
    """Immutable strategy class to provide common base functionality.

    Note that all :class:`ImmutableStrategy` instance objects and their attributes are immutable by
    construction. If another strategy with different options needs to be utilized, a new instance
    of the class should be created.
    """

    def __new__(cls, *args, **kwargs) -> ImmutableStrategy:
        """ZNE strategy constructor."""
        self = super().__new__(cls)
        self.__dict__.update({"_init_options": {}})
        self._save_init_options(*args, **kwargs)
        return self

    def _save_init_options(self, *args, **kwargs) -> None:
        """Saves strategy init options as a dict."""
        init_signature = signature(self.__init__)  # type: ignore
        bound_signature = init_signature.bind(*args, **kwargs)
        bound_signature.apply_defaults()
        bound_args = bound_signature.arguments
        self._init_options: dict = dict(sorted(bound_args.items()))

    def __init__(self) -> None:
        """Base init method with no arguments, can be overriden."""

    @property
    def name(self) -> str:
        """Strategy name."""
        return type(self).__name__

    @property
    def options(self) -> dict:
        """Strategy options."""
        return self._init_options

    def __repr__(self) -> str:
        return f"<{self.name}:{self.options}>" if self.options else self.name

    def __eq__(self, other: Any) -> bool:
        return repr(self) == repr(other)
