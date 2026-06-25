from fastapi import FastAPI

from app.api import agents_router, artifacts_router, memory_router, projects_router, search_router, sessions_router, tasks_router, tools_router, workflows_router
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Raphael")
app.include_router(agents_router)
app.include_router(artifacts_router)
app.include_router(memory_router)
app.include_router(projects_router)
app.include_router(search_router)
app.include_router(sessions_router)
app.include_router(tasks_router)
app.include_router(tools_router)
app.include_router(workflows_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/opencode")
def opencode_health():
    return {"available": False, "status": "adapter_ready"}
