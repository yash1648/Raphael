from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.agents import agent_registry
from app.services.tool_executor import ToolExecutor

router = APIRouter(tags=["agents"])


class ExecuteRequest(BaseModel):
    project_id: int
    objective: str


class ExecuteToolRequest(BaseModel):
    project_id: int
    query: str | None = None


@router.get("/agents")
def list_agents():
    agents = agent_registry.list_agents()
    return {
        "agents": [
            {
                "name": a.name,
                "description": a.description,
                "allowed_tools": a.allowed_tools,
            }
            for a in agents
        ]
    }


@router.get("/agents/{name}")
def get_agent(name: str):
    agent = agent_registry.get(name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent": {
            "name": agent.name,
            "description": agent.description,
            "allowed_tools": agent.allowed_tools,
        }
    }


@router.post("/agents/{name}/execute")
def execute_agent(name: str, body: ExecuteRequest, db: Session = Depends(get_db)):
    agent = agent_registry.get(name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    executor = ToolExecutor(db)
    return agent.execute(project_id=body.project_id, objective=body.objective, executor=executor)


@router.post("/agents/{name}/tools/{tool_name}")
def execute_agent_tool(name: str, tool_name: str, body: ExecuteToolRequest, db: Session = Depends(get_db)):
    agent = agent_registry.get(name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    executor = ToolExecutor(db)
    kwargs = body.model_dump(exclude_none=True)
    return agent.execute_tool(tool_name, executor, **kwargs)
