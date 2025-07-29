from typing import Dict, Any
from tinydb import Query, where
from datetime import datetime
from enum import Enum  # Added Enum import to handle enum values in filters correctly


class TinyDBQueryBuilder:
    """
    A utility class to build TinyDB queries from a dictionary of filters.
    Filters are expected in the format "field_name__operator": value.

    Supported operators:
    - eq: equals (default if no operator specified)
    - neq: not equals
    - lt: less than
    - lte: less than or equal to
    - gt: greater than
    - gte: greater than or equal to
    - isnull: checks if the field exists (False for is_not_null, True for is_null)
    - in: value is one of the expected values (expected should be a list/tuple)
    - notin: value is not one of the expected values (expected should be a list/tuple)
    - contains: string/list contains expected (case-sensitive for strings)
    - icontains: string contains expected (case-insensitive)
    - startswith: string starts with expected (case-sensitive)
    - istartswith: string starts with expected (case-insensitive)
    - endswith: string ends with with expected (case-sensitive)
    - iendswith: string ends with expected (case-insensitive)
    """

    @staticmethod
    def build_tinydb_query(filters: Dict[str, Any]) -> Query:
        """
        Builds a TinyDB Query object from a dictionary of filters.

        Args:
            filters (Dict[str, Any]): A dictionary where keys are filter strings
                                      (e.g., "name__eq", "age__gt") and values
                                      are the expected comparison values.

        Returns:
            Query: A TinyDB Query object representing the combined conditions.
                   Returns Query().noop() if no filters are provided, effectively matching all documents.

        Raises:
            ValueError: If an unsupported filter operator is encountered,
                        or if 'in'/'notin' operators receive non-list/tuple expected values.
        """
        query_conditions = []  # Accumulates individual TinyDB query conditions

        for key, expected in filters.items():
            parts = key.split("__")
            attr = parts[0]
            op = parts[1] if len(parts) > 1 else "eq"  # Default operator is 'eq'

            condition = None
            q_attr = where(attr)  # Create the query object for the attribute

            # Normalize expected values for comparison, especially for datetime and Enum
            expected_for_query = expected
            if isinstance(expected, datetime):
                expected_for_query = expected.isoformat()
            elif isinstance(expected, Enum):
                expected_for_query = expected.value

            match op:
                case "eq":
                    condition = q_attr == expected_for_query
                case "neq":
                    condition = q_attr != expected_for_query
                case "lt":
                    # Use .test() with a lambda to safely handle potential None values
                    # and ensure comparison is only done if the value exists and is comparable.
                    condition = q_attr.test(
                        lambda v: v is not None and v < expected_for_query
                    )
                case "lte":
                    condition = q_attr.test(
                        lambda v: v is not None and v <= expected_for_query
                    )
                case "gt":
                    condition = q_attr.test(
                        lambda v: v is not None and v > expected_for_query
                    )
                case "gte":
                    condition = q_attr.test(
                        lambda v: v is not None and v >= expected_for_query
                    )
                case "isnull":
                    # TinyDB's .exists() checks if a key exists AND its value is NOT None.
                    # If expected is True, we want documents where the field is missing or None.
                    # This is achieved by negating .exists(): `~q_attr.exists()`.
                    # If expected is False, we want documents where the field exists and is not None.
                    # This is simply `q_attr.exists()`.
                    condition = ~q_attr.exists() if expected else q_attr.exists()
                case "in":
                    if not isinstance(expected, (list, tuple)):
                        raise ValueError(
                            f"For 'in' operator, expected value must be a list or tuple. Got {type(expected)}"
                        )
                    condition = q_attr.one_of(expected)
                case "notin":
                    if not isinstance(expected, (list, tuple)):
                        raise ValueError(
                            f"For 'notin' operator, expected value must be a list or tuple. Got {type(expected)}"
                        )
                    condition = q_attr.not_in(expected)
                case "contains":
                    condition = q_attr.test(
                        lambda v: expected in v if isinstance(v, (str, list)) else False
                    )
                case "icontains":
                    condition = q_attr.test(
                        lambda v: (
                            isinstance(v, str) and str(expected).lower() in v.lower()
                        )
                    )
                case "startswith":
                    condition = q_attr.test(
                        lambda v: (isinstance(v, str) and v.startswith(str(expected)))
                    )
                case "istartswith":
                    condition = q_attr.test(
                        lambda v: (
                            isinstance(v, str)
                            and v.lower().startswith(str(expected).lower())
                        )
                    )
                case "endswith":
                    condition = q_attr.test(
                        lambda v: (isinstance(v, str) and v.endswith(str(expected)))
                    )
                case "iendswith":
                    condition = q_attr.test(
                        lambda v: (
                            isinstance(v, str)
                            and v.lower().endswith(str(expected).lower())
                        )
                    )
                case _:
                    raise ValueError(f"Unsupported filter operator: {op}")

            if condition is not None:
                query_conditions.append(condition)

        # Combine all conditions with logical AND
        if not query_conditions:
            return (
                Query().noop()
            )  # If no filters, return a query that matches all documents

        # Chain all conditions using the bitwise AND operator (&)
        final_query = query_conditions[0]
        for cond in query_conditions[1:]:
            final_query &= cond

        return final_query
