import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import (
    agents_router, artifacts_router, memory_router,
    projects_router, search_router, sessions_router,
    tasks_router, tools_router, workflows_router,
)
from app.api.raphael import router as raphael_router
from app.core.config import settings
from app.database import Base, engine

# Export LLM keys to environment so providers can find them
for key in ["NVIDIA_API_KEY", "OPENROUTER_API_KEY"]:
    value = getattr(settings, key, "")
    if value and not os.environ.get(key):
        os.environ[key] = value

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Raphael",
    description="Super Powerful Autonomous AI Assistant API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routers
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(sessions_router)
app.include_router(artifacts_router)
app.include_router(memory_router)
app.include_router(search_router)
app.include_router(agents_router)
app.include_router(tools_router)
app.include_router(workflows_router)

# New Raphael super-assistant router
app.include_router(raphael_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0", "name": "Raphael"}


@app.get("/health/opencode")
def opencode_health():
    return {"available": False, "status": "adapter_ready"}


# Serve frontend static files in production
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend_assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the SPA for all non-API routes."""
        if full_path.startswith(("api/", "raphael/", "health", "docs", "openapi")):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return JSONResponse({"detail": "Not Found"}, status_code=404)
