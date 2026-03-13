from src.command.commands.media import MediableType
from src.database import AsyncPgDBManager
from src.query.dto.course_contents import TraineeCourseContent, TrainerCourseContent



class TraineeCourseContentQueryRepository:
    
    def __init__(self, db: AsyncPgDBManager) -> None:
        self.db = db
    
    
    async def course_contents(self, course_id: int):
        sql = """
            SELECT
                jsonb_build_object(
                    'id', c.id,
                    'title', c.title,
                    'short_description', c.short_description
                ) AS course,
                COALESCE(md.modules, '[]'::jsonb) AS module
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
        
        result = await self.db.execute(executable, fetch_returns="one")
        return TraineeCourseContent(**result) if result is not None else result
        
      
class TrainerCourseContentQueryRepository:
    
    def __init__(self, db: AsyncPgDBManager):
        self.db = db
        
    async def course_contents(self, course_id: int) -> TrainerCourseContent:
        sql = """
        SELECT
            jsonb_build_object(
                'id', c.id,
                'title', c.title,
                'short_description', c.short_description
            ) AS course,
            COALESCE(md.modules, '[]'::jsonb) AS module,
            COALESCE(a.assignments, '[]'::jsonb) AS assignment
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

        LEFT JOIN LATERAL (
            SELECT
                COALESCE(
                    jsonb_agg(
                        jsonb_build_object(
                            'id', a.id,
                            'instructions', a.instructions,
                            'media_id', me.id,
                            'filename', me.filename
                        )
                        ORDER BY a.due_date DESC
                    )
                    FILTER (WHERE a.id IS NOT NULL),
                    '[]'::jsonb
                ) AS assignments
            FROM
                assignments AS a
            LEFT JOIN
                media_assets AS me
                ON a.id = me.mediable_id
                AND me.mediable_type = $2
            WHERE
                a.course_id = c.id
                AND a.deleted_at IS NULL
        ) AS a ON true

        WHERE
            c.id = $3
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.LESSON.value, 
                MediableType.ASSIGNMENT.value,
                course_id
            )
        )
        result = await self.db.execute(executable, fetch_returns="one")

        return TrainerCourseContent(**result) if result is not None else result
    
