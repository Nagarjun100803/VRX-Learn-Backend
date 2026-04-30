import asyncio
import csv
import io
from typing import Any, AsyncGenerator, Type, TypeVar

from pypika import PostgreSQLQuery
from pypika import functions as fn
from pypika.queries import QueryBuilder

from src.database import AsyncPgDBManager, ExecutableSQL
from src.query.dto.base import BaseDTO, PageMeta, Paginated

T = TypeVar("T", bound=BaseDTO)


class PaginatorMixin:
    async def paginate_query(
        self,
        sql: QueryBuilder,
        values: tuple[Any, ...],
        dto_class: Type[T],
        page_meta: PageMeta,
    ) -> Paginated[T]:

        count_sql = PostgreSQLQuery.from_(sql).select(fn.Count("*").as_("total"))

        # Apply limit and offset.
        sql = sql.offset(page_meta.offset).limit(page_meta.limit)

        self.db: AsyncPgDBManager  # Add a type hint to get IDE support.

        executable = ExecutableSQL(sql=sql.get_sql(), values=values)

        count_executable = ExecutableSQL(sql=count_sql.get_sql(), values=values)

        result, count_of_items = await asyncio.gather(
            self.db.execute(executable, fetch_returns="all"),
            self.db.execute(count_executable, fetch_returns="one"),
        )

        data = [dto_class.model_validate(dict(r)) for r in result]

        total_items = count_of_items["total"] if count_of_items else 0

        return Paginated[dto_class](
            data=data,
            page=page_meta.page,
            limit=page_meta.limit,
            total_items=total_items,
        )


class ExportMixin:
    async def _stream_dto(
        self, sql: QueryBuilder, values: tuple[Any, ...], dto_class: Type[T]
    ) -> AsyncGenerator[T, None]:

        self.db: AsyncPgDBManager  # Add a type hint to get IDE support.
        executable = ExecutableSQL(sql=sql.get_sql(), values=values)

        async for row in self.db.stream(executable):
            yield dto_class.model_validate(dict(row))

    async def _serialize_csv(
        self, rows: AsyncGenerator[T, None]
    ) -> AsyncGenerator[bytes, None]:
        """
        Convert streamed DTOs into CSV chunks.
        """

        buffer = io.StringIO()
        writer = None

        async for row in rows:
            row_dict = row.model_dump(by_alias=True)
            # Initalize the writer if not None.
            if writer is None:
                writer = csv.DictWriter(buffer, fieldnames=row_dict.keys())
                writer.writeheader()  # Write the column names.

            # Write the actual row.
            writer.writerow(row_dict)

            yield buffer.getvalue().encode("utf-8-sig")

            buffer.seek(0)
            buffer.truncate(0)

    async def export(
        self, sql: QueryBuilder, values: tuple[Any, ...], dto_class: Type[T]
    ) -> AsyncGenerator[bytes, None]:

        dto_stream = self._stream_dto(sql=sql, values=values, dto_class=dto_class)

        async for chunk in self._serialize_csv(dto_stream):
            yield chunk
