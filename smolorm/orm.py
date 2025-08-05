from typing import Any, Optional, Union
from sqlalchemy import inspection, text
from smolorm.connection import engine
from smolorm.expressions import Expr

# Supported SQL Queries
# SELECT *cols* FROM *table* WHERE *condition* AND/OR *condition* ... [Okay]
# INSERT INTO *table* (*columns*) VALUES(*values*); [Okay]
# UPDATE *table* SET *column* = *value* WHERE *condition* AND/OR *condition* ... [Okay]
# DETELE FROM *table* WHERE *condition* AND/OR *condition* ... [Okay]


class ORM:
    def __init__(self):
        self._table = None
        self._columns = ["*"]
        self._where = None
        self._sql = ""
        self._op = ""

    @classmethod
    def from_(cls, table_name):
        obj = cls()
        obj._table = table_name
        return obj

    @classmethod
    def update(cls, table_name: str, fields: Optional[dict[str, Any]] = None):
        obj = cls()
        obj._table = table_name
        obj._op = "UPDATE"
        if fields is None:
            fields = {}

        query_str = f"UPDATE {obj._table} SET "
        for key, val in fields.items():
            val = f'"{val}"' if isinstance(val, str) else val
            query_str += f"{key} = {val}, "
        query_str = query_str.rstrip(", ")

        obj._sql = query_str
        return obj

    @classmethod
    def create(cls, table_name: str, fields: dict[str, Union[str, int]]) -> int:
        connection = engine.connect()
        transaction = connection.begin()

        columns = ", ".join(fields.keys())
        placeholders = ", ".join([f":{key}" for key in fields.keys()])
        query_str = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        cursor = connection.execute(text(query_str), fields)
        transaction.commit()
        connection.close()
        return cursor.lastrowid

    @classmethod
    def delete(cls, table_name: str):
        obj = cls()
        obj._table = table_name
        obj._op = "DELETE"

        obj._sql = f"DELETE FROM {table_name} "

        return obj

    def select(self, *cols):
        self._columns = cols or ["*"]
        self._sql += f"SELECT {', '.join(self._columns)} FROM {self._table}"
        return self

    def where(self, expr: Expr):
        self._where = expr
        return self

    def order_by(self, column: str, descending: bool = False):
        self._sql += f" ORDER BY {column} {'DESC' if descending else 'ASC'}"
        return self

    def limit(self, n: int):
        self._sql += f" LIMIT {n}"
        return self

    def offset(self, n: int):
        self._sql += f" OFFSET {n}"
        return self

    def run(self):
        if self._where:
            self._sql += f" WHERE {self._where.to_sql()}"

        connection = engine.connect()
        cursor = connection.execute(text(self._sql))
        connection.commit()

        if self._op == "DELETE" or self._op == "UPDATE":
            return cursor.lastrowid

        inspection_result = inspection.inspect(engine)
        cols = inspection_result.get_columns(self._table or "")
        cols = [col["name"] for col in cols]

        self._columns = cols if self._columns == ["*"] else self._columns

        rows = []

        for r in cursor.all():
            rows.append(dict(zip(self._columns, r)))

        return rows
