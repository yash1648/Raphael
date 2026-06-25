from typing import TypedDict


class ToolInfo(TypedDict):
    name: str
    description: str
    category: str
    available: bool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolInfo] = {}

    def register_tool(self, tool_info: ToolInfo) -> None:
        self._tools[tool_info["name"]] = tool_info

    def list_tools(self) -> list[ToolInfo]:
        return list(self._tools.values())

    def get_tool(self, name: str) -> ToolInfo | None:
        return self._tools.get(name)

    def tool_exists(self, name: str) -> bool:
        return name in self._tools


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register_tool(ToolInfo(
        name="memory.get_project_context",
        description="Retrieve project context including tasks, sessions, and artifacts",
        category="memory",
        available=True,
    ))
    registry.register_tool(ToolInfo(
        name="memory.get_project_summary",
        description="Get aggregated summary of project tasks, goals, and activity",
        category="memory",
        available=True,
    ))
    registry.register_tool(ToolInfo(
        name="memory.get_active_work",
        description="Get current in-progress and blocked tasks with latest activity",
        category="memory",
        available=True,
    ))
    registry.register_tool(ToolInfo(
        name="search.search_project",
        description="Search across tasks, sessions, and artifacts within a project",
        category="search",
        available=True,
    ))
    registry.register_tool(ToolInfo(
        name="opencode.analyze_repository",
        description="Analyze a repository to understand its structure and purpose",
        category="opencode",
        available=False,
    ))
    registry.register_tool(ToolInfo(
        name="opencode.search_code",
        description="Search codebase for patterns and definitions",
        category="opencode",
        available=False,
    ))
    registry.register_tool(ToolInfo(
        name="opencode.review_changes",
        description="Review uncommitted or proposed code changes",
        category="opencode",
        available=False,
    ))
    registry.register_tool(ToolInfo(
        name="opencode.generate_plan",
        description="Generate a step-by-step plan for a given objective",
        category="opencode",
        available=False,
    ))

    return registry


registry = create_default_registry()
