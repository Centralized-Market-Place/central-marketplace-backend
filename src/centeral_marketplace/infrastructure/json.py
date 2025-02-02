import datetime
from enum import Enum
import json
import re
from base64 import b64encode, b64decode
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeVar, Union, List
from pydantic import EmailStr

import ulid
from cattr import Converter
from dateutil.parser import parse
from injector import singleton, provider, Module


def get_class(kls):
    parts = kls.split(".")
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def fullname(o):
    return o.__module__ + "." + o.__class__.__qualname__


def datetime_to_millis(dt: datetime.datetime):
    return dt.timestamp() * 1000.0


def json_converter(o):
    if isinstance(o, datetime.datetime):
        return datetime_to_millis(o)  # milliseconds
    if isinstance(o, Decimal):
        return int(o)


def from_json(data):
    return json.loads(data)


def to_json(dict_o):
    return json.dumps(dict_o, default=json_converter)


def parse_date(data: str, obj_type):
    data = data.replace("T00:00:00", "")

    time_part_index = data.find("T")
    if time_part_index > -1:
        data = data[0:time_part_index]

    parsed = datetime.datetime.strptime(data, "%Y-%m-%d").date()
    return parsed


def json_to_dict(data, obj_type):
    if not data:
        return None
    return json.loads(data)


def dict_to_json(data):
    if not data:
        return None
    return json.dumps(data)


def bytes_to_str(data):
    if not data:
        return None
    res = b64encode(data).decode("ascii")
    return res


def str_to_bytes(data, obj_type):
    if not data:
        return None
    res = b64decode(data.encode("ascii"))
    return res


def type_to_str(data: type):
    if not data:
        return None
    return fullname(data)


def str_to_type(data: str, obj_type):
    if not data:
        return None
    return get_class(data)


def string_to_datetime(data, obj_type):
    if not data:
        return None
    return parse(data)


def datetime_to_string(data):
    if not data:
        return None
    return data.isoformat()


def string_to_date(data, obj_type):
    if not data:
        return None
    return parse(data).date()


def date_to_string(data):
    if not data:
        return None
    return data.isoformat()


def convert_to_camel_case(s):
    a = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")
    return a.sub(r"_\1", s).lower()


def convert_dict_to_camel_case(j):
    out = {}
    for k in j:
        new_k = convert_to_camel_case(k)
        if isinstance(j[k], dict):
            out[new_k] = convert_dict_to_camel_case(j[k])
        elif isinstance(j[k], list):
            out[new_k] = convert_array_to_camel_case(j[k])
        else:
            out[new_k] = j[k]
    return out


def convert_array_to_camel_case(a):
    new_arr = []
    for i in a:
        if isinstance(i, list):
            new_arr.append(convert_array_to_camel_case(i))
        elif isinstance(i, dict):
            new_arr.append(convert_dict_to_camel_case(i))
        else:
            new_arr.append(i)
    return new_arr


RestConverter = TypeVar("RestConverter", bound=Converter)
DatabaseConverter = TypeVar("DatabaseConverter", bound=Converter)


def ulid_to_str(data):
    if not data:
        return None
    return str(data)


def str_to_ulid(data, obj_type):
    if not data:
        return None
    return ulid.from_str(data)


def str_hook(o, type):
    if not o:
        return None
    elif isinstance(o, list):
        return List[type]
    return type


def union_str_insight_text_dict_structure_hook(data, obj_type):
    if not data:
        return None
    if isinstance(data, str):
        return data
    raise ValueError(f"Unsupported type for union: {type(data)}")


def union_str_int_structure_hook(data, obj_type):
    if not data:
        return None
    if isinstance(data, str):
        return data
    elif isinstance(data, int):
        return int(data)
    raise ValueError(f"Unsupported type for union: {type(data)}")


def create_rest_converter() -> RestConverter:
    atc = Converter()

    atc.register_structure_hook(dict, lambda c, t: c)
    atc.register_unstructure_hook(dict, lambda c: c)

    atc.register_structure_hook(bytes, str_to_bytes)
    atc.register_unstructure_hook(bytes, bytes_to_str)

    atc.register_structure_hook(ulid.ULID, str_to_ulid)
    atc.register_unstructure_hook(ulid.ULID, ulid_to_str)

    atc.register_structure_hook(type, str_to_type)
    atc.register_unstructure_hook(type, type_to_str)

    atc.register_unstructure_hook(datetime.datetime, date_to_string)
    atc.register_structure_hook(datetime.datetime, string_to_datetime)

    atc.register_unstructure_hook(datetime.date, date_to_string)
    atc.register_structure_hook(datetime.date, string_to_date)

    atc.register_structure_hook(Union[str, int], union_str_int_structure_hook)

    atc.register_unstructure_hook(Enum, lambda e: e.value)
    atc.register_structure_hook(Enum, lambda value, cls: cls(value))

    atc.register_unstructure_hook(EmailStr, lambda e: str(e))
    atc.register_structure_hook(
        EmailStr, lambda e, _: e if isinstance(e, str) else str(e)
    )

    return atc


class JsonModule(Module):
    @singleton
    @provider
    def provide_rest_converter(
        self,
    ) -> RestConverter:
        return create_rest_converter()


@dataclass
class PaginatedResponse:
    page: int
    page_size: int
    total: int
    items: list


@dataclass
class Pagination:
    page: int
    size: int
