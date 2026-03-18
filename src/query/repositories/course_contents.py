from src.command.commands.media import MediableType
from src.query.dto.course_contents import TraineeCourseContent, TrainerCourseContent
from src.query.repositories.base import BaseQueryRepository, map_to_dto



class TraineeCourseContentQueryRepository(BaseQueryRepository):

    @map_to_dto(dto=TraineeCourseContent, dto_mode="single")    
    async def course_contents(self, course_id: int) -> TraineeCourseContent:
        sql = """
            SELECT
                jsonb_build_object(
                    'id', c.id,
                    'title', c.title,
                    'short_description', c.short_description
                ) AS course,
                COALESCE(md.modules, '[]'::jsonb) AS modules
            FROM
                courses AS c

            LEFT JOIN LATERAL (
                SELECT
                    COALESCE(
                        jsonb_agg(module_detail ORDER BY module_position)
                        FILTER (WHERE module_detail IS NOT NULL),
                        '[]'::jsonb
                    ) AS modules
                FROM (
                    SELECT
                        jsonb_build_object(
                            'id', m.id,
                            'title', m.title,
                            'description', m.description,
                            'lessons', COALESCE(
                                jsonb_agg(ld.lesson_detail ORDER BY ld.lesson_position)
                                FILTER (WHERE ld.lesson_detail IS NOT NULL),
                                '[]'::jsonb
                            )
                        ) AS module_detail,
                        m.position_string AS module_position
                    FROM
                        modules AS m
                    LEFT JOIN LATERAL (
                        SELECT
                            jsonb_build_object(
                                'id', l.id,
                                'title', l.title,
                                'module_id', l.module_id,
                                'media_id', me.id,
                                'filename', me.filename
                            ) AS lesson_detail,
                            l.position_string AS lesson_position
                        FROM
                            lessons AS l
                        JOIN
                            media_assets AS me
                            ON l.id = me.mediable_id
                            AND me.mediable_type = $1
                        WHERE
                            l.module_id = m.id
                    ) AS ld ON true
                    WHERE
                        m.course_id = c.id
                    GROUP BY
                        m.id, m.title, m.description, m.position_string
                ) AS sub
            ) AS md ON true

            WHERE
                c.id = $2
        """
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(MediableType.LESSON.value, course_id)
        )
        
        return await self.db.execute(executable, fetch_returns="one")

        
      
class TrainerCourseContentQueryRepository(BaseQueryRepository):

    @map_to_dto(dto=TrainerCourseContent, dto_mode="single")    
    async def course_contents(self, course_id: int) -> TrainerCourseContent:
        sql = """
            SELECT
                JSONB_BUILD_OBJECT(
                    'id', c.id,
                    'title', c.title,
                    'short_description', c.short_description
                ) AS course,
                COALESCE(md.modules, '[]'::jsonb) AS modules,
                COALESCE(ad.assignments, '[]'::jsonb) AS assignments
            FROM
                courses AS c
            LEFT JOIN LATERAL(
                SELECT
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'id', m.id,
                            'title', m.title,
                            'description', m.description
                        ) ORDER BY m.position_string
                    ) FILTER (WHERE m.id is not null) AS modules
                FROM 
                    modules as m
                WHERE
                    c.id = m.course_id and
                    m.deleted_at is null
            ) AS md ON true
            LEFT JOIN LATERAL(
                SELECT
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'id', a.id,
                            'title', a.title
                        ) ORDER BY a.due_date
                    ) FILTER (WHERE a.id is not null) AS assignments
                from
                    assignments AS a
                WHERE
                    a.course_id = c.id and
                    a.deleted_at is null
            ) AS ad ON true
            WHERE
                c.id = $1
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(course_id, )
        )
        return await self.db.execute(executable, fetch_returns="one")
