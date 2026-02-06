from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.mongodb import lifespan_client
from .routers.auth import router as auth_router
from .routers.resume import router as resume_router
from .routers.user import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with lifespan_client():
        yield


app = FastAPI(
    title="Resume Tailor AI API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "health", "description": "Service health checks."},
        {"name": "users", "description": "User creation and management."},
        {"name": "resume", "description": "Resume extraction, tailoring, and export."},
    ],
)

# CORS: allow the Vite dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"], summary="Health check")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(resume_router)
