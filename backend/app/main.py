"""
OpsMate AI - FastAPI Main Application

Entry point for the backend service.
Configures CORS, loads local environment variables, and registers API routers.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from backend/.env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.api.routes import router as api_router

app = FastAPI(
    title="OpsMate AI - ITSM Assistant API",
    description="Backend API for incident analysis, deterministic SLA risk assessment, and LangGraph-powered IT operations assistant.",
    version="1.0.0",
)

# Configure CORS: allow local development and production Vercel frontend
default_origins = "http://localhost:5173,http://127.0.0.1:5173,https://opsmate-ai.vercel.app"
cors_env = os.getenv("CORS_ORIGINS", default_origins)
allowed_origins = [origin.strip().rstrip("/") for origin in cors_env.split(",") if origin.strip()]

# Ensure production Vercel origin is always permitted
if "https://opsmate-ai.vercel.app" not in allowed_origins:
    allowed_origins.append("https://opsmate-ai.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/")
def root():
    """Root endpoint with quick navigation links."""
    return {
        "message": "Welcome to OpsMate AI API",
        "documentation": "/docs",
        "health": "/api/health",
        "incidents": "/api/incidents",
        "summary": "/api/incidents/summary",
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
