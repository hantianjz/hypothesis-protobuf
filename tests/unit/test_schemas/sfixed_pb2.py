# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: sfixed.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='sfixed.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0csfixed.proto\",\n\x06Sfixed\x12\x10\n\x08sfixed32\x18\x01 \x01(\x0f\x12\x10\n\x08sfixed64\x18\x02 \x01(\x10\x62\x06proto3')
)




_SFIXED = _descriptor.Descriptor(
  name='Sfixed',
  full_name='Sfixed',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='sfixed32', full_name='Sfixed.sfixed32', index=0,
      number=1, type=15, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sfixed64', full_name='Sfixed.sfixed64', index=1,
      number=2, type=16, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=16,
  serialized_end=60,
)

DESCRIPTOR.message_types_by_name['Sfixed'] = _SFIXED
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Sfixed = _reflection.GeneratedProtocolMessageType('Sfixed', (_message.Message,), dict(
  DESCRIPTOR = _SFIXED,
  __module__ = 'sfixed_pb2'
  # @@protoc_insertion_point(class_scope:Sfixed)
  ))
_sym_db.RegisterMessage(Sfixed)


# @@protoc_insertion_point(module_scope)