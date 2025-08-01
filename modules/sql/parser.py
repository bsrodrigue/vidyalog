class Expr:
    def to_sql(self):
        raise NotImplementedError()


class BinaryExpr(Expr):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def to_sql(self):
        right = f"'{self.right}'" if isinstance(self.right, str) else str(self.right)
        return f"{self.left} {self.op} {right}"

    def __and__(self, other):
        return AndExpr(self, other)

    def __or__(self, other):
        return OrExpr(self, other)


class Column(Expr):
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):  # type: ignore[override]
        return BinaryExpr(self.name, "=", other)

    def __ne__(self, other):  # type: ignore[override]
        return BinaryExpr(self.name, "!=", other)

    def __lt__(self, other):
        return BinaryExpr(self.name, "<", other)

    def __le__(self, other):
        return BinaryExpr(self.name, "<=", other)

    def __gt__(self, other):
        return BinaryExpr(self.name, ">", other)

    def __ge__(self, other):
        return BinaryExpr(self.name, ">=", other)

    def contains(self, val):
        return FuncExpr(self.name, "LIKE", f"%{val}%")

    def startswith(self, val):
        return FuncExpr(self.name, "LIKE", f"{val}%")

    def endswith(self, val):
        return FuncExpr(self.name, "LIKE", f"%{val}")

    def to_sql(self):
        return self.name


class AndExpr(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_sql(self):
        return f"({self.left.to_sql()} AND {self.right.to_sql()})"


class OrExpr(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_sql(self):
        return f"({self.left.to_sql()} OR {self.right.to_sql()})"


class FuncExpr(Expr):
    def __init__(self, column, op, pattern):
        self.column = column
        self.op = op
        self.pattern = pattern

    def to_sql(self):
        return f"{self.column} {self.op} '{self.pattern}'"

    def __and__(self, other):
        return AndExpr(self, other)

    def __or__(self, other):
        return OrExpr(self, other)


def col(name):
    return Column(name)


class ORM:
    def __init__(self):
        self._table = None
        self._columns = ["*"]
        self._where = None

    @classmethod
    def from_(cls, table_name):
        obj = cls()
        obj._table = table_name
        return obj

    def select(self, *cols):
        self._columns = cols or ["*"]
        return self

    def where(self, expr: Expr):
        self._where = expr
        return self

    def run(self):
        sql = f"SELECT {', '.join(self._columns)} FROM {self._table}"
        if self._where:
            sql += f" WHERE {self._where.to_sql()}"
        print("Generated SQL:", sql)
        return sql  # In real use: execute this against SQLite
