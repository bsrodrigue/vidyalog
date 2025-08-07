from datetime import datetime
import json
from collections import OrderedDict
from abc import ABC
from enum import Enum
from typing import Optional, Union
from sqlalchemy import text
from smolorm.connection import engine
from smolorm.expressions import col
from smolorm.orm import ORM


class SmolField(ABC):
    pass


class TextField(SmolField):
    def __init__(self, default_value: Optional[str] = None, required: bool = False):
        self.required = required
        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        self.default_value = default_value


class IntField(SmolField):
    def __init__(self, default_value: Optional[int] = None, required: bool = False):
        self.required = required
        if self.required and default_value is None:
            raise SmolORMException("Field is required")
        self.default_value = default_value


class RealField(SmolField):
    def __init__(self, default_value: Optional[float] = None, required: bool = False):
        self.required = required
        if self.required and default_value is None:
            raise SmolORMException("Field is required")
        self.default_value = default_value


class DatetimeField(SmolField):
    def __init__(
        self, default_value: Optional[datetime] = None, required: bool = False
    ):
        self.required = required
        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        self.default_value = default_value


class SmolORMException(Exception):
    def __init__(self, message: str = ""):
        self.message = message

        # TODO: Keep going


class SqlModel(ABC):
    table_name: str = ""

    created_at: DatetimeField = DatetimeField(
        default_value=datetime.now(), required=True
    )
    updated_at: DatetimeField = DatetimeField(
        default_value=datetime.now(), required=True
    )

    deleted_at: DatetimeField = DatetimeField()

    @staticmethod
    def _get_coldefs(_cls) -> OrderedDict[str, SmolField]:
        columns = OrderedDict()
        for key, val in _cls.__dict__.items():
            if not isinstance(val, SmolField):
                continue
            columns[str(key)] = val

        if len(columns) == 0:
            raise SmolORMException("No columns defined")

        return columns

    def __init_subclass__(cls) -> None:
        table_name = cls.table_name
        if table_name is None:
            raise SmolORMException("table_name is required")

        columns = SqlModel._get_coldefs(cls)
        connection = engine.connect()

        query_str = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        query_str += "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        query_str += "created_at TEXT, "
        query_str += "updated_at TEXT, "
        query_str += "deleted_at TEXT, "
        for key, val in columns.items():
            query_str += f"{key} "
            if isinstance(val, TextField):
                query_str += "TEXT"
            elif isinstance(cls.__dict__[key], int):
                query_str += "INT"
            elif isinstance(cls.__dict__[key], float):
                query_str += "REAL"
            elif isinstance(cls.__dict__[key], list):
                query_str += "TEXT"
            elif isinstance(cls.__dict__[key], Enum):
                query_str += "TEXT"
            elif isinstance(cls.__dict__[key], datetime):
                query_str += "TEXT"

            if val is not None:
                if isinstance(val, str):
                    val = f'"{val}"'
                elif isinstance(val, int):
                    val = val
                elif isinstance(val, float):
                    val = val
                elif isinstance(val, Enum):
                    val = f'"{val.value}"'
                elif isinstance(val, datetime):
                    val = f'"{val.isoformat()}"'
                elif isinstance(val, list):
                    if len(val) <= 0:
                        query_str += ", "
                        continue
                    first = val[0]

                    if isinstance(first, Enum):
                        val = json.dumps([x.value for x in val])
                    else:
                        val = json.dumps(val)
                query_str += f" DEFAULT {val}"
            query_str += ", "
        query_str = query_str.rstrip(", ")
        query_str += ");"

        # print(f"==CREATE MODEL {cls.__name__} QUERY==:\n{query_str}\n")
        connection.execute(text(query_str))
        connection.commit()
        connection.close()
        return super().__init_subclass__()

    @classmethod
    def create(cls, fields: dict[str, Union[str, int]]):
        table = cls.table_name
        row_id = ORM.from_(table).create(fields)
        result = ORM.from_(cls.table_name).select().where(col("id") == row_id).run()

        if not isinstance(result, list):
            raise SmolORMException(f"Failed to create {cls.__name__}")

        if len(result) <= 0:
            raise SmolORMException(f"Failed to create {cls.__name__}")

        return result[0]

    @classmethod
    def update(cls, fields: dict[str, Union[str, int]]):
        table = cls.table_name
        return ORM.from_(table).update(fields)

    @classmethod
    def delete(cls):
        table = cls.table_name
        return ORM.from_(table).delete()

    @classmethod
    def select(cls, *cols):
        return ORM.from_(cls.table_name).select(*cols)

    @classmethod
    def drop(cls):
        connection = engine.connect()
        query_str = f"DROP table IF EXISTS {cls.table_name};"
        connection.execute(text(query_str))
        connection.close()
