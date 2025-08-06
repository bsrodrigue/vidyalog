from typing import Union
from sqlalchemy import inspection, text
from smolorm.connection import engine
from smolorm.expressions import Expr

# Supported SQL Queries
# SELECT *cols* FROM *table* WHERE *condition* AND/OR *condition* ... [Okay]
# INSERT INTO *table* (*columns*) VALUES(*values*); [Okay]
# UPDATE *table* SET *column* = *value* WHERE *condition* AND/OR *condition* ... [Okay]
# DETELE FROM *table* WHERE *condition* AND/OR *condition* ... [Okay]


class ORM:
    """
    Basic ORM State Machine for SmolORM
    """

    def __init__(self):
        self._table = None
        self._columns = ["*"]
        self._where = None
        self._sql = ""
        self._lastopflag: str = "INIT"
        self._is_create: bool = False
        self._is_update: bool = False
        self._is_delete: bool = False

    @classmethod
    def from_(cls, table_name):
        obj = cls()
        obj._table = table_name
        return obj

    def update(self, fields: dict[str, Union[str, int]]):
        self._lastopflag = "UPDATE"
        self._is_update = True

        query_str = f"UPDATE {self._table} SET "
        for key, val in fields.items():
            val = f'"{val}"' if isinstance(val, str) else val
            query_str += f"{key} = {val}, "
        query_str = query_str.rstrip(", ")

        self._sql = query_str
        return self

    def create(self, fields: dict[str, Union[str, int]]) -> int:
        self._is_create = True
        connection = engine.connect()
        transaction = connection.begin()

        columns = ", ".join(fields.keys())
        placeholders = ", ".join([f":{key}" for key in fields.keys()])
        query_str = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})"

        cursor = connection.execute(text(query_str), fields)
        transaction.commit()
        connection.close()
        return cursor.lastrowid

    def delete(self):
        self._is_delete = True
        self._lastopflag = "DELETE"

        self._sql = f"DELETE FROM {self._table} "

        return self

    def select(self, *cols):
        self._lastopflag = "SELECT"
        self._columns = cols or ["*"]
        self._sql += f"SELECT {', '.join(self._columns)} FROM {self._table}"
        return self

    def where(self, expr: Expr):
        self._lastopflag = "WHERE"
        self._sql += f" WHERE {expr.to_sql()}"
        return self

    def order_by(self, column: str, descending: bool = False):
        self._lastopflag = "ORDER_BY"
        self._sql += f" ORDER BY {column} {'DESC' if descending else 'ASC'}"
        return self

    def limit(self, n: int):
        self._lastopflag = "LIMIT"
        self._sql += f" LIMIT {n}"
        return self

    def offset(self, n: int):
        self._lastopflag = "OFFSET"
        self._sql += f" OFFSET {n}"
        return self

    def run(self):
        connection = engine.connect()
        cursor = connection.execute(text(self._sql))
        connection.commit()

        if self._is_delete or self._is_update or self._is_create:
            return []
            # return cursor.lastrowid

        inspection_result = inspection.inspect(engine)
        cols = inspection_result.get_columns(self._table or "")
        cols = [col["name"] for col in cols]

        self._columns = cols if self._columns == ["*"] else self._columns

        rows = []

        for r in cursor.all():
            rows.append(dict(zip(self._columns, r)))

        return rows
