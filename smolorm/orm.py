from typing import Any, Optional
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

    @classmethod
    def from_(cls, table_name):
        obj = cls()
        obj._table = table_name
        return obj

    @classmethod
    def update(cls, table_name: str, fields: Optional[dict[str, Any]] = None):
        obj = cls()
        obj._table = table_name
        if fields is None:
            fields = {}

        query_str = f"UPDATE {obj._table} "
        for key, val in fields.items():
            val = f'"{val}"' if isinstance(val, str) else val
            query_str += f"SET {key} = {val}, "
        query_str = query_str.rstrip(", ")

        obj._sql = query_str
        return obj

    @classmethod
    def create(cls, table_name: str, fields: Optional[dict[str, Any]] = None):
        connection = engine.connect()
        transaction = connection.begin()
        if fields is not None:
            query_str = f"INSERT INTO {table_name} "
            query_str += "("
            for key, val in fields.items():
                query_str += f"{key} "
                query_str += ", "
            query_str = query_str.rstrip(", ")
            query_str += ") "

            query_str += "VALUES("
            for key, val in fields.items():
                query_str += f"'{val}', "
            query_str = query_str.rstrip(", ")
            query_str += ");"
        else:
            query_str = f"INSERT INTO {table_name} "

        connection.execute(text(query_str))
        transaction.commit()
        connection.close()

    @classmethod
    def delete(cls, table_name: str):
        obj = cls()
        obj._table = table_name

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

        try:
            connection = engine.connect()
            results = connection.execute(text(self._sql))
            connection.commit()

            inspection_result = inspection.inspect(engine)
            cols = inspection_result.get_columns(self._table or "")
            cols = [col["name"] for col in cols]

            self._columns = cols if self._columns == ["*"] else self._columns

            rows = []

            for r in results.all():
                rows.append(dict(zip(self._columns, r)))

            return rows
        except Exception:
            return []
