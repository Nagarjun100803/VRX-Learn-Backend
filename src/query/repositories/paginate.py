import asyncio
from typing import Any, Type, TypeVar

from pypika import PostgreSQLQuery, functions as fn
from pypika.queries import QueryBuilder

from src.database import AsyncPgDBManager
from src.query.dto.base import BaseDTO, PageMeta, Paginated


T = TypeVar("T", bound=BaseDTO)


class PaginatorMixin:
    
    async def paginate_query(
        self,
        sql: QueryBuilder,
        values: tuple[Any, ...],
        dto_class: Type[T],
        page_meta: PageMeta
    ) -> Paginated[T]:

        count_sql = PostgreSQLQuery\
            .from_(sql)\
            .select(
                fn.Count("*").as_("total")
            )
        
        # Apply limit and offset.
        sql = sql.offset(page_meta.offset).limit(page_meta.limit)
        
        self.db: AsyncPgDBManager # Add a type hint to get IDE support.
        executable = self.db.query_builder.build_executable(sql=sql.get_sql(), values=values)
        
        count_executable = self.db.query_builder.build_executable(sql=count_sql.get_sql(), values=values)
        
        result, count_of_items = await asyncio.gather(
            self.db.execute(executable, fetch_returns="all"),
            self.db.execute(count_executable, fetch_returns="one")
        )
        
        dto_class: BaseDTO
        data = [
            dto_class.model_validate(dict(r))
            for r in result
        ]
        
        total_items = count_of_items["total"]
        
        return Paginated[dto_class](
            data=data,
            page=page_meta.page,
            limit=page_meta.limit,
            total_items=total_items
        )
        

        