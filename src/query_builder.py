from enum import Enum

from pypika import Order, Table
from pypika.queries import Selectable
from pypika.terms import AggregateFunction, Function
from pypika.utils import format_quotes


class JsonbBuildObject(Function):
    def __init__(self, *args):
        super().__init__("JSONB_BUILD_OBJECT", *args)


class RowToJson(Function):
    """
    ROW_TO_JSON(table_alias)

    Converts a whole row to JSON.
    Accepts a Table object and renders only the alias, not "table_name" "alias".

    Usage:
        RowToJson(user)          → ROW_TO_JSON("u")
        RowToJson(user_table)    → ROW_TO_JSON("u")
    """

    def __init__(self, table):
        super().__init__("ROW_TO_JSON", table)
        self.table = table

    def get_function_sql(self, **kwargs) -> str:
        # Extract just the alias (or table name if no alias)
        quote_char = kwargs.get("quote_char", '"')
        alias = getattr(self.table, "alias", None) or getattr(
            self.table, "_table_name", None
        )
        table_sql = format_quotes(alias, quote_char)
        return f"ROW_TO_JSON({table_sql})"


class JsonbAgg(AggregateFunction):
    def __init__(self, term):
        super().__init__("JSONB_AGG", term)
        self._order_by = []

    def orderby(self, *fields, **kwargs):
        """
        Usage:
            JsonbAgg(table.field).orderby(table.created_at, order=Order.desc)
        """
        order = kwargs.get("order", Order.asc)
        for field in fields:
            self._order_by.append((field, order))
        return self

    def get_special_params_sql(self, **kwargs):
        # Renders: ORDER BY field ASC/DESC inside the aggregate
        if not self._order_by:
            return None
        order_clauses = ", ".join(
            f"{field.get_sql(**kwargs)} {order.value.upper()}"
            for field, order in self._order_by
        )
        return f"ORDER BY {order_clauses}"


class PGJoinType(Enum):
    """
    PostgreSQL-specific join types not supported natively by PyPika.
    Pass via the how= parameter in .join().
    """

    left_lateral = "LEFT JOIN LATERAL"
    inner_lateral = "JOIN LATERAL"


class PGSqlTypes:
    JSONB = "jsonb"


class CustomOrder(Enum):
    """
    Enum for ordering in queries.
    Mimics pypika.enums.Order but adds NULLS FIRST and NULLS LAST options.
    """

    asc = "ASC"
    desc = "DESC"
    asc_nulls_first = "ASC NULLS FIRST"
    asc_nulls_last = "ASC NULLS LAST"
    desc_nulls_first = "DESC NULLS FIRST"
    desc_nulls_last = "DESC NULLS LAST"


class LateralQuery(Selectable):
    def __init__(self, query, alias: str):
        super().__init__(alias=alias)
        self.query = query

    def get_sql(self, **kwargs) -> str:
        kwargs.pop("subquery", None)  # ← prevent duplicate kwarg collision
        kwargs.pop("with_alias", None)  # ← same issue can happen with this
        inner = self.query.get_sql(subquery=True, **kwargs)
        return f"{inner} {self.alias}"


user_table = Table("users")
course_table = Table("courses")
module_table = Table("modules")
lesson_table = Table("lessons")
enrollment_table = Table("enrollments")
assignment_table = Table("assignments")
assignment_submission_table = Table("assignment_submissions")
media_asset_table = Table("media_assets")
issue_table = Table("issues")
module_restriction_table = Table("module_restriction")
