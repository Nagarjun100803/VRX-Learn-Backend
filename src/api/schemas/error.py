from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    message: str
    type: str
    status: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Invalid credentials provided.",
                "type": "UnAuthenticated",
                "status": "error",
            }
        }
    )
