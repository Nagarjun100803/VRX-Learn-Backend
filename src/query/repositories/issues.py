from typing import Optional, cast

from pypika import Case, Criterion, Parameter, PostgreSQLQuery

from src.command.commands.media import MediableType, MediaStatus
from src.database import ExecutableSQL
from src.pypika_query_builder import (
    JsonbBuildObject,
    issue_table,
    media_asset_table,
    user_table,
)
from src.query.dto.issues import IssueDetail
from src.query.repositories.base import BaseQueryRepository, map_to_dto


class IssueQueryRepository(BaseQueryRepository):
    @map_to_dto(dto=IssueDetail, dto_mode="single")
    async def issue(self, id: int) -> Optional[IssueDetail]:
        sql = (
            PostgreSQLQuery.from_(issue_table)
            .join(user_table)
            .on(issue_table.created_by == user_table.id)
            .left_join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == issue_table.id,
                        media_asset_table.mediable_type == Parameter("$2"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        issue_table.id == Parameter("$1"),
                        issue_table.deleted_at.isnull(),
                        # Either attached media asset is uploaded or not attached at all.
                        Criterion.any(
                            terms=[
                                media_asset_table.status == Parameter("$3"),
                                media_asset_table.id.isnull(),
                            ]
                        ),
                    ]
                )
            )
            .select(
                issue_table.id,
                issue_table.subject,
                issue_table.category,
                issue_table.description,
                issue_table.status,
                # Submitted by
                JsonbBuildObject(
                    "id",
                    user_table.id,
                    "username",
                    user_table.username,
                    "email",
                    user_table.email,
                    "role",
                    user_table.role,
                    "submitted_at",
                    issue_table.created_at,
                ).as_("submitted_by"),
                # Attachment
                Case()
                .when(
                    media_asset_table.id.isnotnull(),
                    JsonbBuildObject(
                        "id",
                        media_asset_table.id,
                        "filename",
                        media_asset_table.filename,
                        "mime_type",
                        media_asset_table.mime_type,
                    ),
                )
                .as_("media"),
            )
        ).get_sql()

        executable = ExecutableSQL(
            sql=sql, values=(id, MediableType.ISSUE, MediaStatus.UPLOADED)
        )

        return cast(
            Optional[IssueDetail],
            await self.db.execute(executable, fetch_returns="one"),
        )
