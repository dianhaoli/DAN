"""FastAPI application entry point."""

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api import auth, sessions, users, todos, social, leaderboards, ai, gamification
from app.middleware.rate_limit import RateLimitMiddleware
from app.ml.loader import load_models

settings = get_settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting application", environment=settings.environment)
    
    # Preload ML models
    try:
        load_models()
        logger.info("ML models loaded successfully")
    except Exception as e:
        logger.error("Failed to load ML models", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title="DAN API",
    description="Digital Accountability Network - Productivity tracking backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Log response
    logger.info(
        "Request completed",
        request_id=request_id,
        status_code=response.status_code,
    )
    
    return response


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(todos.router, prefix="/api/todos", tags=["Todos"])
app.include_router(social.router, prefix="/api", tags=["Social"])
app.include_router(leaderboards.router, prefix="/api/leaderboards", tags=["Leaderboards"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(gamification.router, prefix="/api", tags=["Gamification"])


@app.get("/api/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/health/db")
async def db_health_check():
    """Database health check endpoint."""
    from app.database import SessionLocal
    from sqlalchemy import text
    from app.models.todo import Todo
    
    try:
        db = SessionLocal()
        # Test basic connection
        db.execute(text("SELECT 1"))
        
        # Check if todos table exists and is accessible
        todo_count = db.query(Todo).count()
        
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "todos_table": "exists",
            "todo_count": todo_count
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "type": type(e).__name__
            },
        )


@app.get("/api/health/redis")
async def redis_health_check():
    """Redis health check endpoint."""
    import redis
    
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "redis": "disconnected", "error": str(e)},
        )


@app.get("/api/health/ml")
async def ml_health_check():
    """ML models health check endpoint."""
    from app.ml.loader import get_models
    
    models = get_models()
    if models["distilbert"] is not None and models["xgboost"] is not None:
        return {"status": "healthy", "models": "loaded"}
    return JSONResponse(
        status_code=503,
        content={"status": "unhealthy", "models": "not loaded"},
    )
