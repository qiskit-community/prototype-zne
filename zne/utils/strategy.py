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

"""Strategy design pattern tools.

This module provides support for strategy classes, which are similar in format and
spirit to those produced by the builtin :class:`dataclass` decorator. In this case,
the relevant information is extracted from the class' ``__init__`` method signature
rather than from class fields. Said class signature specifies the so called 'settings'
for the strategy, where arguments whose name begins with a leading ``_`` are excluded
from the settings namespace. Although not currently enforced, it is strongly suggested
for these excluded arguments to be optional (i.e. developers should provide defaults).

Init's arguments are referred to as 'init args', and are not subject to any namespace
exclusions. Similarly, construction-time init args (including defaults) are referred to
as 'original args': they are merely a reflection of the values of all arguments passed
to ``__init__`` when instantiating the given strategy object.

Currently, init arguments of kind POSITIONAL_ONLY, VAR_POSITIONAL, and VAR_KEYWORD
are disallowed. See https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind
for more information.

Strategy classes include the following specific mehods and fields:
    01. ``__init_subclass__``: to handle subclassing.
    02. ``__new__``: to save the original args at construction-time.
    03. ``__getattr__``: to retrieve original args via ``getattr`` (i.e. virtual attrs).
    04. ``__repr__``: a string representation of the strategy instance.
    05. ``__eq__``: to compare strategy instances.
    06. ``NAME``: the name of the strategy (i.e. class name).
    07. ``INIT_NAMESPACE``: a tuple of the strategy's settings names.
    08. ``SETTINGS_NAMESPACE``: a tuple of the strategy's settings names.
    09. ``settings``: a dictionary of settings and their corresponding values/states.
    10. ``init_args``: a dictionary of init arguments and their corresponding values/states.
    11. ``original_args``: a copy of the construction-time init args.
    12. ``is_facade``: to check is current class is a facade of a given ancestor.
    13. ``replicate``: to build replicas of any strategy instance with updated settings.

Out of these, {01, 02, 03} can extend and be extended, and {04, 05} can be overriden;
all others should be left unmodified.

Classes inheriting from a :class:`strategy` class, are strategy classes
themselves as well; with settings either inherited or provided by a new
``__init__`` method. This means that they do not need to be re-decorated.

Generally speaking, strategies are mutable, meaning that their settings
can be updated at runtime. The implicit assumption made by this decorator is
that the current state of all settings listed in ``SETTINGS_NAMESPACE`` can be
accessed through a ``getattr`` call. If any of these settings is not accessible
that way the corresponding (construction-time) init arg will be retrieved instead,
possibly leading to conflicts and runtime errors if mutated after instantiation.
If certain settings cannot be accessed by design, the suggested solution is
removing said settings from the settings namespace as explained before, or adding a
dummy property that retrieves their state (i.e. getter).

Oftentimes, developers will need their strategies to be immutable after instantiation.
To this end, the :class:`~zne.utils.strategy.strategy` decorator class accepts an
optional keyword argument ``frozen`` which, if set to ``True`` (default ``False``),
will forbid all ``setattr`` calls, and automatically return deepcopies of mutable
settings. In this scenario, settings will still be declared through the class'
``__init__`` method signature, while the body could be left blank (i.e. ``pass``),
hold the appropriate docstring, or used for validation among other things.

Replicas of any strategy instance can be produced by calling their
:method:`~zne.utils.strategy.strategy.replicate` method with updated settings
as keyword arguments. This is especially useful when dealing with frozen
(i.e. immutable) strategies.
"""

from __future__ import annotations

from abc import ABC
from copy import deepcopy
from inspect import Parameter, signature
from typing import Any

from .classconstant import classconstant
from .unset import UNSET


################################################################################
## CLASS DECORATOR
################################################################################
class strategy:  # pylint: disable=invalid-name
    """Strategy class decorator.

    Applies a strategy base class and its corresponding methods to the decorated class.

    This is done by dynamically subclassing from both the corresponding strategy base class
    (i.e. mutable or frozen), and the pre-decorated class as declared by the developer.
    The base strategy class will have precedence in the resulting class' mro; therefore,
    the resulting strategy class will extend the ``__init_subclass__``, ``__new__``, and
    ``__getattr__`` methods from the pre-decorated class. Additionally, in order to allow
    redefinition of the base strategy class' ``__init__`` (dummy), ``__repr__`` and ``__eq__``
    methods, if these are found in the pre-decorated class' dictionary, they will be bridged
    to the resulting class; effectively overriding the defaults. Similarly, ``__module__``,
    ``__name__``, ``__annotations__``, and ``__doc__``, will also be bridged from the
    pre-decorated class as is standard in decorators.

    Args:
        frozen: Whether to inherit from ``_BaseStrategy`` or ``_FrozenStrategy``.

    Example:
        >>> @strategy
        >>> class cls:
        >>>     def __init__(self, a, b, _c=None):
        >>>         pass
        >>> cls.mro()
        [__main__.cls, zne.utils.strategy._BaseStrategy, __main__.cls, object]

        >>> @strategy(frozen=True)
        >>> class cls:
        >>>     def __init__(self, a, b, _c=None):
        >>>         pass
        >>> cls.mro()
        [__main__.cls,
        zne.utils.strategy._FrozenStrategy,
        zne.utils.strategy._BaseStrategy,
        __main__.cls,
        object]
    """

    __slots__ = ("_frozen",)  # TODO: add `abstract` option

    OVERRIDING_NAMESPACE = (
        "__module__",
        "__annotations__",
        "__doc__",
        "__init__",
        "__repr__",
        "__eq__",
    )

    def __new__(cls, /, target: type = None, **kwargs) -> type | strategy:  # type: ignore
        """Return a decorated class or a strategy object capable of decorating."""
        self = super().__new__(cls)
        if target is None:
            return self  # Note: init auto-triggered for `strategy` return types
        return self(target, **kwargs)

    def __init__(self, /, *_, frozen: bool = False, **__) -> None:
        """Save decorator configuration."""
        self.frozen: bool = frozen

    def __call__(self, /, target: type, *, frozen: bool | None = None, **__) -> type:
        """Decorate target class."""
        frozen = self.frozen if frozen is None else frozen
        BaseStrategy = _FrozenStrategy if frozen else _BaseStrategy
        overriding_attrs = {
            attr: value
            for attr in self.OVERRIDING_NAMESPACE
            if (value := target.__dict__.get(attr, UNSET)) is not UNSET
        }
        return type(target.__name__, (BaseStrategy, target), overriding_attrs)

    @property
    def frozen(self) -> bool:
        """Frozen strategy."""
        return getattr(self, "_frozen", False)

    @frozen.setter
    def frozen(self, value: bool) -> None:
        self._frozen: bool = bool(value)


################################################################################
## AUXILIARY
################################################################################
def _pack_init_args(obj: object, *args, **kwargs) -> dict[str, Any]:
    """Packs object init options as a dict, binding missing kwargs with defaults.

    Args:
        obj: the object whose `__init__` method to inspect.
        args, kwargs: the particular values passed on to the `__init__` method.

    Returns:
        A dictionary sorted by signature, where keys are argument names,
        and values are either those provided or the `__init__` defaults.

    Note:
        Dictionaries keep insertion order as a langauage feature from Python 3.7.
        https://stackoverflow.com/questions/39980323/are-dictionaries-ordered-in-python-3-6#answers
    """
    init_signature = signature(obj.__init__)  # type: ignore
    bound_signature = init_signature.bind(*args, **kwargs)
    bound_signature.apply_defaults()
    bound_args = bound_signature.arguments  # Note: type `OrderedDict`
    return dict(bound_args)


def _infer_init_namespace(cls: type) -> tuple[str, ...]:
    """Infer init namespace from a given class."""
    init_signature = signature(cls.__init__)  # type: ignore
    namespace = tuple(init_signature.parameters.keys())
    return namespace[1:]  # Note: disregard `self`


def _infer_settings_namespace(cls: type) -> tuple[str, ...]:
    """Infer strategy settings namespace from a given class."""
    if cls.__init__ is object.__init__:  # type: ignore
        return ()  # Note: to avoid `*(*kw)args` from `object.__init__`
    init_namespace: tuple[str, ...] = _infer_init_namespace(cls)
    return tuple(name for name in init_namespace if not name.startswith("_"))


def _closest_common_ancestor(*args) -> type:
    """Retrieve closest common ancestor class from the input classes' MROs.

    Note: metaclasses are not supported, ``object`` is always shared.
    """
    cls_list = map(lambda obj: obj if isinstance(obj, type) else type(obj), args)
    mros = [cls.mro() for cls in cls_list]
    base = min(mros, key=len)
    mros.remove(base)
    for cls in base:
        if all(cls in mro for mro in mros):
            return cls
    return None  # Note: safeguard, `object` always shared (never called)  # pragma: no cover


def _shared_strategy_ancestor(*strategies) -> type:
    """Return closest common strategy ancestor or None."""
    shared: type = _closest_common_ancestor(*strategies)
    if shared in (None, *_BASE_STRATEGY_CLASSES) or not issubclass(shared, _BaseStrategy):
        return None
    return shared


################################################################################
## BASE STRATEGY CLASSES
################################################################################
class _BaseStrategy:
    """Strategy base class.

    Note: this class is not meant to be instantiated or inherited directly.
    """

    # TODO: subscriptable classconstant types (e.g. `classconstant[str]`)
    NAME: classconstant  # str
    INIT_NAMESPACE: classconstant  # tuple[str]
    SETTINGS_NAMESPACE: classconstant  # tuple[str]

    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        cls._validate_init()
        cls.NAME = classconstant(cls.__name__)
        cls.INIT_NAMESPACE = classconstant(_infer_init_namespace(cls))
        cls.SETTINGS_NAMESPACE = classconstant(_infer_settings_namespace(cls))

    def __new__(cls, *args, **kwargs) -> _BaseStrategy:
        # Note: logic added to `__new__` to avoid making `super().__init__` mandatory
        self = super().__new__(cls)
        self._original_args = _pack_init_args(self, *args, **kwargs)  # type: ignore
        return self

    def __init__(self) -> None:
        pass  # Note: dummy, to avoid `*(*kw)args` from `object.__init__`

    def __getattr__(self, name: str) -> Any:
        try:
            return super().__getattr__(name)  # type: ignore
        except (AttributeError, TypeError):
            original_args = getattr(self, "_original_args", {})
            attr = original_args.get(name, UNSET)
        if attr is UNSET:
            raise AttributeError(f"'{type(self)}' object has no attribute '{name}'")
        return deepcopy(attr)

    def __repr__(self) -> str:
        strategy_name: str = type(self).__name__
        settings_str = ", ".join(f"{key}={value!r}" for key, value in self.settings.items())
        return f"{strategy_name}({settings_str})" if settings_str else strategy_name

    def __eq__(self, other: object) -> bool:
        cls: type = _shared_strategy_ancestor(self, other)
        if cls is None or not self.is_facade(cls) or not other.is_facade(cls):  # type: ignore
            return False
        SHARED_NAMESPACE = cls.SETTINGS_NAMESPACE  # type: ignore # pylint: disable=invalid-name
        self_settings = {name: getattr(self, name, UNSET) for name in SHARED_NAMESPACE}
        other_settings = {name: getattr(other, name, UNSET) for name in SHARED_NAMESPACE}
        return self_settings == other_settings

    @property
    def settings(self) -> dict[str, Any]:
        """Strategy settings."""
        return {key: getattr(self, key) for key in self.SETTINGS_NAMESPACE}

    @property
    def init_args(self) -> dict[str, Any]:
        """Strategy init args."""
        return {key: getattr(self, key) for key in self.INIT_NAMESPACE}

    @property
    def original_args(self) -> dict[str, Any]:
        """A copy of original args."""
        original_args = getattr(self, "_original_args", {})
        return deepcopy(original_args)

    @classmethod
    def is_facade(cls, ancestor: Any) -> bool:
        """Checks if the strategy class is a facade subclass of the given ancestor."""
        if not isinstance(ancestor, type):
            ancestor = type(ancestor)
        if not (issubclass(cls, ancestor) and issubclass(ancestor, _BaseStrategy)):
            return False  # Note: subclassing is transitive (A -> B -> C then A -> C)
        filtered_mro = list(filter(lambda cls: issubclass(cls, ancestor), cls.mro()))
        for facade, parent in zip(filtered_mro, filtered_mro[1:]):
            if set(facade.SETTINGS_NAMESPACE) - set(parent.SETTINGS_NAMESPACE):  # type: ignore
                return False
        return True

    def replicate(self, **kwargs) -> _BaseStrategy:
        """Build a replica of the current strategy altering the specified settings."""
        init_args = deepcopy(self.init_args)
        init_args.update(kwargs)
        return type(self)(**init_args)

    @classmethod
    def _validate_init(cls):
        """Validate init method.

        Raises:
            TypeError: if POSITIONAL_ONLY, VAR_POSITIONAL, or VAR_KEYWORD arguments.
        """
        init_signature = signature(cls.__init__)
        parameters = init_signature.parameters.values()
        kinds = tuple(p.kind for p in parameters)[1:]  # Note: disregard `self`
        disallowed = {Parameter.POSITIONAL_ONLY, Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}
        for kind in kinds:
            if kind in disallowed:
                raise TypeError(
                    f"Invalid __init__ method in strategy class <{cls.__name__}>: "
                    f"{kind} arguments disallowed."
                )


# TODO
class _BaseStrategyABC(_BaseStrategy, ABC):
    """Strategy abstract base class.

    Note: this class is not meant to be instantiated or inherited directly.
    """


# TODO
class _FrozenStrategy(_BaseStrategy):
    """Frozen (immutable) strategy base class.

    Note: this class is not meant to be instantiated or inherited directly.
    """


# TODO
class _FrozenStrategyABC(_FrozenStrategy, ABC):
    """Frozen (immutable) strategy abstract base class.

    Note: this class is not meant to be instantiated or inherited directly.
    """


_BASE_STRATEGY_CLASSES: set[type] = {
    _BaseStrategy,
    _BaseStrategyABC,
    _FrozenStrategy,
    _FrozenStrategyABC,
}
