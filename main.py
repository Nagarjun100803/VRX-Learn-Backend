from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from src.api.routers.users import user_router
from src.api.routers.courses import router as course_router
from src.api.routers.modules import router as module_router
from src.database import async_db_manager
from src.exceptions import DomainError
from src.api.exception_registry import exception_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Lifespan event to initialize and close the database pool.
    """
    await async_db_manager.init_pool()
    yield 
    await async_db_manager.close_pool()


api_version = "/api/v1"

app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check() -> dict:
    return {
        "message": "Hello by Nagarjun",
        "status": "Okay"
    }


app.include_router(user_router, prefix=api_version)
app.include_router(course_router, prefix=api_version)
app.include_router(module_router, prefix=api_version)


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




