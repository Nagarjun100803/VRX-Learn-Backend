from typing import Protocol

from pydantic import model_validator


class _PydanticModel(Protocol):
    def model_dump(self, *args, **kwargs) -> dict: ...
    def module_dump_json(self, *args, **kwargs) -> str: ...


class UpdateValidatorMixin:
    @model_validator(mode="after")
    def validate_inputs(self: _PydanticModel):
        if not self.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}):
            raise ValueError("Requires at least one field to update.")
        return self


class LookUpValidatorMixin:
    @model_validator(mode="after")
    def validate_inputs(self: _PydanticModel):
        if sum(x is not None for x in self.model_dump()) != 1:
            raise ValueError(
                f"Expecting exactly one values to look up. Received {set(self.model_dump(exclude_none=True).key())}"
            )
        return self
