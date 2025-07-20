import json
import dataclasses
from enum import Enum
from datetime import datetime
from typing import Type, TypeVar
import dacite

from modules.enums.enums import BacklogPriority

T = TypeVar("T")


def enum_by_name(enum_cls):
    return lambda x: enum_cls[x]


def int_hook(value):
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return value
    return value


class DataclassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)  # pyright: ignore
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.name
        return super().default(o)


class DataclassSerializer:
    @staticmethod
    def serialize(obj: object) -> str:
        return json.dumps(obj, cls=DataclassEncoder)

    @staticmethod
    def deserialize(json_str: str, cls: Type[T]) -> T:
        if not dataclasses.is_dataclass(cls):
            raise ValueError(f"{cls.__name__} is not a dataclass")

        raw = json.loads(json_str)
        return dacite.from_dict(
            data_class=cls,
            data=raw,
            config=dacite.Config(
                type_hooks={
                    int: int_hook,
                    datetime: datetime.fromisoformat,
                    BacklogPriority: enum_by_name(BacklogPriority),
                },
                cast=[Enum],
            ),
        )
