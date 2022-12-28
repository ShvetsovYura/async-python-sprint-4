from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from ipaddress import ip_address, ip_network
from json import dumps, loads
from typing import Callable
from uuid import UUID

from dateutil.parser import parse

import db.pg_types as pt


def bool_in(data: str):
    return data == 't'


def bool_out(value: bool):
    return 'true' if value else 'false'


def bytes_in(data):
    return bytes.fromhex(data[2:])


def bytes_out(value):
    return '\\x' + value.hex()


def cidr_out(value):
    return str(value)


def cidr_in(data):
    return ip_network(data, False) if '/' in data else ip_address(data)


def date_in(data):
    if data in ('infinity', '-infinity'):
        return data
    else:
        return datetime.strptime(data, '%Y-%m-%d').date()


def date_out(value: datetime):
    return value.isoformat()


def datetime_out(value: datetime):
    if value.tzinfo is None:
        return value.isoformat()
    else:
        return value.astimezone(timezone.utc).isoformat()


def enum_out(value: Enum) -> str:
    return str(value.value)


def float_out(value: float):
    return str(value)


def inet_in(data: str):
    return ip_network(data, False) if '/' in data else ip_address(data)


def inet_out(value) -> str:
    return str(value)


def int_in(data: str) -> int:
    return int(data)


def int_out(value: int) -> str:
    return str(value)


def interval_out(value: timedelta):
    return f'{value.days} days {value.seconds} seconds {value.microseconds} microseconds'


def json_in(data: str) -> dict:
    return loads(data)


def json_out(value: dict) -> str:
    return dumps(value)


def null_out(value):
    return None


def numeric_in(data):
    return Decimal(data)


def numeric_out(data):
    return str(data)


def pg_interval_out(value):
    return str(value)


def string_in(data):
    return data


def string_out(value: str):
    return value


def time_in(data):
    pattern = '%H:%M:%S.%f' if '.' in data else '%H:%M:%S'
    return datetime.strptime(data, pattern).time()


def time_out(value: datetime):
    return value.isoformat()


def timestamp_in(data):
    if data in ('infinity', '-infinity'):
        return data

    try:
        pattern = '%Y-%m-%d %H:%M:%S.%f' if '.' in data else '%Y-%m-%d %H:%M:%S'
        return datetime.strptime(data, pattern)
    except ValueError:
        return parse(data)


def timestamptz_in(data):
    if data in ('infinity', '-infinity'):
        return data

    try:
        pattern = '%Y-%m-%d %H:%M:%S.%f%z' if '.' in data else '%Y-%m-%d %H:%M:%S%z'
        return datetime.strptime(f'{data}00', pattern)
    except ValueError:
        return parse(data)


def unknown_out(value):
    return str(value)


def vector_in(data):
    return [int(value) for value in data.split()]


def uuid_out(value: UUID):
    return str(value)


def uuid_in(data):
    return UUID(data)


PY_PG = {
    date: pt.DATE,
    Decimal: pt.NUMERIC,
    time: pt.TIME,
    timedelta: pt.INTERVAL,
    UUID: pt.UUID_TYPE,
    bool: pt.BOOLEAN,
    bytearray: pt.BYTES,
    dict: pt.JSONB,
    float: pt.FLOAT,
    type(None): pt.NULLTYPE,
    bytes: pt.BYTES,
    str: pt.TEXT,
}

PY_TYPES = {
    date: date_out,    # date
    datetime: datetime_out,
    Decimal: numeric_out,    # numeric
    Enum: enum_out,    # enum
    time: time_out,    # time
    timedelta: interval_out,    # interval
    UUID: uuid_out,    # uuid
    bool: bool_out,    # bool
    bytearray: bytes_out,    # bytea
    dict: json_out,    # jsonb
    float: float_out,    # float8
    type(None): null_out,    # null
    bytes: bytes_out,    # bytea
    str: string_out,    # unknown
    int: int_out,
}

PG_TYPES = {
    pt.BIGINT: int,    # int8
    pt.BOOLEAN: bool_in,    # bool
    pt.BYTES: bytes_in,    # bytea
    pt.CHAR: string_in,    # char
    pt.CSTRING: string_in,    # cstring
    pt.DATE: date_in,    # date
    pt.FLOAT: float,    # float8
    pt.INET: inet_in,    # inet
    pt.INTEGER: int,    # int4
    pt.JSON: json_in,    # json
    pt.JSONB: json_in,    # jsonb
    pt.MACADDR: string_in,    # MACADDR type
    pt.MONEY: string_in,    # money
    pt.NAME: string_in,    # name
    pt.NUMERIC: numeric_in,    # numeric
    pt.OID: int,    # oid
    pt.REAL: float,    # float4
    pt.SMALLINT: int,    # int2
    pt.SMALLINT_VECTOR: vector_in,    # int2vector
    pt.TEXT: string_in,    # text
    pt.TIME: time_in,    # time
    pt.TIMESTAMP: timestamp_in,    # timestamp
    pt.TIMESTAMPTZ: timestamptz_in,    # timestamptz
    pt.UNKNOWN: string_in,    # unknown
    pt.UUID_TYPE: uuid_in,    # uuid
    pt.VARCHAR: string_in,    # varchar
    pt.XID: int,    # xid
}


def make_param(value):    # noqa CCF001
    py_types = dict(PY_TYPES)

    try:
        converter: Callable = py_types[type(value)]
    except KeyError:
        converter: Callable = str
        for key_, value_ in py_types.items():
            try:
                if isinstance(value, key_):
                    converter: Callable = value_
                    break
            except TypeError:
                pass

    return converter(value)


def python_types_convert_to_pg_params(values: tuple):
    return tuple([make_param(value) for value in values])
