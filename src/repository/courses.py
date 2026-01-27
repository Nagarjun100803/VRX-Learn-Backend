import asyncio
from asyncpg.protocol.record import Record
from typing import Any, ClassVar, Literal, Optional, Type, Union, override
from src.query_builder.base import BaseExecutableSQL
from src.repository.base import BaseRepository
from src.commands.courses import(
    Course, CourseCreate, CourseDelete, CourseGet,
    CourseInfoUpdate, RecordedCourseDetailsUpdate,
    CourseType   
)
from src.repository.ownership_specification import BaseOwnershipSpec, CourseOwnershipSpec



class CourseRepository(BaseRepository[Course]):
         
    tablename: ClassVar[str] = "courses"
    _ownership_spec: ClassVar[Type[BaseOwnershipSpec]] = CourseOwnershipSpec
    
    @override
    def _to_domain(self, row: Optional[Record]) -> Course:
        
        if not row:
            return None
        course = dict(row)
        detail_columns = ["type", "price", "total_hours"] if course["type"] == CourseType.PRE_RECORDED.value else ["type"]
        details = {key: course[key] for key in detail_columns}    

        return Course(details=details, **course)
    
    
    @override
    async def add(self, cmd: CourseCreate) -> Course:
        
        data = cmd.model_dump(exclude_none=True, exclude={"details", "trainer_id"})
        data.update(cmd.details.model_dump())
        data.update({"slug": cmd.get_slug(), "trainer_id": cmd.trainer_id})
        executable = self.db.query_builder.build_insert(self.tablename, data)
        
        course: Record = await self.db.execute(executable, fetch_returns="one")
        
        return self._to_domain(course)
    
           
    async def update(
        self, cmd: Union[
            CourseInfoUpdate, 
            RecordedCourseDetailsUpdate
        ]
    ) -> Optional[Course]:
        
        return await super().update(cmd)
        
            
  
    @override
    async def delete(self, cmd: CourseDelete) -> Optional[Course]:
        data = cmd.model_dump(exclude={"id"})
        data = self._add_audit_field(data, "delete")
        print(data)
    
        executables: list[BaseExecutableSQL] = [
        
            # self.db.query_builder.build_update(
            #     "resources", data,
            #     where_clause=self.db.query_builder.build_base_where(
            #         condition="where module_id in (select id from modules where course_id = ($course_id) and deleted_at is null)",
            #         values={"course_id": id},
            #     ),
            #     return_columns=None
            # ),
            
            self.db.query_builder.build_update(
                "modules", data,
                where_clause = self.db.query_builder.build_where(
                    column="course_id", value=cmd.id
                )
            ),
            # We can use build_where, but for uniformity we go with this approach.
            self.db.query_builder.build_update(
                self.tablename, data,
                where_clause=self.db.query_builder.build_where_pk(cmd.id)
            )
        ]
        
        for executable in executables:
            print(executable.preview())
            print("=="* 10)
            print("\n")
        
        # # Handover to transaction.
        course: Optional[Record] = await self.db.with_transaction(executables)

        return self._to_domain(course)
    

    async def get(self, query: CourseGet):
        return await super().get(query)
    


    
    
    
        




