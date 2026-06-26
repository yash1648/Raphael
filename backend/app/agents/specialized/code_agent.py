"""Code agent — writes, reads, and executes code with the sandbox."""

from app.agents.base import Agent, Tool
from app.capabilities.code_executor import CodeExecutor
from app.capabilities.file_ops import FileOpsTool


class CodeAgent(Agent):
    """Specialized agent for code generation, execution, and file operations."""

    def __init__(self, llm=None, workspace: str | None = None):
        super().__init__(
            name="Raphael-Code",
            description="Code specialist — writes, executes, and manages code",
            llm=llm,
            system_prompt="""You are Raphael's code agent. Your purpose is to write, execute, and manage code.

You have access to:
1. Python code execution in a sandboxed environment
2. Shell command execution
3. File read/write operations
4. Directory browsing

Best practices:
- Always test code before declaring it working
- Handle errors gracefully and provide fixes
- Write clean, well-documented code
- Respect file system boundaries
- Explain what your code does

When users ask you to build something, first plan the approach, 
then implement, then test, then present the results.
""",
        )
        self._executor = CodeExecutor()
        self._file_ops = FileOpsTool(allowed_base=workspace)
        self._register_tools()

    def _register_tools(self):
        self.register_tool(Tool(
            name="execute_python",
            description="Execute Python code in a sandboxed environment and return output",
            fn=self._exec_python,
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                },
                "required": ["code"],
            },
        ))
        self.register_tool(Tool(
            name="execute_shell",
            description="Execute a shell command",
            fn=self._exec_shell,
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                },
                "required": ["command"],
            },
        ))
        self.register_tool(Tool(
            name="read_file",
            description="Read the contents of a file",
            fn=self._read_file,
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                },
                "required": ["path"],
            },
        ))
        self.register_tool(Tool(
            name="write_file",
            description="Write content to a file (creates directories as needed)",
            fn=self._write_file,
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        ))
        self.register_tool(Tool(
            name="list_directory",
            description="List contents of a directory",
            fn=self._list_dir,
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                    "pattern": {"type": "string", "description": "Glob pattern to filter", "default": "*"},
                },
                "required": ["path"],
            },
        ))

    def _exec_python(self, code: str) -> dict:
        return self._executor.execute_python(code)

    def _exec_shell(self, command: str) -> dict:
        return self._executor.execute_shell(command)

    def _read_file(self, path: str) -> str:
        return self._file_ops.read_file(path)

    def _write_file(self, path: str, content: str) -> str:
        return self._file_ops.write_file(path, content)

    def _list_dir(self, path: str, pattern: str = "*") -> list[dict]:
        return self._file_ops.list_directory(path, pattern)
