from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import uvicorn

from app.core.config import settings
from app.database.connection import create_db_and_tables
from app.controllers.task_controller import router
from app.controllers.migration_controller import router as migration_router
from app.models.schemas import ErrorResponse


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.debug
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(router, tags=["Tasks"])
    app.include_router(migration_router, tags=["Admin"])
    
    return app


# Create app instance
app = create_application()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors with custom response"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail="Validation error",
            errors=[
                {
                    "field": ".".join(str(loc) for loc in error["loc"]) if error.get("loc") else "unknown",
                    "message": error.get("msg", "Unknown validation error"),
                    "type": error.get("type", "unknown")
                }
                for error in exc.errors()
            ]
        ).model_dump()
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail="Pydantic validation error",
            errors=[
                {
                    "field": ".".join(str(loc) for loc in error["loc"]) if error.get("loc") else "unknown",
                    "message": error.get("msg", "Unknown validation error"),
                    "type": error.get("type", "unknown")
                }
                for error in exc.errors()
            ]
        ).model_dump()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            detail=str(exc)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    if settings.debug:
        # In debug mode, show the actual error
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=f"Internal server error: {str(exc)}"
            ).model_dump()
        )
    else:
        # In production, hide the actual error
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail="Internal server error"
            ).model_dump()
        )


@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks"""
    create_db_and_tables()
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up...")
    print(f"📝 API Documentation available at: http://{settings.host}:{settings.port}/docs")
    print(f"🔄 Alternative docs at: http://{settings.host}:{settings.port}/redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """Perform cleanup tasks on shutdown"""
    print(f"👋 {settings.app_name} shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info" if not settings.debug else "debug"
    ) 