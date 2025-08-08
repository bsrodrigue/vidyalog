from datetime import datetime
import json
from collections import OrderedDict
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from sqlalchemy import text
from smolorm.connection import engine
from smolorm.expressions import col
from smolorm.orm import ORM


class SmolField(ABC):
    def __init__(self, col_type: str, required: bool = True):
        self.col_type = col_type
        self.required = required
        self.sql_default_value = None

    @abstractmethod
    def to_sql(self, value):
        raise NotImplementedError()


class TextField(SmolField):
    def __init__(self, default_value: Optional[str] = None, required: bool = True):
        super().__init__("TEXT", required)

        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        if default_value is not None:
            self.sql_default_value = self.to_sql(default_value)

    def to_sql(self, value: str):
        return f'"{value}"'


class IntField(SmolField):
    def __init__(self, default_value: Optional[int] = None, required: bool = True):
        super().__init__("INT", required)
        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        if default_value is not None:
            self.sql_default_value = self.to_sql(default_value)

    def to_sql(self, value: int):
        return f"{value}"


class RealField(SmolField):
    def __init__(self, default_value: Optional[float] = None, required: bool = True):
        super().__init__("REAL", required)
        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        if default_value is not None:
            self.sql_default_value = self.to_sql(default_value)

    def to_sql(self, value: float):
        return f"{value}"


class EnumField(SmolField):
    def __init__(self, default_value: Optional[Enum] = None, required: bool = True):
        super().__init__("TEXT", required)
        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        if default_value is not None:
            self.sql_default_value = self.to_sql(default_value)

    def to_sql(self, value: Enum):
        return f'"{value.value}"'


class DatetimeField(SmolField):
    """
    SQLite does not actually support datetime fields.
    We will store them as TEXT and parse them on retrieval
    """

    def __init__(self, default_value: Optional[datetime] = None, required: bool = True):
        super().__init__("TEXT", required)
        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        if default_value is not None:
            self.sql_default_value = self.to_sql(default_value)

    def to_sql(self, value: datetime):
        return f'"{value.isoformat()}"'


class ListField(SmolField):
    def __init__(
        self, default_value: Optional[list[Any]] = None, required: bool = True
    ):
        super().__init__("TEXT", required)
        if self.required and default_value is None:
            raise SmolORMException("Field is required")

        if default_value is not None:
            self.sql_default_value = self.to_sql(default_value)

    def to_sql(self, value: list[Any]):
        return f'"{json.dumps(value)}"'


class SmolORMException(Exception):
    def __init__(self, message: str = ""):
        self.message = message


class SqlModel(ABC):
    table_name: str = ""

    created_at = DatetimeField(default_value=datetime.now())
    updated_at = DatetimeField(default_value=datetime.now())
    deleted_at = DatetimeField(required=False)

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

        query_str = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        query_str += "id INTEGER PRIMARY KEY AUTOINCREMENT, "

        for column_name, smol_field in columns.items():
            query_str += f"{column_name} "
            query_str += smol_field.col_type

            if smol_field.required:
                query_str += " NOT NULL "

            if smol_field.sql_default_value is not None:
                query_str += f" DEFAULT {smol_field.sql_default_value} "

            query_str += ", "
        query_str = query_str.rstrip(", ")
        query_str += ");"

        print(f"==CREATE MODEL {cls.__name__} QUERY==:\n{query_str}\n")
        connection = engine.connect()
        connection.execute(text(query_str))
        connection.commit()
        connection.close()
        return super().__init_subclass__()

    @classmethod
    def create(cls, fields: dict[str, Any]):
        table = cls.table_name
        row_id = ORM.from_(table).create(fields)
        result = ORM.from_(cls.table_name).select().where(col("id") == row_id).run()

        if not isinstance(result, list):
            raise SmolORMException(f"Failed to create {cls.__name__}")

        if len(result) <= 0:
            raise SmolORMException(f"Failed to create {cls.__name__}")

        return result[0]

    @classmethod
    def update(cls, fields: dict[str, Any]):
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
