import json
import dataclasses
from enum import Enum
from datetime import datetime
from typing import Optional, Type, TypeVar
import dacite

from modules.enums.enums import BacklogPriority, BacklogStatus

T = TypeVar("T")


def enum_by_name(enum_cls):
    return lambda x: enum_cls[x]


def int_hook(value) -> Optional[int]:
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
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

        data_dict = json.loads(json_str)
        return dacite.from_dict(
            data_class=cls,
            data=data_dict,
            config=dacite.Config(
                type_hooks={
                    datetime: datetime.fromisoformat,
                    BacklogPriority: enum_by_name(BacklogPriority),
                    BacklogStatus: enum_by_name(BacklogStatus),
                },
                cast=[Enum],
            ),
        )
