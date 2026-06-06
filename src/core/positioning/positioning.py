from typing import Any, Optional, Self, cast

from asyncpg import Record
from fractional_indexing import generate_key_between
from pydantic import model_validator
from pypika import Criterion, PostgreSQLQuery, Table
from pypika import functions as fn
from pypika.terms import ValueWrapper

from src.command.commands.base import BaseCmd
from src.database import AsyncPgDBManager, ExecutableSQL
from src.exceptions import EntityNotFoundError, ValidationError
from src.pypika_query_builder import PGSqlTypes, RowToJson


class ReorderParticipants(BaseCmd):
    preceding_id: Optional[int] = None
    target_id: int
    succeeding_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_participants(self) -> Self:
        if self.preceding_id is None and self.succeeding_id is None:
            raise ValueError("Either preceding_id or succeeding_id must be provided.")
        return self


class ParticipantMeta(BaseCmd):
    id: int
    position_string: str
    scope: str
    scope_id: int


class ReorderParticipantsMeta(BaseCmd):
    preceding: Optional[ParticipantMeta] = None
    target: Optional[ParticipantMeta] = None
    succeeding: Optional[ParticipantMeta] = None


class PositioningService:
    def __init__(self, db: AsyncPgDBManager) -> None:
        self.db = db

    async def reorder(
        self, participants: ReorderParticipants, tablename: str, scope: str
    ) -> str:

        participants_meta = await self._get_reorder_participants(
            participants=participants, tablename=tablename, scope=scope
        )

        # Validate participants meta data.
        self._validate_participants(
            participants=participants, participants_meta=participants_meta
        )

        preceding_position = (
            participants_meta.preceding.position_string
            if participants_meta.preceding
            else None
        )
        succeeding_position = (
            participants_meta.succeeding.position_string
            if participants_meta.succeeding
            else None
        )

        print(f"preceding position: {preceding_position}")
        print(f"succeeding position: {succeeding_position}")

        # Calculate a new key for target.
        new_position_string = self._get_new_position_string(
            preceding_position, succeeding_position
        )

        print(f"new position: {new_position_string}")
        # Update the position.
        updated_position = await self._update_position(
            target_id=participants.target_id,
            position_string=new_position_string,
            tablename=tablename,
        )

        if updated_position is None:
            raise EntityNotFoundError(
                value=participants.target_id, alias="Target participant"
            )

        return updated_position.get("position_string", "'")

    async def generate_position(self, tablename: str, scope: str, scope_id: int) -> str:

        max_position_string = await self._get_max_position_string(
            tablename=tablename, scope=scope, scope_id=scope_id
        )

        print(max_position_string)
        new_position_string = self._get_new_position_string(
            preceding_string=max_position_string, succeeding_string=None
        )

        return new_position_string

    def _get_new_position_string(
        self, preceding_string: Optional[str], succeeding_string: Optional[str]
    ) -> str:

        try:
            return generate_key_between(preceding_string, succeeding_string)
        except Exception as e:
            print("Error occur while generating new position string.")
            raise e

    def _validate_preceding(
        self,
        preceding_id: Optional[int],
        preceding_meta: Optional[ParticipantMeta],
        target_meta: ParticipantMeta,
    ) -> None:

        if preceding_id is not None and preceding_meta is None:
            raise EntityNotFoundError(
                message=f"Preceding participant not found with this ID : {preceding_id}"
            )
        if preceding_meta is not None:
            if preceding_meta.scope_id != target_meta.scope_id:
                raise ValidationError(
                    message=f"Preceding participant belongs to a different {preceding_meta.scope}."
                )

    def _validate_succeeding(
        self,
        succeeding_id: Optional[int],
        succeeding_meta: Optional[ParticipantMeta],
        target_meta: ParticipantMeta,
    ) -> None:

        if succeeding_id is not None and succeeding_meta is None:
            raise EntityNotFoundError(
                message=f"Succeeding participant not found with this ID : {succeeding_id}"
            )
        if succeeding_meta is not None:
            if succeeding_meta.scope_id != target_meta.scope_id:
                raise ValidationError(
                    message=f"Suceeding participant belongs to a different {succeeding_meta.scope}."
                )

    def _validate_participants(
        self,
        participants: ReorderParticipants,
        participants_meta: ReorderParticipantsMeta,
    ) -> None:

        if participants_meta.target is None:
            raise EntityNotFoundError(
                message=f"Target participant not found with this ID: {participants.target_id}"
            )

        self._validate_preceding(
            preceding_id=participants.preceding_id,
            preceding_meta=participants_meta.preceding,
            target_meta=participants_meta.target,
        )

        self._validate_succeeding(
            succeeding_id=participants.succeeding_id,
            succeeding_meta=participants_meta.succeeding,
            target_meta=participants_meta.target,
        )

        if participants_meta.preceding is None and participants_meta.succeeding is None:
            raise ValidationError(
                message=(
                    "No record found for both preceding_id and succeeding_id."
                    "At least one of them must exist."
                )
            )

    async def _update_position(
        self, target_id: int, position_string: str, tablename: str
    ) -> Optional[Record]:

        table = Table(tablename)
        update_query = (
            PostgreSQLQuery.update(table)
            .set(table.position_string, position_string)
            .where(table.id == target_id)
        )

        query: Any = update_query.returning(table.position_string)  # type: ignore
        sql: str = query.get_sql()

        executable = ExecutableSQL(sql=sql, values=tuple())

        return await self.db.execute(executable, fetch_returns="one")

    async def _get_reorder_participants(
        self, participants: ReorderParticipants, tablename: str, scope: str
    ) -> ReorderParticipantsMeta:

        table = Table(tablename)

        participant_query = (
            PostgreSQLQuery.from_(table)
            .where(
                Criterion.all(
                    terms=[
                        table.deleted_at.isnull(),
                        table.id.isin(
                            [
                                participants.preceding_id,
                                participants.target_id,
                                participants.succeeding_id,
                            ]
                        ),
                    ]
                )
            )
            .select(
                table.id,
                table.position_string,
                table.field(scope).as_("scope_id"),
                ValueWrapper(scope).as_("scope"),
            )
        )

        participant_cte = Table("participant_cte")  # Reference table

        sql = (
            PostgreSQLQuery.with_(participant_query, participant_cte._table_name)
            .select(
                PostgreSQLQuery.from_(participant_cte)
                .where(participant_cte.id == participants.preceding_id)
                .select(
                    fn.Cast(RowToJson(participant_cte), PGSqlTypes.JSONB).as_(
                        "preceding"
                    )
                ),
                PostgreSQLQuery.from_(participant_cte)
                .where(participant_cte.id == participants.target_id)
                .select(
                    fn.Cast(RowToJson(participant_cte), PGSqlTypes.JSONB).as_("target")
                ),
                PostgreSQLQuery.from_(participant_cte)
                .where(participant_cte.id == participants.succeeding_id)
                .select(
                    fn.Cast(RowToJson(participant_cte), PGSqlTypes.JSONB).as_(
                        "succeeding"
                    )
                ),
            )
            .get_sql()
        )

        executable = ExecutableSQL(sql=sql, values=tuple())

        partipants_meta = cast(
            Record, await self.db.execute(executable, fetch_returns="one")
        )

        return ReorderParticipantsMeta.model_validate(dict(partipants_meta))

    async def _get_max_position_string(
        self, tablename: str, scope: str, scope_id: int
    ) -> Optional[str]:

        table = Table(tablename)

        sql = (
            PostgreSQLQuery.from_(table)
            .where(table.field(scope) == scope_id)
            .select(fn.Max(table.position_string).as_("max_position_string"))
            .get_sql()
        )

        executable = ExecutableSQL(sql=sql, values=tuple())

        record = cast(Record, await self.db.execute(executable, fetch_returns="one"))

        return cast(Optional[str], record["max_position_string"])
