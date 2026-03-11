from datetime import UTC, datetime, timedelta
from typing import Optional
import jwt
from src.command.commands.users import UserRole
from pydantic import BaseModel
from src.exceptions import UnAuthenticated


class JWTPayloadCreate(BaseModel):
    user_id: int
    role: UserRole


class JWTPayload(JWTPayloadCreate):
    sub: str = "access_token"
    exp: int


class JWTHandler:
    
    def create_jwt_token(
        self, 
        payload: JWTPayload, 
        expires_delta: Optional[timedelta] =  None
    ) -> str:
        
        if expires_delta is None:
            expires_delta = datetime.now(tz=UTC) + timedelta(minutes=15)
        
        data = payload.model_copy().model_dump()
        data.update(
            {"sub": "access_token", "exp": expires_delta}
        )
        return jwt.encode(payload=data, algorithm="HS256", key="secret")
        
    

    def decode_jwt_token(
        self,
        token: str
    ) -> JWTPayload:    
        try:
            payload = jwt.decode(token, key="secret", algorithms=["HS256"])
            return JWTPayload(**payload)
        except jwt.PyJWKError:
            raise UnAuthenticated(message="Invalid or Expired token.")
        