import json
import dataclasses
from enum import Enum
from datetime import datetime
from typing import Type, TypeVar
import dacite

T = TypeVar("T")


def int_hook(value):
    if isinstance(value, str):
        return int(value)
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
        raw = json.loads(json_str)
        return dacite.from_dict(
            data_class=cls,
            data=raw,
            config=dacite.Config(cast=[datetime, Enum], type_hooks={int: int_hook}),
        )
