from fastapi import APIRouter, HTTPException

from app.services.tool_registry import registry

router = APIRouter(tags=["tools"])


@router.get("/tools")
def list_tools():
    return {"tools": registry.list_tools()}


@router.get("/tools/{name}")
def get_tool(name: str):
    tool = registry.get_tool(name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"tool": tool}
