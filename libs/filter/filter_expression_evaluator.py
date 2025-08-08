from functools import reduce
from typing import Any

from modules.repositories.abstract_repository import FilterOp, FilterQuery
from smolorm.expressions import Expr, col


class FilterExpressionEvaluator:
    @staticmethod
    def evaluate(entity: Any, filters: list[FilterQuery]) -> bool:
        for f in filters:
            column = f.column
            op = f.op
            value = f.value

            actual = getattr(entity, column, None)

            if not FilterExpressionEvaluator._compare(actual, value, op):
                return False
        return True

    @staticmethod
    def chain_filter_queries_to_sql_query(filters: list[FilterQuery]) -> Expr:
        filter_expressions: list[Any] = [
            FilterExpressionEvaluator.filter_query_to_sql_query(f) for f in filters
        ]

        final_expression: Expr = reduce(lambda x, y: (x) & (y), filter_expressions)

        return final_expression

    @staticmethod
    def filter_query_to_sql_query(filter: FilterQuery) -> Expr:
        column = filter.column
        op = filter.op
        value = filter.value

        match op:
            case FilterOp.CONTAINS:
                return col(column).contains(str(value))
            case FilterOp.ICONTAINS:
                return col(column).contains(str(value).lower())
            case FilterOp.STARTS_WITH:
                return col(column).startswith(value)
            case FilterOp.ISTARTS_WITH:
                return col(column).startswith(str(value).lower())
            case FilterOp.ENDS_WITH:
                return col(column).endswith(value)
            case FilterOp.IENDS_WITH:
                return col(column).endswith(str(value).lower())
            case FilterOp.IN:
                return col(column).in_(value)
            case FilterOp.NOT_IN:
                return col(column).not_in_(value)
            case FilterOp.EQ:
                if value is None or value == "NULL" or value == "null":
                    return col(column).null_()
                return col(column) == value
            case FilterOp.NEQ:
                if value is None or value == "NULL" or value == "null":
                    return col(column).not_null_()
                return col(column) != value
            case FilterOp.LT:
                return col(column) < value
            case FilterOp.LTE:
                return col(column) <= value
            case FilterOp.GT:
                return col(column) > value
            case FilterOp.GTE:
                return col(column) >= value
            case _:
                raise ValueError(f"Unsupported operator: {op}")

    @staticmethod
    def _compare(actual: Any, expected: Any, op: FilterOp) -> bool:
        match op:
            case FilterOp.EQ:
                return actual == expected
            case FilterOp.NEQ:
                return actual != expected
            case FilterOp.LT:
                return actual < expected
            case FilterOp.LTE:
                return actual <= expected
            case FilterOp.GT:
                return actual > expected
            case FilterOp.GTE:
                return actual >= expected
            case FilterOp.CONTAINS:
                return expected in actual
            case FilterOp.ICONTAINS:
                return str(expected).lower() in str(actual).lower()
            case FilterOp.STARTS_WITH:
                return str(actual).startswith(str(expected))
            case FilterOp.ISTARTS_WITH:
                return str(actual).lower().startswith(str(expected).lower())
            case FilterOp.ENDS_WITH:
                return str(actual).endswith(str(expected))
            case FilterOp.IENDS_WITH:
                return str(actual).lower().endswith(str(expected).lower())
            case FilterOp.IN:
                return actual in expected
            case FilterOp.NOT_IN:
                return actual not in expected
            case _:
                raise ValueError(f"Unsupported filter operator: {op}")
