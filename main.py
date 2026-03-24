from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.exception_registry import exception_registry
from src.api.routers import ROUTERS
from src.dependencies import db
from src.exceptions import DomainError
from src.settings import settings



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Lifespan event to initialize and close the database pool.
    """
    await db.init_pool()
    yield 
    await db.close_pool()


api_version = "/api/v1"

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.cors.allowed_origins,
    allow_credentials = True,
    allow_headers = ["*"],
    allow_methods = ["*"]
)

@app.get("/health")
async def health_check() -> dict:
    return {
        "message": "Hello by Nagarjun",
        "status": "Okay"
    }


# Register api routers.
for router in ROUTERS:
    app.include_router(router, prefix=api_version)



@app.exception_handler(DomainError)
async def custom_exception_handler(
    request: Request,
    exc: DomainError
) -> JSONResponse:
    
    status_code = 500 # Default.
    for domain_exc_class, code in exception_registry.items():
        if isinstance(exc, domain_exc_class):
            status_code = code 
            break
        
    return JSONResponse(
        status_code=status_code,
        content={
            "message": exc.message,
            "type": exc.__class__.__name__,
            "status": "error"
        }
    )




