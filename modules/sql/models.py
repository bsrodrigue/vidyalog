from collections import OrderedDict
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar
from sqlalchemy import create_engine, text

from modules.sql.parser import ORM

engine = create_engine("sqlite:///db.sqlite3")


class SqlOperator(Enum):
    EQ = "eq"
    NEQ = "neq"


@dataclass()
class SqlFilter:
    column: str = ""
    operator: str = ""
    value: str = ""


class SqlModel(ABC):
    table_name: str = ""

    @staticmethod
    def _get_coldefs(_cls) -> OrderedDict:
        columns = OrderedDict()
        for key, val in _cls.__dict__.items():
            if (
                key.startswith("_")
                or key.endswith("_")
                or callable(val)
                or isinstance(val, (staticmethod, classmethod))
            ):
                continue
            columns[key] = val

        return columns

    def __init_subclass__(cls) -> None:
        connection = engine.connect()
        columns = SqlModel._get_coldefs(cls)

        table_name = columns.pop("table_name")

        query_str = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        query_str += "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        for key, val in columns.items():
            query_str += f"{key} "
            if isinstance(cls.__dict__[key], str):
                query_str += "TEXT"
            elif isinstance(cls.__dict__[key], int):
                query_str += "INT"
            if val is not None:
                query_str += f" DEFAULT {val}"
            query_str += ", "
        query_str = query_str.rstrip(", ")
        query_str += ");"

        connection.execute(text(query_str))
        connection.close()
        return super().__init_subclass__()

    @classmethod
    def create(cls, fields: dict[str, Any]):
        connection = engine.connect()
        transaction = connection.begin()
        try:
            query_str = f"INSERT INTO {cls.table_name} "
            query_str += "( "
            for key, val in fields.items():
                query_str += f"{key} "
                query_str += ", "
            query_str = query_str.rstrip(", ")
            query_str += ") "

            query_str += "VALUES( "
            for key, val in fields.items():
                query_str += f"'{val}', "
            query_str = query_str.rstrip(", ")
            query_str += ");"

            connection.execute(text(query_str))
            transaction.commit()
        finally:
            connection.close()

    @classmethod
    def select(cls):
        return ORM.from_("users")

    @classmethod
    def drop(cls):
        connection = engine.connect()
        query_str = f"DROP table IF EXISTS {cls.table_name};"
        connection.execute(text(query_str))
        connection.close()


class UserModel(SqlModel):
    table_name: str = "users"
    age: int = 0
    username: str = "bsrodrigue"
    password: str = "password"
