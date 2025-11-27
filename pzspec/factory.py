"""
Factory framework for creating ctypes structures for Zig FFI testing.

Inspired by FactoryBot/Factory Boy, provides a declarative way to define
test data factories with defaults, sequences, and traits.
"""

from typing import Any, Callable, Dict, List, Optional, Type
import ctypes


class FactoryField:
    """
    Defines a field with a default value for a struct factory.

    Usage:
        class Vec2Factory(StructFactory):
            x = factory_field(default=0.0)
            y = factory_field(default=0.0, lazy=True)  # lazy evaluation
    """

    def __init__(self, default: Any = None, lazy: bool = False):
        """
        Initialize a factory field.

        Args:
            default: Default value, or callable if lazy=True
            lazy: If True, default is called each time to get value
        """
        self.default = default
        self.lazy = lazy

    def resolve(self) -> Any:
        """Resolve the field value."""
        if self.lazy and callable(self.default):
            return self.default()
        return self.default


def factory_field(default: Any = None, lazy: bool = False) -> FactoryField:
    """
    Create a factory field with a default value.

    Args:
        default: Default value, or callable if lazy=True
        lazy: If True, default is called each time to get value

    Returns:
        FactoryField instance
    """
    return FactoryField(default=default, lazy=lazy)


class Sequence:
    """
    Auto-incrementing sequence for generating unique values.

    Usage:
        class EntityFactory(StructFactory):
            id = sequence(lambda n: n)
            name = sequence(lambda n: f"entity_{n}")
    """

    def __init__(self, func: Callable[[int], Any]):
        """
        Initialize a sequence.

        Args:
            func: Callable that takes counter value and returns generated value
        """
        self.func = func
        self.counter = 0

    def next(self) -> Any:
        """Get the next value in the sequence."""
        self.counter += 1
        return self.func(self.counter)

    def reset(self):
        """Reset the sequence counter."""
        self.counter = 0


def sequence(func: Callable[[int], Any]) -> Sequence:
    """
    Create an auto-incrementing sequence.

    Args:
        func: Callable that takes counter (starting at 1) and returns value

    Returns:
        Sequence instance

    Example:
        id = sequence(lambda n: n)           # 1, 2, 3, ...
        name = sequence(lambda n: f"vec_{n}") # vec_1, vec_2, ...
    """
    return Sequence(func)


def trait(method: Callable) -> Callable:
    """
    Decorator to mark a method as a trait (named preset).

    Traits are converted to classmethods that build instances with preset values.

    Usage:
        class Vec2Factory(StructFactory):
            @trait
            def unit_x(self):
                return {"x": 1.0, "y": 0.0}

        # Then use as:
        vec = Vec2Factory.unit_x()
    """
    method._is_trait = True
    return method


class StructFactoryMeta(type):
    """
    Metaclass that processes factory class definitions.

    Collects fields, sequences, and traits from class attributes
    and sets up the factory infrastructure.
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Collect factory fields and sequences
        fields: Dict[str, FactoryField] = {}
        sequences: Dict[str, Sequence] = {}
        traits: Dict[str, Callable] = {}

        # Check base classes for inherited fields
        for base in bases:
            if hasattr(base, '_factory_fields'):
                fields.update(base._factory_fields)
            if hasattr(base, '_factory_sequences'):
                sequences.update(base._factory_sequences)
            if hasattr(base, '_factory_traits'):
                traits.update(base._factory_traits)

        # Process current class attributes
        for attr_name, attr_value in list(namespace.items()):
            if isinstance(attr_value, FactoryField):
                fields[attr_name] = attr_value
            elif isinstance(attr_value, Sequence):
                sequences[attr_name] = attr_value
            elif callable(attr_value) and getattr(attr_value, '_is_trait', False):
                traits[attr_name] = attr_value

        # Store metadata
        namespace['_factory_fields'] = fields
        namespace['_factory_sequences'] = sequences
        namespace['_factory_traits'] = traits

        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)

        # Create trait classmethods
        for trait_name, trait_method in traits.items():
            def make_trait_classmethod(method):
                @classmethod
                def trait_classmethod(cls, **overrides):
                    # Get trait values by calling the method
                    trait_values = method(cls)
                    # Merge with overrides (overrides take precedence)
                    merged = {**trait_values, **overrides}
                    return cls.build(**merged)
                return trait_classmethod

            setattr(cls, trait_name, make_trait_classmethod(trait_method))

        return cls


class StructFactory(metaclass=StructFactoryMeta):
    """
    Base class for ctypes struct factories.

    Subclass this to create factories for your ctypes.Structure classes.

    Example:
        class Vec2(ctypes.Structure):
            _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

        class Vec2Factory(StructFactory):
            struct_class = Vec2
            x = factory_field(default=0.0)
            y = factory_field(default=0.0)

            @trait
            def unit_x(self):
                return {"x": 1.0, "y": 0.0}

        # Usage:
        vec = Vec2Factory()              # (0.0, 0.0)
        vec = Vec2Factory(x=5.0)         # (5.0, 0.0)
        vec = Vec2Factory.unit_x()       # (1.0, 0.0)
        vecs = Vec2Factory.build_batch(3) # 3 instances
    """

    struct_class: Optional[Type[ctypes.Structure]] = None

    _factory_fields: Dict[str, FactoryField] = {}
    _factory_sequences: Dict[str, Sequence] = {}
    _factory_traits: Dict[str, Callable] = {}

    def __new__(cls, **overrides) -> ctypes.Structure:
        """
        Create a new struct instance with resolved field values.

        Args:
            **overrides: Field values to override defaults

        Returns:
            Instance of struct_class with populated fields
        """
        return cls.build(**overrides)

    @classmethod
    def build(cls, **overrides) -> ctypes.Structure:
        """
        Build a struct instance with the given overrides.

        Args:
            **overrides: Field values to override defaults

        Returns:
            Instance of struct_class with populated fields
        """
        if cls.struct_class is None:
            raise ValueError(
                f"{cls.__name__} must define 'struct_class' "
                "pointing to a ctypes.Structure subclass"
            )

        # Start with resolved defaults
        values = {}

        # Resolve factory fields
        for field_name, field in cls._factory_fields.items():
            values[field_name] = field.resolve()

        # Resolve sequences
        for seq_name, seq in cls._factory_sequences.items():
            values[seq_name] = seq.next()

        # Apply overrides
        values.update(overrides)

        # Create struct instance
        struct = cls.struct_class()

        # Set field values (only those that exist on the struct)
        struct_field_names = {f[0] for f in cls.struct_class._fields_}
        for field_name, value in values.items():
            if field_name in struct_field_names:
                setattr(struct, field_name, value)

        return struct

    @classmethod
    def build_batch(cls, count: int, **overrides) -> List[ctypes.Structure]:
        """
        Build multiple struct instances.

        Args:
            count: Number of instances to create
            **overrides: Field values to override defaults (applied to all)

        Returns:
            List of struct instances
        """
        return [cls.build(**overrides) for _ in range(count)]

    @classmethod
    def reset_sequences(cls):
        """Reset all sequence counters for this factory."""
        for seq in cls._factory_sequences.values():
            seq.reset()
