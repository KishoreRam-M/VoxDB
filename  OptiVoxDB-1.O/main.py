"""
OptiVox DB - Advanced AI-Powered Database Assistant
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Core.Config import settings
from Core.lifespan import lifespan
from Core.middleware import RequestLoggingMiddleware
from Core.Logging import logger

# Import routers
from routes import system, chat, query, education, websocket, schema

# Create FastAPI application
app = FastAPI(
    title="OptiVox DB",
    description="Advanced AI-Powered Database Assistant with natural language interface",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=True
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(system.router)
app.include_router(chat.router)
app.include_router(query.router)
app.include_router(education.router)
app.include_router(websocket.router)
app.include_router(schema.router)

# Log startup
logger.info("OptiVox DB application configured")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
