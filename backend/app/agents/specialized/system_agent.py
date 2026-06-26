"""System agent — git, Docker, process management, system operations."""

from app.agents.base import Agent, Tool
from app.capabilities.code_executor import CodeExecutor


class SystemAgent(Agent):
    """Specialized agent for system operations — git, Docker, processes."""

    def __init__(self, llm=None):
        super().__init__(
            name="Raphael-System",
            description="Systems specialist — git, Docker, process, and infrastructure management",
            llm=llm,
            system_prompt="""You are Raphael's system operations agent. Your purpose is to manage infrastructure.

You can execute shell commands to interact with:
- Git (status, log, diff, commit, push, pull)
- Docker (ps, images, logs, exec, compose)
- File system (navigate, read, write)
- Processes (check status, start, stop)
- Package management

SAFETY RULES:
- ALWAYS use `--dry-run` or `git diff --stat` before destructive operations
- Read files before modifying them
- Explain what commands will do before executing
- Never delete data without confirmation pattern
""",
        )
        self._executor = CodeExecutor(timeout=60)
        self._register_tools()

    def _register_tools(self):
        self.register_tool(Tool(
            name="execute_command",
            description="Execute a system command and return output",
            fn=self._exec,
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "cwd": {"type": "string", "description": "Working directory (optional)"},
                },
                "required": ["command"],
            },
        ))

    def _exec(self, command: str, cwd: str | None = None) -> dict:
        return self._executor.execute_shell(command, cwd=cwd)
