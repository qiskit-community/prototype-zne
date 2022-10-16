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

"""Build dictionary library util."""


def build_dict_library(*named_objects) -> dict:
    """Build dictionary library.

    Args:
        named_objects: A list of objects.

    Returns:
        A dictionary that maps object names (keys) to the objects themselves (values).

    Raises:
        TypeError: If any of the provided objects does not have the ``__name__`` attribute
        ValueError: If two or more objects with identical names were provided.
    """
    named_objects: set = set(named_objects)  # type: ignore
    if any(not hasattr(obj, "__name__") for obj in named_objects):
        raise TypeError("Provided name_objects must have a __name__ attribute.")
    object_names: set = {obj.__name__ for obj in named_objects}
    if len(named_objects) != len(object_names):
        raise ValueError("Distinct objects with identical names where provided.")
    return {obj.__name__: obj for obj in named_objects}
