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

"""Validation utils module."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from .unset import UNSET, UnsetType


class quality:  # pylint: disable=invalid-name
    """Quality attribute similar to property but geared towards custom validation.

    Args:
        fval: function to be used for validating an attribute value on __set__
        feff: function to be used for perfomring side-effects on __set__ (e.g. erasing cache)
        default: value to assume if set to `...`
        null: value to assume if set to `None`
    """

    __slots__ = "fval", "feff", "_default", "_null", "name", "private_name"

    # TODO: update doc to fval's like property does for fget
    def __init__(
        self,
        fval: Callable[[Any, Any], Any] | None = None,
        feff: Callable[[Any], None] | None = None,
        *,
        default: Any = UNSET,
        null: Any = UNSET,
    ) -> None:
        self.fval = fval
        self.feff = feff
        self._default = default
        self._null = null

    def __call__(
        self,
        fval: Callable[[Any, Any], Any] | None | UnsetType = UNSET,
        feff: Callable[[Any], None] | None | UnsetType = UNSET,
        *,
        default: Any = UNSET,
        null: Any = UNSET,
    ) -> quality:
        """Returns a copy of the quality with updated attributes."""
        return self.__class__(
            fval=self.fval if fval is UNSET else fval,  # type: ignore
            feff=self.feff if feff is UNSET else feff,  # type: ignore
            default=self.default if default is UNSET else default,
            null=self.null if null is UNSET else null,
        )

    def __copy__(self) -> quality:
        return self.__class__(
            fval=self.fval,
            feff=self.feff,
            default=self.default,
            null=self.null,
        )

    def __deepcopy__(self, memo: dict) -> quality:
        fval = deepcopy(self.fval, memo)
        feff = deepcopy(self.feff, memo)
        default = deepcopy(self._default, memo)
        null = deepcopy(self._null, memo)
        return self.__class__(fval, feff, default=default, null=null)

    ################################################################################
    ## PROPERTIES
    ################################################################################
    @property
    def default(self) -> Any:
        """Default value for the managed attribute to be used for `...`.

        Enforced immutable to avoid side-effects.
        """
        return deepcopy(self._default)

    @property
    def null(self) -> Any:
        """Null value for the managed attribute to be used for `None`.

        Enforced immutable to avoid side-effects.
        """
        return deepcopy(self._null)

    ################################################################################
    ## DESCRIPTOR PROTOCOL
    ################################################################################
    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name  # pylint: disable=attribute-defined-outside-init
        self.private_name = f"_{name}"  # pylint: disable=attribute-defined-outside-init

    def __get__(self, obj: object, objtype: type = None) -> Any:
        if obj is None:
            return self
        if hasattr(obj, self.private_name):
            return getattr(obj, self.private_name)
        setattr(obj, self.name, UNSET)
        return getattr(obj, self.name)

    def __set__(self, obj: object, value: Any) -> None:
        value = self._apply_defaults(value)
        if self.fval is not None:
            value = self.fval(obj, value)
        setattr(obj, self.private_name, value)
        if self.feff is not None:
            self.feff(obj)

    def __delete__(self, obj: object) -> None:
        if hasattr(obj, self.private_name):
            delattr(obj, self.private_name)
        if self.feff is not None:
            self.feff(obj)

    ################################################################################
    ## DECORATORS
    ################################################################################
    def validator(self, fval: Callable[[Any, Any], Any] | None) -> quality:
        """Descriptor to obtain a copy of the quality with a different validator."""
        return self.__class__(
            fval=fval,
            feff=self.feff,
            default=self.default,
            null=self.null,
        )

    def side_effect(self, feff: Callable[[Any], None] | None) -> quality:
        """Descriptor to obtain a copy of the quality with a different side effect."""
        return self.__class__(
            fval=self.fval,
            feff=feff,
            default=self.default,
            null=self.null,
        )

    ################################################################################
    ## AUXILIARY
    ################################################################################
    def _apply_defaults(self, value: Any) -> Any:
        """Apply defaults to user input value."""
        default = self.null if self.default is UNSET else self.default
        null = default if self.null is UNSET else self.null
        if value is UNSET:
            value = None if default is UNSET else default
        elif value is Ellipsis and default is not UNSET:
            value = default
        elif value is None and null is not UNSET:
            value = null
        return value
