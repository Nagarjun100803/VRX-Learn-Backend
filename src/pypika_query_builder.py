from pypika import Table, Order
from pypika.queries import Selectable
from pypika.terms import Function, AggregateFunction
from enum import Enum



class JsonbBuildObject(Function):
    def __init__(self, *args):
        super().__init__("JSONB_BUILD_OBJECT", *args)


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
    left_lateral  = "LEFT JOIN LATERAL"
    inner_lateral = "JOIN LATERAL"


class CutsomOrder(Enum):
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
    


user_table = Table("users", alias="u")
course_table = Table("courses", alias="c")
module_table = Table("modules", alias="m")
lesson_table = Table("lessons", alias="l")
enrollment_table = Table("enrollments", alias="e")
assignment_table = Table("assignments", alias="a")
assignment_submission_table = Table("assignment_submissions", alias="asub")
media_asset_table = Table("media_assets", alias="me")
