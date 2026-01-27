from pydantic import model_validator, ConfigDict
from typing import Self




class UpdateValidatorMixin:
    
    @model_validator(mode="after")
    def validate_inputs(self) -> Self:
        if not self.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}):
            raise ValueError("Requires atleast one field to update. ")
        return self
    
    
class LookUpValidatorMixin:
    
    @model_validator(mode="after")
    def validate_inputs(self) -> Self:
        if sum(x is not None for x in self.model_dump()) != 1:
            raise ValueError(f"Expecting exactly one values to look up. Received {set(self.model_dump(exclude_none=True).key())}")
        return self
            