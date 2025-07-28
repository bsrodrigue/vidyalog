from typing import Any


class FilterExpressionEvaluator:
    @staticmethod
    def evaluate(entity: Any, filters: dict[str, Any]) -> bool:
        for key, expected in filters.items():
            attr_path = key.split("__")
            attr_name = attr_path[0]
            op = attr_path[1] if len(attr_path) > 1 else "eq"

            actual = getattr(entity, attr_name, None)

            if not FilterExpressionEvaluator._compare(actual, expected, op):
                return False
        return True

    @staticmethod
    def _compare(actual: Any, expected: Any, op: str) -> bool:
        if op == "isnull":
            return actual is None

        if op == "in":
            return actual in expected

        if op == "notin":
            return actual not in expected

        if op == "neq":
            return actual != expected

        if actual is None:
            return False

        match op:
            case "eq":
                return actual == expected
            case "lt":
                return actual < expected
            case "lte":
                return actual <= expected
            case "gt":
                return actual > expected
            case "gte":
                return actual >= expected
            case "contains":
                return expected in actual
            case "icontains":
                return str(expected).lower() in str(actual).lower()
            case "startswith":
                return str(actual).startswith(str(expected))
            case "istartswith":
                return str(actual).lower().startswith(str(expected).lower())
            case "endswith":
                return str(actual).endswith(str(expected))
            case "iendswith":
                return str(actual).lower().endswith(str(expected).lower())
            case _:
                raise ValueError(f"Unsupported filter operator: {op}")
