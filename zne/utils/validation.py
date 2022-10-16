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

from collections.abc import Sequence, Set
from typing import Any, Tuple, Union

IsInstanceTypes = Union[type, Tuple[Union[type, tuple], ...]]


################################################################################
## VALIDATION
################################################################################
def validate_object_type(
    obj: object,
    class_or_tuple: IsInstanceTypes,
    *,
    default: Any = Ellipsis,
) -> Any:
    """Validate type with same interface as ``isinstance``.

    Args:
        obj: The object to validate
        class_or_tuple: A type, tuple of types, or Union to validate against.
        default: If provided and ``obj`` is None return this instead (validated).

    Returns:
        The validated object or default.

    Raises:
        TypeError: If ``obj`` is not of a type specified in ``class_or_tuple``.
        TypeError: If ``class_or_tuple`` is incompatible with ``isinstance``.
    """
    if default is not ... and obj is None:  # Ellipsis avoids infinite recurssion
        return validate_object_type(default, class_or_tuple)
    try:
        if not isinstance(obj, class_or_tuple):
            raise TypeError(f"Expected {class_or_tuple} but got {type(obj)} instead.")
    except TypeError as error:
        raise TypeError("Invalid types provided: incompatible with ``isinstance``.") from error
    else:
        return obj


def validate_sequence(  # pylint: disable=too-many-arguments
    seq: Sequence,
    element_types: IsInstanceTypes = object,
    *,
    standard_type: type | None = None,
    cast_single: bool = False,
    allow_set: bool = False,
    default: Any = Ellipsis,
) -> Sequence:
    """Validate sequence and (optioanlly) the type of its elements.

    Args:
        seq: A sequence object ot validate.
        element_types: A type, tuple of types, or Union for the elements in the sequence.
        standard_type: A callable to cast the returned sequence to a standard type, or None.
        cast_single: If ``True``, allows single element input (casted to tuple).
        allow_set: If ``True``, ``Set`` objects will be allowed as sequences.
        default: If provided and ``seq`` is ``None`` return this instead (validated).
            Ellipsis (i.e. ``...``) disables the functinoality.

    Returns:
        The validated (casted) sequence or default.

    Raises:
        ValueError: If ``standard_type`` input fails to cast the return value's type.
    """
    ## DEFAULT
    if default is not ... and seq is None:  # Ellipsis avoids infinite recurssion
        return validate_sequence(
            default,
            element_types,
            standard_type=standard_type,
            cast_single=cast_single,
            allow_set=allow_set,
        )

    ## ALLOW SET
    SequenceType: IsInstanceTypes = (Sequence, Set) if allow_set else Sequence

    ## CAST SINGLE
    element_types = _validate_isinstance_types(element_types)
    if cast_single and isinstance(seq, element_types):
        # TODO: handle arbitrarily deep recursive sequences gracefully (now up to depth two)
        if not isinstance(seq, SequenceType) or any(not isinstance(e, element_types) for e in seq):
            seq = (seq,)

    ## VALIDATION
    validate_object_type(seq, SequenceType)
    for element in seq:
        validate_object_type(element, element_types)

    ## STANDARD TYPE
    if standard_type is not None:
        try:
            seq = standard_type(seq)
            return validate_sequence(seq, element_types, allow_set=allow_set)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Incompatible `standard_type` input, type casting cannot be performed."
            ) from error

    ## RETURN
    return seq


################################################################################
## AUXILIARY
################################################################################
def _validate_isinstance_types(types: IsInstanceTypes) -> tuple:
    """Validate that types are a valid second argument for ``isinstance`` call.

    Args:
        types: To validate.

    Returns:
        The input types if validated in tuple form.

    Raises:
        TypeError: If types are invalid.
    """
    try:
        isinstance(None, types)
    except TypeError as error:
        raise TypeError("Invalid types provided: incompatible with ``isinstance``.") from error
    else:
        if not isinstance(types, tuple):
            types = (types,)
        return types
