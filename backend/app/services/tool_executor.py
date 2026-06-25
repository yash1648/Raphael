from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.services.memory import MemoryService
from app.services.search import SearchService
from app.services.tool_registry import registry as tool_registry

TOOL_ROUTING = {
    "memory.get_project_context": (MemoryService, "get_project_context"),
    "memory.get_project_summary": (MemoryService, "get_project_summary"),
    "memory.get_active_work": (MemoryService, "get_active_work"),
    "search.search_project": (SearchService, "search"),
}


class ToolExecutor:
    def __init__(self, db: Session):
        self.db = db

    def validate_tool(self, tool_name: str) -> bool:
        return tool_registry.tool_exists(tool_name)

    def list_available_tools(self) -> list[str]:
        return list(TOOL_ROUTING.keys())

    def execute(self, tool_name: str, **kwargs) -> dict:
        if not self.validate_tool(tool_name):
            return {
                "tool": tool_name,
                "success": False,
                "error": f"Tool '{tool_name}' not found in registry",
            }

        if tool_name not in TOOL_ROUTING:
            return {
                "tool": tool_name,
                "success": False,
                "error": f"Tool '{tool_name}' is registered but has no executor implementation",
            }

        service_cls, method_name = TOOL_ROUTING[tool_name]
        service = service_cls(self.db)
        method = getattr(service, method_name)

        try:
            result = method(**kwargs)
            return {
                "tool": tool_name,
                "success": True,
                "result": jsonable_encoder(result),
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "success": False,
                "error": str(e),
            }
