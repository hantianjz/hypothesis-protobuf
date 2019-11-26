"""Conversion of protobuf modules to hypothesis strategies via internal representation."""

from __future__ import absolute_import, division, print_function, unicode_literals

from functools import partial

from hypothesis import strategies as st

from google.protobuf.internal import enum_type_wrapper
from google.protobuf.internal.well_known_types import FieldDescriptor

SINGLEPRECISION = dict(max_value=(2 - 2**-23) * 2**127,
                       min_value=-(2 - 2**-23) * 2**127)
RANGE32 = dict(max_value=2**31 - 1, min_value=-(2**31) + 1)
RANGE64 = dict(max_value=2**63 - 1, min_value=-(2**63) + 1)
URANGE32 = dict(min_value=0, max_value=2**32 - 1)
URANGE64 = dict(min_value=0, max_value=2**64 - 1)

SCALAR_MAPPINGS = {
    FieldDescriptor.TYPE_DOUBLE: st.floats(),
    FieldDescriptor.TYPE_FLOAT: st.floats(**SINGLEPRECISION),
    FieldDescriptor.TYPE_INT32: st.integers(**RANGE32),
    FieldDescriptor.TYPE_INT64: st.integers(**RANGE64),
    FieldDescriptor.TYPE_UINT32: st.integers(**URANGE32),
    FieldDescriptor.TYPE_UINT64: st.integers(**URANGE64),
    FieldDescriptor.TYPE_SINT32: st.integers(**RANGE32),
    FieldDescriptor.TYPE_SINT64: st.integers(**RANGE64),
    FieldDescriptor.TYPE_FIXED32: st.integers(**URANGE32),
    FieldDescriptor.TYPE_FIXED64: st.integers(**URANGE64),
    FieldDescriptor.TYPE_SFIXED32: st.integers(**RANGE32),
    FieldDescriptor.TYPE_SFIXED64: st.integers(**RANGE64),
    FieldDescriptor.TYPE_BOOL: st.booleans(),
    FieldDescriptor.TYPE_STRING: st.text(),
    FieldDescriptor.TYPE_BYTES: st.binary()
}

LABEL_MAPPINGS = {
    FieldDescriptor.LABEL_OPTIONAL: st.one_of,
    FieldDescriptor.LABEL_REPEATED: st.lists,
    FieldDescriptor.LABEL_REQUIRED: lambda x: x
}

MAX_LOAD_DEPTH = 5


def overridable(f):
    """
    Handle overrides in a strategy-generating function, taking a field as a
    first argument.

    Overrides can be strategies themselves or functions from strategies to
    strategies. In the latter case, the override will be passed the originally
    generated strategy from the decorated function.
    """
    def wrapper(*args, **kwargs):
        overrides = kwargs.get('overrides')
        if not overrides:
            return f(*args)

        field = args[0]
        field_name = getattr(field, 'DESCRIPTOR', field).full_name

        overridden_strategy = overrides.get(field_name)
        if not overridden_strategy:
            return f(*args)

        if not callable(overridden_strategy):
            return overridden_strategy

        return overridden_strategy(f(*args))

    return wrapper


@overridable
def enum_to_strategy(enum):
    """Generate strategy for enum."""
    return st.sampled_from([value.number for value in enum.DESCRIPTOR.values])


def find_strategy_in_env(descriptor, env):
    """Find strategy matching descriptor."""
    for proto_cls, strategy in env.items():
        if proto_cls.DESCRIPTOR.full_name == descriptor.full_name:
            return strategy
    raise LookupError("Did not exist in env.")


def apply_modifier(strategy, field):
    """Apply labeled modifier to strategy."""
    return LABEL_MAPPINGS.get(field.label)(strategy)


def non_null(x):
    return x is not None


@overridable
def field_to_strategy(field, env):
    """Generate strategy for field."""
    if SCALAR_MAPPINGS.get(field.type) is not None:
        return apply_modifier(strategy=SCALAR_MAPPINGS[field.type],
                              field=field)

    if field.type is FieldDescriptor.TYPE_ENUM:
        return apply_modifier(strategy=find_strategy_in_env(
            field.enum_type, env),
                              field=field)

    if field.type is FieldDescriptor.TYPE_MESSAGE:
        field_options = field.message_type.GetOptions()

        if field_options.deprecated:
            return st.none()

        if field_options.map_entry:
            k, v = field.message_type.fields
            return st.dictionaries(
                field_to_strategy(k, env).filter(non_null),
                field_to_strategy(v, env).filter(non_null))

        return apply_modifier(strategy=find_strategy_in_env(
            field.message_type, env),
                              field=field)

    raise Exception("Unhandled field {}.".format(field))


def buildable(message_obj):
    """Return a "buildable" callable for st.builds which will handle optionals."""
    def builder(**kwargs):
        return message_obj(
            **{
                k: v
                for k, v in kwargs.items()
                if v is not None  # filter out unpopulated optional param
            })

    builder.__name__ = message_obj.DESCRIPTOR.full_name
    return builder


def message_to_strategy(message_obj, env, overrides=None):
    """Generate strategy from message."""
    # Protobuf messages may have recursive dependencies.
    # We can manage these by lazily constructing strategies using st.deferred
    return st.deferred(lambda: st.builds(
        buildable(message_obj), **{
            field_name: field_to_strategy(field, env, overrides=overrides)
            for field_name, field in message_obj.DESCRIPTOR.fields_by_name.
            items()
        }))


def handle_message_type(all_mess_objs, all_enum_objs, cont_obj, cont_type):

    for cur_enum in cont_type.enum_types:
        all_enum_objs.append(getattr(cont_obj, cur_enum.name))

    all_mess_objs.append(cont_obj)
    all_nested = cont_type.nested_types
    for cur_nested in all_nested:
        handle_message_type(all_mess_objs, all_enum_objs,
                            getattr(cont_obj, cur_nested.name), cur_nested)


def load_module_into_env(parent_obj, env, overrides=None, depth=1):
    """Populate env with all messages and enums from the module."""
    if depth > MAX_LOAD_DEPTH:
        raise Exception(
            "Nesting below {} levels is not supported".format(MAX_LOAD_DEPTH))

    if hasattr(parent_obj.DESCRIPTOR, 'enum_types'):
        enum_types = parent_obj.DESCRIPTOR.enum_types
    else:
        enum_types = parent_obj.DESCRIPTOR.enum_types_by_name.values()

    for enum_type in enum_types:
        enum_obj = enum_type_wrapper.EnumTypeWrapper(enum_type)
        env[enum_obj] = enum_to_strategy(enum_obj, overrides=overrides)

    # get all types at the current depth
    if hasattr(parent_obj.DESCRIPTOR, 'nested_types'):
        nested_types = parent_obj.DESCRIPTOR.nested_types
    else:  # parent_obj is a module
        nested_types = parent_obj.DESCRIPTOR.message_types_by_name.values()

    # Some message types are dependant on other messages being loaded
    # Unfortunately, how to determine load order is not clear.
    # We'll loop through all the messages, skipping over errors until we've either:
    # A) loaded all the messages
    # B) exhausted all the possible orderings
    total_messages = len(nested_types)
    loaded = set()
    is_loaded = False
    for __ in range(total_messages):
        for message in nested_types:
            if message in loaded:
                continue
            try:
                message_obj = getattr(parent_obj, message.name)
                load_module_into_env(message_obj,
                                     env,
                                     overrides=overrides,
                                     depth=depth + 1)
                env[message_obj] = message_to_strategy(message_obj,
                                                       env,
                                                       overrides=overrides)
                loaded.add(message)
            except LookupError:
                continue

        if all(message in loaded for message in nested_types):
            is_loaded = True
            break
    return is_loaded


def modules_to_strategies(*modules, **overrides):
    """
    Map protobuf classes from all supplied modules to hypothesis strategies.

    If overrides are provided as strategies, these are used in place of the
    fields or enums they are mapped to. If they are provided as callables of
    type Callable[[Strategy], Strategy], they will be passed the originally
    generated strategy for the field they are mapped to.
    """
    env = {}
    module_loaded = {}
    total_modules = len(modules)
    for __ in range(total_modules):
        for module in modules:
            if module_loaded.get(module):
                continue
            module_loaded[module] = load_module_into_env(
                module, env, overrides)
    return env
