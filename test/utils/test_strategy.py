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

from zne.utils.strategy import (
    _BaseStrategy,
    _closest_common_ancestor,
    _FrozenStrategy,
    _infer_init_namespace,
    _infer_settings_namespace,
    _pack_init_args,
    _shared_strategy_ancestor,
    strategy,
)


################################################################################
## TEST CASES
################################################################################
def general_ancestry():
    """Generate test cases for general common ancestry.

    Returns:
        A three-tuple holding the two classes to compare and the common ancestor class.
    """
    cls = type("cls", (), {})
    clz = type("clz", (), {})
    A = type("A", (cls,), {})
    B = type("B", (cls,), {})
    AA = type("AA", (A,), {})
    AB = type("AB", (A,), {})
    yield cls, int, object
    yield cls, clz, object
    yield cls, A, cls
    yield A, B, cls
    yield AA, B, cls
    yield AA, AB, A


def strategy_ancestry():
    """Generate test cases for strategy common ancestry.

    Returns:
        A three-tuple holding the two classes to compare and the common strategy ancestor.
    """
    # TODO: _FrozenStrategy
    NonStrategy = type("NonStrategy", (), {})
    cls = type("cls", (_BaseStrategy,), {})
    clz = type("clz", (_BaseStrategy,), {})
    A = type("A", (cls,), {})
    B = type("B", (cls,), {})
    AA = type("AA", (A,), {})
    AB = type("AB", (A,), {})
    yield cls, int, None
    yield cls, NonStrategy, None
    yield cls, clz, None
    yield cls, A, cls
    yield A, B, cls
    yield AA, B, cls
    yield AA, AB, A


def strategy_facades():
    """Generate test cases for strategy facades.

    Returns:
        A three-tuple holding the two classes to compare and whether the former is
        a facade of the latter.
    """
    NonStrategy = type("NonStrategy", (), {"__init__": lambda self, a, b: None})
    cls = type("cls", (_BaseStrategy,), {"__init__": lambda self, a, b: None})
    clz = type("clz", (_BaseStrategy,), {"__init__": lambda self, a, b: None})
    subcls = type("subcls", (cls,), {"__init__": lambda self, a, b: None})
    c_setting = type("c_setting", (cls,), {"__init__": lambda self, a, b, c: None})
    c_arg = type("c_arg", (cls,), {"__init__": lambda self, a, b, _c: None})
    A = type("A", (cls,), {"__init__": lambda self, a: None})
    B = type("B", (cls,), {"__init__": lambda self, b: None})
    C = type("C", (cls,), {"__init__": lambda self, c: None})
    _C = type("_C", (cls,), {"__init__": lambda self, _c: None})
    AA = type("AA", (A,), {"__init__": lambda self: None})
    AB = type("AB", (A,), {"__init__": lambda self, a, b: None})
    ABA = type("ABA", (AB,), {"__init__": lambda self, a: None})
    CA = type("AA", (C,), {"__init__": lambda self: None})
    yield cls, NonStrategy, False  # Non-strategy
    yield clz, cls, False  # Different strategies
    yield cls, cls, True  # Self facade
    yield subcls, cls, True  # Same settings facade
    yield c_setting, cls, False  # New setting
    yield c_arg, cls, True  # New excluded
    yield A, cls, True  # Simple facade
    yield B, cls, True  # Other facade
    yield C, cls, False  # Generalization
    yield _C, cls, True  # Excluded arg
    yield AA, cls, True  # Sub-facade
    yield CA, cls, False  # Intermediate generalization
    yield ABA, cls, False  # Local generalization


################################################################################
## CLASS DECORATOR
################################################################################
class TestClassDecorator:
    """Test strategy class decorator."""

    def test_new(self):
        """Test new."""
        decorator = strategy()
        assert isinstance(decorator, strategy)
        cls = type("cls", (), {})
        decorator = strategy(cls)
        assert not isinstance(decorator, strategy)
        assert issubclass(decorator, cls)
        assert issubclass(decorator, _BaseStrategy)
        assert not issubclass(decorator, _FrozenStrategy)
        decorator = strategy(cls, frozen=True)
        assert not isinstance(decorator, strategy)
        assert issubclass(decorator, cls)
        assert issubclass(decorator, _BaseStrategy)
        assert issubclass(decorator, _FrozenStrategy)

    def test_init(self):
        """Test init."""
        decorator = strategy()
        assert decorator.frozen is False
        decorator = strategy(frozen=True)
        assert decorator.frozen is True
        decorator = strategy(frozen=False)
        assert decorator.frozen is False

    def test_call(self):
        """Test call."""
        decorator = strategy()
        ## PLAIN STRATEGY
        cls = type("cls", (), {})
        strategy_class = decorator(cls)
        assert issubclass(strategy_class, cls)
        assert issubclass(strategy_class, _BaseStrategy)
        assert not issubclass(strategy_class, _FrozenStrategy)
        assert strategy_class.__init__ is not object.__init__
        strategy_class = decorator(cls, frozen=True)
        assert issubclass(strategy_class, cls)
        assert issubclass(strategy_class, _BaseStrategy)
        assert issubclass(strategy_class, _FrozenStrategy)
        assert strategy_class.__init__ is not object.__init__
        ## NAME
        name = "NAME"
        cls = type(name, (), {})
        assert decorator(cls).__name__ is name
        ## OVERRIDING MODULE
        module = "MODULE"
        cls = type("cls", (), {"__module__": module})
        assert decorator(cls).__module__ is module
        # OVERRIDING ANNOTATIONS
        annotations = {"annotation": ...}
        cls = type("cls", (), {"__annotations__": annotations})
        assert decorator(cls).__annotations__ is annotations
        ## OVERRIDING DOC
        doc = "DOCSTRING"
        cls = type("cls", (), {"__doc__": doc})
        assert decorator(cls).__doc__ is doc
        ## OVERRIDING INIT
        init = lambda self: None
        cls = type("cls", (), {"__init__": init})
        assert decorator(cls).__init__ is init
        ## OVERRIDING REPR
        repr = lambda self: "STRATEGY-REPR"
        cls = type("cls", (), {"__repr__": repr})
        assert decorator(cls).__repr__ is repr
        ## OVERRIDING EQ
        eq = lambda self, other: self is other
        cls = type("cls", (), {"__eq__": eq})
        assert decorator(cls).__eq__ is eq
        ## EXTENDING INIT SUBCLASS
        super_call = Mock()
        cls = type("cls", (), {"__init_subclass__": super_call})
        _ = decorator(cls)
        super_call.assert_called_once()
        ## EXTENDING NEW
        super_call = Mock()
        cls = type("cls", (), {"__new__": super_call})
        _ = decorator(cls)()
        super_call.assert_called_once()
        ## EXTENDING GETATTR
        super_call = Mock()
        cls = type("cls", (), {"__getattr__": super_call})
        getattr(decorator(cls)(), "attr")
        super_call.assert_called_once()

    def test_frozen(self):
        """Test frozen property."""
        decorator = strategy()
        assert decorator.frozen is False
        decorator.frozen = True
        assert decorator.frozen is True
        decorator.frozen = False
        assert decorator.frozen is False
        decorator.frozen = 1
        assert decorator.frozen is True
        decorator.frozen = {}
        assert decorator.frozen is False


################################################################################
## AUXILIARY
################################################################################
@mark.parametrize(
    "init, kwargs",
    [
        (lambda self: None, {}),
        (lambda self, a: None, {"a": 0}),
        (lambda self, a, b: None, {"a": 0, "b": 1}),
        (lambda self, a, b, c: None, {"a": 0, "b": 1, "c": 2}),
    ],
)
def test_pack_init_args(init, kwargs):
    """Test init args packing logic."""
    cls = type("cls", (), {"__init__": init})
    obj = cls(**kwargs)
    assert _pack_init_args(obj, **kwargs) == kwargs  # keyword
    assert _pack_init_args(obj, *kwargs.values()) == kwargs  # positional
    if len(kwargs) > 1:
        pos = tuple(v for v in tuple(kwargs.values())[: len(kwargs) // 2])
        kw = {k: v for k, v in tuple(kwargs.items())[len(kwargs) // 2 :]}
        assert _pack_init_args(obj, *pos, **kw) == kwargs  # positional + keyword


@mark.parametrize(
    "init, namespace",
    [
        (lambda self: None, ()),
        (lambda self, a: None, ("a",)),
        (lambda self, a, b: None, ("a", "b")),
        (lambda self, a, b, c: None, ("a", "b", "c")),
    ],
)
def test_infer_init_namesapce(init, namespace):
    """Test init namespace inferance."""
    cls = type("cls", (), {"__init__": init})
    assert _infer_init_namespace(cls) == namespace


@mark.parametrize(
    "init, settings",
    [
        (object.__init__, ()),
        (lambda self: None, ()),
        (lambda self, a: None, ("a",)),
        (lambda self, _a: None, ()),
        (lambda self, a, b: None, ("a", "b")),
        (lambda self, a, _b: None, ("a",)),
        (lambda self, _a, b: None, ("b",)),
        (lambda self, _a, _b: None, ()),
        (lambda self, a, _b, c: None, ("a", "c")),
    ],
)
def test_infer_settings_namesapce(init, settings):
    """Test settings namespace inferance."""
    cls = type("cls", (), {"__init__": init})
    assert _infer_settings_namespace(cls) == settings


@mark.parametrize("cls_A, cls_B, ancestor", [*general_ancestry()])
def test_closest_common_ancestor(cls_A, cls_B, ancestor):
    """Test closest common ancestor retrieval."""
    assert _closest_common_ancestor(cls_A, cls_B) is ancestor
    assert _closest_common_ancestor(cls_B, cls_A) is ancestor
    assert _closest_common_ancestor(cls_A(), cls_B) is ancestor
    assert _closest_common_ancestor(cls_B, cls_A()) is ancestor
    assert _closest_common_ancestor(cls_A, cls_B()) is ancestor
    assert _closest_common_ancestor(cls_B(), cls_A) is ancestor
    assert _closest_common_ancestor(cls_A(), cls_B()) is ancestor
    assert _closest_common_ancestor(cls_B(), cls_A()) is ancestor


@mark.parametrize("cls_A, cls_B, ancestor", [*strategy_ancestry()])
def test_shared_strategy_ancestor(cls_A, cls_B, ancestor):
    """Test strategy ancestor retrieval."""
    assert _shared_strategy_ancestor(cls_A, cls_B) is ancestor
    assert _shared_strategy_ancestor(cls_B, cls_A) is ancestor
    assert _shared_strategy_ancestor(cls_A(), cls_B) is ancestor
    assert _shared_strategy_ancestor(cls_B, cls_A()) is ancestor
    assert _shared_strategy_ancestor(cls_A, cls_B()) is ancestor
    assert _shared_strategy_ancestor(cls_B(), cls_A) is ancestor
    assert _shared_strategy_ancestor(cls_A(), cls_B()) is ancestor
    assert _shared_strategy_ancestor(cls_B(), cls_A()) is ancestor


################################################################################
## STRATEGY CLASSES
################################################################################
@mark.parametrize(
    "init, namespace",
    [
        (lambda self: None, ()),
        (lambda self, foo: None, ("foo",)),
        (lambda self, _bar: None, ("_bar",)),
        (lambda self, foo, _bar: None, ("foo", "_bar")),
        (lambda self, foo, bar: None, ("foo", "bar")),
        (lambda self, _foo, _bar: None, ("_foo", "_bar")),
    ],
)
class TestStrategy:
    """Test Strategy class."""

    @mark.parametrize("cls_name", ["cls", "Class", "Klass"])
    def test_init_subclass(self, cls_name, init, namespace):
        """Test subclassing logic."""
        settings = tuple(n for n in namespace if not n.startswith("_"))
        cls = type(cls_name, (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        assert hasattr(cls, "NAME")
        assert cls.NAME == obj.NAME == cls_name
        assert hasattr(cls, "INIT_NAMESPACE")
        assert isinstance(cls.INIT_NAMESPACE, tuple)
        assert cls.INIT_NAMESPACE is obj.INIT_NAMESPACE
        assert cls.INIT_NAMESPACE == tuple(namespace)
        assert hasattr(cls, "SETTINGS_NAMESPACE")
        assert isinstance(cls.SETTINGS_NAMESPACE, tuple)
        assert cls.SETTINGS_NAMESPACE is obj.SETTINGS_NAMESPACE
        assert cls.SETTINGS_NAMESPACE == tuple(settings)

    def test_new(self, init, namespace):
        """Test constructor logic."""
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        assert hasattr(obj, "_original_args")
        assert obj._original_args == kwargs

    def test_getattr(self, init, namespace):
        """Test getattr."""
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        for n, attr in enumerate(namespace):
            assert getattr(obj, attr) == n
        for attr in ("non_attr", "error"):
            with raises(AttributeError):
                getattr(obj, attr)

    def test_super_getattr(self, init, namespace):
        """Test extending getattr."""
        _super = type("super", (), {"__getattr__": lambda self, attr: attr})
        cls = type("cls", (_BaseStrategy, _super), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        for attr in ("non_attr", "error"):
            assert getattr(obj, attr) == attr
        for _, attr in enumerate(namespace):
            assert getattr(obj, attr) == attr

    def test_repr(self, init, namespace):
        """Test string representation."""
        settings = tuple(n for n in namespace if not n.startswith("_"))
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        cls_name = cls.__name__
        settings_str = ", ".join(f"{s}={getattr(obj, s)}" for s in settings)
        str_repr = f"{cls_name}({settings_str})" if settings_str else cls_name
        assert str(obj) == repr(obj) == str_repr

    def test_eq(self, init, namespace):
        """Test basic equality (same class, different settings).

        Note: checks reflexivity, symmetry, and transitivity.
        """
        settings = tuple(n for n in namespace if not n.startswith("_"))
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        copy = cls(**kwargs)
        assert obj == obj  # Reflexivity
        assert obj == copy == obj  # Symmetry
        assert obj == copy == cls(**kwargs) == obj  # Transitivity
        if settings:  # Different settings
            kwargs = {name: i + 1 for i, name in enumerate(namespace)}
            assert cls(**kwargs) != obj

    def test_settings(self, init, namespace):
        """Test settings property."""
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        settings = tuple(n for n in namespace if not n.startswith("_"))
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        assert obj.settings == {n: i for i, n in enumerate(namespace) if n in settings}
        for n in settings:
            setattr(obj, n, n)
            assert obj.settings.get(n) == getattr(obj, n)
        assert obj.settings == {n: n for n in settings}

    def test_init_args(self, init, namespace):
        """Test init_args property."""
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        assert obj.init_args == {n: i for i, n in enumerate(namespace)}
        for n in namespace:
            setattr(obj, n, n)
            assert obj.init_args.get(n) == getattr(obj, n)
        assert obj.init_args == {n: n for n in namespace}

    def test_original_args(self, init, namespace):
        """Test original_args property"""
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        assert obj.original_args == obj._original_args == kwargs
        assert obj.original_args is not obj._original_args

    def test_replicate(self, init, namespace):
        """Test replicate method."""
        cls = type("cls", (_BaseStrategy,), {"__init__": init})
        kwargs = {name: i for i, name in enumerate(namespace)}
        obj = cls(**kwargs)
        updates_list = (
            {},
            {n: n for n in namespace},
            {n: n for n, _ in zip(namespace, range(1))},
            {n: n for n, _ in zip(namespace, range(2))},
        )
        for updates in updates_list:
            replica = obj.replicate(**updates)
            assert type(replica) is type(obj)
            assert replica is not obj
            (init_args := obj.original_args).update(**updates)
            assert init_args == replica.original_args


class TestStrategyNonParametric:
    """Test Strategy class without parametrization."""

    def test_eq_facade(self):
        """Test equality for strategy facades.

        Note: reflexivity assumed from `TestStrategy.test_eq`, symmetry always checked,
        and transitivity checked where relevant (specified in comments).

        Class-legend: {
            N: {},
            _BaseStrategy: {
                clz: {},
                cls: {A: {}, B: {BB: {}}, C: {}, _C: {}}
            }
        }
        """
        cls = type("cls", (_BaseStrategy,), {"__init__": lambda self, a, b: None})
        clz = type("clz", (_BaseStrategy,), {"__init__": lambda self, a, b: None})
        A = type("A", (cls,), {"__init__": lambda self, a: None, "b": "b"})
        B = type("B", (cls,), {"__init__": lambda self, b: None, "a": "a"})
        BB = type("BB", (B,), {"__init__": lambda self, b: None, "a": "a"})
        C = type("C", (cls,), {"__init__": lambda self, c: None, "a": "a", "b": "b"})
        _C = type("_C", (cls,), {"__init__": lambda self, _c: None, "a": "a", "b": "b"})
        N = type("N", (), {"__init__": lambda self, a, b: None})
        assert cls("a", "b") == A("a") == cls("a", "b")  # Facade
        assert cls("a", "b") == B("b") == cls("a", "b")  # Facade
        assert A("a") == B("b") == A("a")  # Different facades (transitivity)
        assert cls("a", "b") != cls("b", "a") != cls("a", "b")  # Different settings
        assert cls("a", "a") != A("a") != cls("a", "a")  # Different settings
        assert cls("a", "a") != B("b") != cls("a", "a")  # Different settings
        assert A("b") != B("a") != A("b")  # Different facades different settings
        assert cls("a", "b") != clz("a", "b") != cls("a", "b")  # Different strategies same settings
        assert cls("a", "b") != N("a", "b") != cls("a", "b")  # Non-strategy
        assert cls("a", "b") != C("c") != cls("a", "b")  # Non-facade
        assert cls("a", "b") == _C("_c") == cls("a", "b")  # Excluded extra setting
        assert cls("a", "b") == BB("b") == cls("a", "b")  # Sub-subclass
        assert BB("b") == _C("_c") == BB("b")  # Furthest (transitivity)

    @mark.parametrize("cls, ancestor, expected", [*strategy_facades()])
    def test_is_facade(self, cls, ancestor, expected):
        """Test strategy facade detection."""
        obj = cls(**{k: k for k in _infer_init_namespace(cls)})
        ancestor_obj = ancestor(**{k: k for k in _infer_init_namespace(ancestor)})
        assert cls.is_facade(ancestor) is expected
        assert obj.is_facade(ancestor) is expected
        assert cls.is_facade(ancestor_obj) is expected
        assert obj.is_facade(ancestor_obj) is expected
        if expected:  # Inverted is False
            expected = cls is ancestor  # Only `True` if equal
            assert ancestor.is_facade(cls) is expected
            assert ancestor.is_facade(obj) is expected
            assert ancestor_obj.is_facade(cls) is expected
            assert ancestor_obj.is_facade(obj) is expected

    @mark.parametrize(
        "init, error",
        [
            (lambda self: None, False),
            (lambda self, /: None, False),
            (lambda self, foo: None, False),
            (lambda self, /, foo: None, False),
            (lambda self, foo, /: None, True),
            (lambda self, foo, /, bar: None, True),
            (lambda self, foo, bar, /: None, True),
            (lambda self, *args: None, True),
            (lambda self, foo, *args: None, True),
            (lambda self, foo, *args, bar: None, True),
            (lambda self, foo, *, bar: None, False),
            (lambda self, *, foo, bar: None, False),
            (lambda self, **kwargs: None, True),
            (lambda self, foo, **kwargs: None, True),
            (lambda self, *, foo, **kwargs: None, True),
            (lambda self, foo, *, bar, **kwargs: None, True),
            (lambda self, *args, **kwargs: None, True),
            (lambda self, foo, /, *args, **kwargs: None, True),
        ],
    )
    def test_validate_init(self, init, error):
        if error:
            with raises(TypeError):
                _ = type("cls", (_BaseStrategy,), {"__init__": init})
        else:
            _ = type("cls", (_BaseStrategy,), {"__init__": init})
