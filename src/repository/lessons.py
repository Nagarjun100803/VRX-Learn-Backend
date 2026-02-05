from dataclasses import dataclass
from typing import ClassVar, Optional, Type
from src.repository.base import BaseRepository
from src.commands.lessons import Lesson, LessonCreateWithPosition, LessonDelete, LessonGet, LessonTitleUpdate, LessonReArrange
from src.repository.ownership_specification import BaseOwnershipSpec, LessonOwnershipSpec
from src.commands.media import MediableType


@dataclass(kw_only=True)
class LessonRepository(BaseRepository[Lesson]):   
     
    tablename: ClassVar[str] = "lessons"
    _ownership_spec: ClassVar[Type[BaseOwnershipSpec]] = LessonOwnershipSpec
    
    def _to_domain(self, row) -> Optional[Lesson]:
        if row is None:
            return None
        return Lesson(**row)
    
    async def add(self, cmd: LessonCreateWithPosition):
        return await super().add(cmd)
    
    
    async def update(self, cmd: LessonTitleUpdate) -> Optional[Lesson]:
        return await super().update(cmd)
    
    
    async def delete(self, cmd: LessonDelete) -> Optional[Lesson]:
        # Delete the media record and actual lesson.
        data = cmd.model_dump(exclude={"id"})
        data = self._add_audit_field(data, "delete")
        executables = [
            self.db.query_builder.build_update(
                "media_assets", data, 
                where_clause=self.db.query_builder.build_base_where(
                    condition="Where mediable_id = ($mediable_id) and mediable_type = ($mediable_type)",
                    values={
                        "mediable_id": cmd.id, 
                        "mediable_type": MediableType.LESSON
                    }
                )     
            ),
            self.db.query_builder.build_update(
                self.tablename, data,
                where_clause=self.db.query_builder.build_where_pk(value=cmd.id)
            )
        ]
        
        lesson = await self.db.with_transaction(executables, return_last=True)
        return self._to_domain(lesson)
    

    async def get(self, query: LessonGet) -> Optional[Lesson]:
        return await super().get(query)
    
