import re
import sqlparse
from typing import Any, Optional, Self, Sequence
from pydantic import BaseModel, model_validator
from src.commands.base import EntityBase, any_id_adaptor, AnyID
from src.query_builder.base import BaseQueryBuilder, BaseWhere, BaseExecutableSQL



class AsyncPgExecutableSQL(BaseExecutableSQL, BaseModel):
    sql: str
    values: tuple
    
    def preview(self):
        pattern = r"\$\d+"
        placeholders: list = re.findall(pattern, self.sql)
        preview_string = self.sql
        
        # Replace the placeholder with actual value for preview.
        for p, v in zip(placeholders[::-1], self.values[::-1], strict=True):
            v = f"'{v}'" if isinstance(v, str) else str(v)
            preview_string = preview_string.replace(p, v)
        
        return sqlparse.format(preview_string, reindent=True, keyword_case="upper", use_space_around_operators=True)
    



class AsyncPgWhere(BaseWhere, BaseModel):
    condition: str
    values: dict
    
    @model_validator(mode="after")
    def validate_placeholders(self) -> Self:
        pattern = r"(\$[A-Za-z_]+)" #typical example: ($email_id) or ($EMAIL_ID)
        
        # Grab all the placholders from a where clause.
        placeholders: list[str] = re.findall(pattern, self.condition)
        placeholders: set[str] = {p[1:] for p in placeholders} # Skip dollar($) sign from a string.
         
        # print(f"Placholders are {placeholders}")
        # Get all the keys from a values dict.
        placholder_keys: set[str] = set(self.values.keys())
        
        # print(f"Placholders Keys are {placholder_keys}")
        
        # Get missing placholders in values dict.
        missing_placeholders = placeholders - placholder_keys
        # print(f"Missing Placholders Keys are {missing_placholders}")
        if missing_placeholders:
            raise ValueError(
                    f"Missing required placeholder values. "
                    f"The following placeholders were not provided: {missing_placeholders}."
                )

        return self
    
    

class AsyncPgQueryBuilder(BaseQueryBuilder):
    
    
    @staticmethod
    def process_data(data: dict[str, Any]) -> dict[str, Any]:
        # change EntityBase to int. 
        func = lambda v: v.remove_prefix().id if isinstance(v, EntityBase) else v    
        processed_data = {k: func(v) for k, v in data.items()}
        # print(f'The processed data is {processed_data}')
        return processed_data
            
    
    def build_insert(
        self, 
        tablename: str, 
        data: dict[str, Any], 
        return_columns: Sequence[str] = ("*",)
    ) -> AsyncPgExecutableSQL:
        
        sql = f"INSERT INTO {tablename}("
        columns_and_values = AsyncPgQueryBuilder.process_data(data)
        sql += ", ".join(list(columns_and_values.keys()))        
        sql += ")VALUES("
        
        sql += ", ".join([f"${i}" for i in range(1, len(columns_and_values) + 1)])
        sql += ") "
        
        if return_columns:
            sql += "RETURNING "
            sql += ", ".join([col for col in return_columns])
        sql += ";"
        
        return AsyncPgExecutableSQL(sql=sql, values=tuple(columns_and_values.values()))
        
        
    def build_update(
        self, 
        tablename: str, 
        data: dict[str, Any], 
        where_clause: Optional[AsyncPgWhere] = None, 
        return_columns: Sequence[str] = ("*",)
    ) -> AsyncPgExecutableSQL:
        
        sql = f"UPDATE {tablename} SET "
        columns_and_values = AsyncPgQueryBuilder.process_data(data)
        idx = 1
        values = list(columns_and_values.values()) # Values to pass AsyncPgExecutableSQL.
        
        for col in columns_and_values.keys():
            sql += f"{col} = ${idx}, "
            idx += 1
        
        # Remove last comma.
        sql = sql.rpartition(",")[0] + " "
        
        if where_clause:
            sql += where_clause.condition
            placeholders: list[str] = re.findall(r"(\$[A-Za-z_]+)", where_clause.condition)
            for placholder in placeholders:
                sql = sql.replace(f"({placholder})", f"${idx} ")
                idx += 1

            # Handling the placholder order in values dict.
            # Take placholder and perform dictionary access 
            # to get proper order of values. 
            where_clause_values = [
                where_clause.values[p[1:]]  
                for p in placeholders
            ]
            
            values.extend(where_clause_values)
            
        if return_columns:
            sql += " RETURNING "
            sql += ", ".join(return_columns)
            
        sql += ";"
        
        return AsyncPgExecutableSQL(sql=sql, values=values)
    
    
    def build_simple_select(
        self,
        tablename: str,
        columns: Sequence[str] = ("*", ),
        where_clause: Optional[AsyncPgWhere] = None
    ):
        
        sql = "SELECT "
        requested_columns = columns if columns else ["*"]
        sql += ", ".join(col for col in requested_columns)
        sql += f" FROM {tablename} "
        
        # Where clause logic.
        idx = 1
        values = []
        if where_clause:
            sql += where_clause.condition
            placeholders: list[str] = re.findall(r"(\$[A-Za-z_]+)", where_clause.condition)
            for placholder in placeholders:
                sql = sql.replace(f"({placholder})", f"${idx} ")
                idx += 1
            
                where_clause_values = [
                    where_clause.values[p[1:]]  
                    for p in placeholders
                ]

            values.extend(where_clause_values)
                
                
        sql += ";"
        
        return AsyncPgExecutableSQL(sql=sql, values=tuple(values))
            
            
    # def build_where_id(
    #     self,
    #     entity_id: AnyID
    # ) -> AsyncPgWhere:
        
    #     entity_id = any_id_adaptor.validate_python(entity_id) # Return the numeric part.
    #     return AsyncPgWhere(
    #         condition="where id = ($id) and deleted_at is null",
    #         values={"id": entity_id}
    #     )
        
    def build_base_where(
        self,
        condition: str,
        values: dict
    ) -> AsyncPgWhere:
        
        return AsyncPgWhere(
            condition=condition,
            values=values
        )
    
    def build_where(
        self,
        value: AnyID,
        column: str = "id"
    ) -> AsyncPgWhere:
        
        if column == "id":
            value: int = any_id_adaptor.validate_python(value) # Return the numeric part.
        
        return AsyncPgWhere(
            condition=f"where {column} = ($value) and deleted_at is null",
            values={"value": value}
        )
        
        
    def build_where_pk(self, value: AnyID) -> AsyncPgWhere:
        return self.build_where(value=value)
    
    
    def build_executable(self, sql, values):
        return AsyncPgExecutableSQL(sql=sql, values=values)