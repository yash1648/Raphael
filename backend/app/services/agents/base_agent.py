class BaseAgent:
    name: str = ""
    description: str = ""
    allowed_tools: list[str] = []

    def execute(self, project_id: int, objective: str, executor=None) -> dict:
        return {
            "agent": self.name,
            "objective": objective,
            "status": "not_implemented",
        }

    def execute_tool(self, tool_name: str, executor, **kwargs) -> dict:
        if tool_name not in self.allowed_tools:
            return {
                "tool": tool_name,
                "success": False,
                "error": f"Agent '{self.name}' does not have permission to use tool '{tool_name}'",
            }
        return executor.execute(tool_name, **kwargs)
