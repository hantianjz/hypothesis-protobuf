"""Tests for hypothesis_protobuf/module_conversion.py"""

from __future__ import absolute_import, unicode_literals

from numbers import Number

from past.builtins import basestring
from hypothesis import strategies as st

from .test_schemas import im_pb2
from .test_schemas import loop_pb2
from .test_schemas import sfixed_pb2

from hypothesis import given
from .test_schemas import im_pb2, im_depend_pb2, im_nested_pb2

from hypothesis_protobuf.module_conversion import modules_to_strategies
from hypothesis_protobuf.utils import full_field_name


def test_instant_message_example():
    """Ensure InstantMessage can be made into a strategy with the correct types."""
    protobuf_strategies = modules_to_strategies(im_pb2)
    instant_message_strategy = protobuf_strategies[im_pb2.InstantMessage]
    instant_message_example = instant_message_strategy.example()
    assert isinstance(instant_message_example.timestamp, Number)
    assert isinstance(instant_message_example.sender.screen_name, basestring)
    assert isinstance(instant_message_example.recipient.screen_name,
                      basestring)
    assert isinstance(instant_message_example.message, basestring)
    assert isinstance(instant_message_example.metadata.latency, float)
    assert isinstance(instant_message_example.metadata.inner.a, float)
    assert isinstance(instant_message_example.metadata.inner.layer.client.name,
                      basestring)
    assert isinstance(instant_message_example.metadata.inner.layer.status,
                      Number)
    assert isinstance(instant_message_example.client, Number)


def test_overrides_respected():
    """Ensure provided overrides are respected."""
    protobuf_strategies = modules_to_strategies(
        im_pb2, **{
            full_field_name(im_pb2.InstantMessage, 'message'):
            st.just('test message')
        })
    instant_message_strategy = protobuf_strategies[im_pb2.InstantMessage]
    instant_message_example = instant_message_strategy.example()
    assert instant_message_example.message == 'test message'


def test_nested_strategies_produce_data():
    """Ensure nested messages are accessible within strategy dict."""
    protobuf_strategies = modules_to_strategies(im_pb2)
    assert protobuf_strategies[im_pb2.MetaData.Inner].example()
    assert protobuf_strategies[im_pb2.MetaData.Inner.LimboDreamLayer].example()


def test_recursive_strategies_produce_data():
    """
    Ensure that we are able to construct strategies for recursive
    messages
    """
    protobuf_strategies = modules_to_strategies(loop_pb2)
    assert protobuf_strategies[loop_pb2.Loop].example()


@given(modules_to_strategies(sfixed_pb2)[sfixed_pb2.Sfixed])
def test_sfixed_values_are_in_range(sfixed):
    """
    Ensure that sfixed32 and sfixed64 fields have strategies generating
    values in the range of 32 and 64 bit signed integers respectively.
    """
    assert -(1 << 31) <= sfixed.sfixed32 <= (1 << 31) - 1
    assert -(1 << 63) <= sfixed.sfixed64 <= (1 << 63) - 1


def test_instant_message_nested_example():
    """Ensure InstantMessage can be made into a strategy with the correct types."""
    protobuf_strategies = modules_to_strategies(im_nested_pb2)
    instant_message_strategy = protobuf_strategies[
        im_nested_pb2.InstantMessage]
    instant_message_example = instant_message_strategy.example()
    assert isinstance(instant_message_example.timestamp, Number)
    assert isinstance(instant_message_example.sender.screen_name, basestring)
    assert isinstance(instant_message_example.recipient.screen_name,
                      basestring)
    assert isinstance(instant_message_example.message, basestring)
    assert isinstance(instant_message_example.metadata.latency, float)
    assert isinstance(instant_message_example.timestamp, Number)
    assert isinstance(instant_message_example.nested1, Number)
    assert isinstance(instant_message_example.metadata.inner_data.nested1,
                      Number)
    assert isinstance(instant_message_example.metadata.inner_data.nested2,
                      Number)


def test_overrides_respected_nested():
    """Ensure provided overrides are respected."""
    protobuf_strategies = modules_to_strategies(
        im_nested_pb2, **{
            full_field_name(im_nested_pb2.InstantMessage, 'timestamp'):
            st.just(101),
            full_field_name(im_nested_pb2.InstantMessage, 'message'):
            st.just('test message'),
            full_field_name(im_nested_pb2.InstantMessage, 'nested1'):
            st.just(3),
            full_field_name(im_nested_pb2.MetaData, 'latency'):
            st.just(10),
            full_field_name(im_nested_pb2.MetaData.InnerData, 'nested1'):
            st.just(2),
        })
    instant_message_strategy = protobuf_strategies[
        im_nested_pb2.InstantMessage]
    instant_message_example = instant_message_strategy.example()
    assert instant_message_example.timestamp == 101
    assert instant_message_example.message == 'test message'
    assert instant_message_example.nested1 == 3
    assert instant_message_example.metadata.latency == 10
    assert instant_message_example.metadata.inner_data.nested1 == 2


def test_multiple_modules_dependency():
    """Ensure modules are loaded regardless of load order."""
    # im_depend_pb2 imports types from im_pb2
    protobuf_strategies = modules_to_strategies(im_depend_pb2, im_pb2)
    assert im_depend_pb2.DepMessage in protobuf_strategies
