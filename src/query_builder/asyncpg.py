import re
from httpx import get
import sqlparse
from typing import Any, Literal, Optional, Self, Sequence, Union
from pydantic import BaseModel, model_validator
from src.command.commands.base import EntityBase, any_id_adaptor, AnyID
from src.query_builder.base import BaseQueryBuilder, BaseWhere, BaseExecutableSQL


def get_placeholder_count(sql: str) -> int:
    """Returns the number of placeholder exists in a sql string."""
    pattern = r"\$\d+"
    placholders = re.findall(pattern, sql)
    return len(placholders)


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
    

    def where(self, filters: dict[str, Any]) -> "AsyncPgExecutableSQL":    
        """
        Add WHERE clause with dynamic filters to SQL.
        
        Automatically increments placeholder indices and appends values.
        Skips None values (optional filters).
        
        Args:
            filters: {column_name: value} dict
                    - Key: column name with table prefix (e.g., "asub.assignment_id")
                    - Value: filter value (None values are skipped)
        
        Returns:
            New AsyncPgExecutableSQL with WHERE clause added
        
        Example:
            >>> executable = AsyncPgExecutableSQL(sql="SELECT * FROM asub", values=())
            >>> executable = executable.where({
            ...    "asub.assignment_id": 18,
            ...    "asub.status": "graded",
            ...    "asub.from_date": None  # ← Skipped
            ...    })
            >>> print(executable)
            >>> AsyncPgExecutable(sql="SELECT * FROM asub WHERE asub.assignment_id = $1 AND asub.status = $2", values=(18, "graded"))
            >>> print(executable.sql) 
            >>> "SELECT * FROM asub WHERE asub.assignment_id = $1 AND asub.status = $2"
            >>> print(executable.values)
            >>> (18, "graded")
        """
       
        number_of_placholder = get_placeholder_count(self.sql)
        placholder_idx = number_of_placholder + 1
        
        sql = self.sql
        values = list(self.values)
        
        sql += "WHERE "
        for key, value in filters.items():
            if value is not None:
                # Add the column with a placholder.
                sql += f"{key} = ${placholder_idx} AND "
                placholder_idx += 1
                values.append(value)
        
        # Remove last AND operator.
        sql = sql.rpartition("AND")[0]
    
        return AsyncPgExecutableSQL(sql=sql, values=tuple(values))
    
    
    @staticmethod
    def get_sort_order(by: str) -> tuple[str, Literal["ASC", "DESC"]]:
        if by[0] == "-":
            return (by[1:], "DESC")
        return (by, "ASC")

    
    def order_by(self, by: Union[str, list[str]]) -> "AsyncPgExecutableSQL":
        
        sql = self.sql
        if isinstance(by, str):
            by = [by]
        
        order_spec = []
        for col in by:
            col, order = self.get_sort_order(by=col)
            order_spec.append(f"{col} {order}")
            
        sql += " ORDER BY " + ", ".join(order_spec) + " "

        return AsyncPgExecutableSQL(sql=sql, values=self.values)
            
        
    def limit(self, n: int) -> "AsyncPgExecutableSQL":
        sql = self.sql + f" LIMIT {n} "
        return AsyncPgExecutableSQL(sql=sql, values=self.values)
    
    
    def offset(self, n: int) -> "AsyncPgExecutableSQL":
        sql = self.sql + f" OFFSET {n} "
        return AsyncPgExecutableSQL(sql=sql, values=self.values)


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
    ) -> AsyncPgExecutableSQL:
        
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
    
        
    def build_exists(
        self,
        tablename: str,
        where_clause: Optional[AsyncPgWhere] = None,
        **filter_kwargs: dict[str, Any]
    ) -> AsyncPgExecutableSQL:
        
        where_clause = where_clause or self.build_where_from_dict(filter_kwargs)
        
        # Get the select statement first.
        executable = self.build_simple_select(
            tablename=tablename,
            columns=("1",),
            where_clause=where_clause
        )     
        
        # Get the executable and update the sql only.
        # Strip the trailing semicolon if it exists before wrapping
        inner_sql = executable.sql.rstrip(";")
        new_sql = f"""
            select exists ({inner_sql});
        """
        return AsyncPgExecutableSQL(sql=new_sql, values=executable.values)
        
            

        
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
    
    def build_where_from_dict(self, filters: dict[str, Any]) -> AsyncPgWhere:
            where_clause = "WHERE "
            where_clause += " AND ".join([f'{col}=(${col})' for col in filters.keys()])
            where_clause += " AND deleted_at IS NULL"
            return AsyncPgWhere(condition=where_clause, values=filters)
        
        
        
    def build_where_pk(self, value: AnyID) -> AsyncPgWhere:
        return self.build_where(value=value)
    
    
    def build_executable(self, sql, values):
        return AsyncPgExecutableSQL(sql=sql, values=values)
    
