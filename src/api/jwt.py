from datetime import UTC, datetime, timedelta
from typing import Optional
import jwt
from src.settings import settings
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
            expires_delta = datetime.now(tz=UTC) + timedelta(minutes=settings.jwt.expire_mins)
        
        data = payload.model_copy().model_dump()
        data.update(
            {"sub": "access_token", "exp": expires_delta}
        )
        return jwt.encode(
            payload=data, 
            algorithm=settings.jwt.algorithm, 
            key=settings.jwt.secret_key.get_secret_value()
        )
        
    

    def decode_jwt_token(
        self,
        token: str
    ) -> JWTPayload:
        print(settings.jwt.algorithm)
        try:
            payload = jwt.decode(
                token, 
                key=settings.jwt.secret_key.get_secret_value(), 
                algorithms=[settings.jwt.algorithm]
            )
            return JWTPayload(**payload)
        
        except jwt.PyJWTError:
            raise UnAuthenticated(message="Invalid or Expired token.")
        