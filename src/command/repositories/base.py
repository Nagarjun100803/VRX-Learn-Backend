from abc import ABC, abstractmethod
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
    overload,
)

from asyncpg import Connection, Record
from pydantic import BaseModel, ValidationError
from pypika import Parameter, PostgreSQLQuery, functions
from pypika.queries import Table
from pypika.terms import Criterion, ExistsCriterion, ValueWrapper

from src.database import AsyncPgDBManager, ExecutableSQL

NC = TypeVar("NC", bound=BaseModel)
# NC -> Normalized Command type.


def prepare_insert_query(
    table: Union[str, Table], cmd: BaseModel
) -> tuple[str, tuple[Any, ...]]:

    table = Table(table) if isinstance(table, str) else table
    data_dict = cmd.model_dump(exclude_none=True)
    insert_query = PostgreSQLQuery.into(table)

    insert_query = insert_query.columns(*data_dict.keys())
    # Add parameters
    insert_query = insert_query.insert(
        *[Parameter(f"${idx}") for idx, _ in enumerate(data_dict.values(), start=1)]
    )
    insert_query: Any = insert_query.returning("*")

    sql: str = insert_query.get_sql()

    return sql, tuple(data_dict.values())


class BaseRepository[T](ABC):
    """
    Base repository class providing common CRUD operations.
    Don't instantiate this class directly; use a subclass instead.
    """

    tablename: ClassVar[str] = "base"

    def __init__(self, db: AsyncPgDBManager):
        self.db = db

    def _normalize(self, cmd: BaseModel, model: type[NC]) -> NC:
        """Normalizes the command object to the specified type."""
        if not isinstance(cmd, model):
            cmd = model.model_validate(cmd)
        return cast(NC, cmd)

    def _normalize_one_of(self, cmd: BaseModel, models: Sequence[type[NC]]) -> NC:
        """Normalizes the command object to one of the specified types."""

        for model in models:
            if isinstance(cmd, model):
                return cmd

            # Try to validate the command against the model.
            try:
                return model.model_validate(cmd)
            except ValidationError:
                continue  # Continue to the next model if validation fails.

        raise ValueError(
            f"Command object does not match any of the specified models: {models}"
        )

    @abstractmethod
    def _to_domain(self, row: Optional[Record]) -> Optional[T]:
        "Converts raw database record to Domain object."

    def _validate_id(self, id: Any) -> int:
        "Validates the id value and returns if it is an integer."
        if id is None or not isinstance(id, int):
            raise ValueError(f"Cannot get a record without a valid id. {id}")
        return id

    @abstractmethod
    async def add(self, cmd: BaseModel, connection: Optional[Connection]) -> T:
        "Adds a new record to the database."
        table = Table(self.tablename)

        sql, params = prepare_insert_query(table, cmd)

        executable = ExecutableSQL(sql=sql, values=params)

        result = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )
        return cast(T, self._to_domain(result))

    @abstractmethod
    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[T]:
        "Updates an existing record in the database."

        table = Table(self.tablename)
        id = self._validate_id(getattr(cmd, "id"))

        data_dict = cmd.model_dump(exclude={"id"}, exclude_none=True)
        update_query = PostgreSQLQuery.update(table).where(
            Criterion.all(
                terms=[table.id == Parameter("$1"), table.deleted_at.isnull()]
            )
        )

        values = [id]
        for idx, col in enumerate(data_dict.keys(), start=2):
            update_query = update_query.set(col, Parameter(f"${idx}"))
            values.append(data_dict[col])

        # Set updated_at to current timestamp
        update_query = update_query.set("updated_at", functions.Now())
        update_query: Any = update_query.returning("*")  # type: ignore
        sql: str = update_query.get_sql()

        executable = ExecutableSQL(sql=sql, values=tuple(values))

        result = await self.db.execute(executable, fetch_returns="one")

        return self._to_domain(result)

    @abstractmethod
    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[T]:
        """
        Deletes a record from the database.
        """

        table = Table(self.tablename)

        id = self._validate_id(getattr(cmd, "id"))
        deleted_by = self._validate_id(getattr(cmd, "deleted_by"))

        delete_query = (
            PostgreSQLQuery.update(table)
            .set("deleted_at", functions.Now())
            .set("deleted_by", deleted_by)
            .where(
                Criterion.all(
                    terms=[table.id == Parameter("$1"), table.deleted_at.isnull()]
                )
            )
        )
        delete_query: Any = delete_query.returning("*")
        sql: str = delete_query.get_sql()
        executable = ExecutableSQL(sql=sql, values=(id,))

        result = await self.db.execute(executable, fetch_returns="one")

        return self._to_domain(result)

    @abstractmethod
    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[T]:
        """
        Retrieves a single record from the database.
        """

        id = self._validate_id(getattr(query, "id"))

        table = Table(self.tablename)
        sql = (
            PostgreSQLQuery.from_(table)
            .select("*")
            .where(
                Criterion.all(
                    terms=[table.id == Parameter("$1"), table.deleted_at.isnull()]
                )
            )
        )

        executable = ExecutableSQL(sql=sql.get_sql(), values=(id,))

        result = await self.db.execute(executable, fetch_returns="one")

        return self._to_domain(result)

    @overload
    async def pick(
        self,
        columns: Sequence[str],
        fetch_all: Literal[False],
        connection: Optional[Connection] = None,
        **filters: Any,
    ) -> Optional[Record]: ...

    @overload
    async def pick(
        self,
        columns: Sequence[str],
        fetch_all: Literal[True],
        connection: Optional[Connection] = None,
        **filters: Any,
    ) -> list[Record]: ...

    async def pick(
        self,
        columns: Sequence[str],
        fetch_all: bool = False,
        connection: Optional[Connection] = None,
        **filters: Any,
    ) -> Union[Optional[Record], list[Record]]:

        table = Table(self.tablename)
        sql = PostgreSQLQuery.from_(table).select(*columns)

        for idx, col in enumerate(filters, start=1):
            sql = sql.where(table.field(col) == Parameter(f"${idx}"))

        executable = ExecutableSQL(sql=sql.get_sql(), values=tuple(filters.values()))
        result = await self.db.execute(
            executable,
            fetch_returns="one" if not fetch_all else "all",
            connection=connection,
        )
        return result

    async def exists_by(
        self, connection: Optional[Connection] = None, **filters: Any
    ) -> bool:
        """
        Checks if a record exists in the database based on the given filters.
        """
        table = Table(self.tablename)

        filter_query = (
            PostgreSQLQuery.from_(table)
            .select(ValueWrapper(1))
            .where(
                Criterion.all(
                    terms=[table.deleted_at.isnull()]
                    + [
                        table.field(col) == Parameter(f"${idx}")
                        for idx, col in enumerate(filters, start=1)
                    ]
                )
            )
        )

        sql = PostgreSQLQuery.select(ExistsCriterion(filter_query).as_("exists"))
        executable = ExecutableSQL(sql=sql.get_sql(), values=tuple(filters.values()))

        result = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        if result is None:
            return False
        return result["exists"]
