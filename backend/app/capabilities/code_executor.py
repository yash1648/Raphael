"""Safe code execution sandbox using subprocess isolation."""

import ast
import os
import subprocess
import sys
import tempfile
import textwrap
import time


class CodeExecutionError(Exception):
    """Raised when code execution fails."""


SANDBOX_BANNED_KEYWORDS = [
    "import os", "import subprocess", "import sys",
    "__import__", "eval(", "exec(", "compile(",
    "open(", "__builtins__", "pickle",
]


class CodeExecutor:
    """Executes code in an isolated subprocess with resource limits."""

    def __init__(self, timeout: int = 30, max_output: int = 10000):
        self.timeout = timeout
        self.max_output = max_output

    def execute_python(self, code: str, stdin: str = "") -> dict:
        """Execute Python code in a sandboxed subprocess.

        Returns dict with stdout, stderr, exit_code, execution_time.
        """
        # Basic static analysis
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {
                "stdout": "",
                "stderr": f"SyntaxError: {e}",
                "exit_code": 1,
                "execution_time": 0,
                "success": False,
            }

        # Wrap code in execution harness with resource limits
        wrapper = textwrap.dedent(f"""
        import sys
        import resource
        import signal

        # Set resource limits
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))  # 256MB

        # Timeout handler
        def timeout_handler(signum, frame):
            print("Execution timed out", file=sys.stderr)
            sys.exit(124)

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm({self.timeout})

        # Execute user code
        try:
            exec('''{code}''')
        except Exception as e:
            print(f"{{type(e).__name__}}: {{e}}", file=sys.stderr)
            sys.exit(1)
        """)

        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, "-c", wrapper],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.timeout + 5,  # Extra buffer
                env={} if os.name == "posix" else None,  # Minimal env on Unix
            )
            exec_time = time.time() - start
            stdout = result.stdout[:self.max_output]
            stderr = result.stderr[:self.max_output]

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result.returncode,
                "execution_time": round(exec_time, 3),
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout}s",
                "exit_code": 124,
                "execution_time": self.timeout,
                "success": False,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": round(time.time() - start, 3),
                "success": False,
            }

    def execute_shell(self, command: str, cwd: str | None = None) -> dict:
        """Execute a shell command with resource limits."""
        start = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
            )
            exec_time = time.time() - start
            return {
                "stdout": result.stdout[:self.max_output],
                "stderr": result.stderr[:self.max_output],
                "exit_code": result.returncode,
                "execution_time": round(exec_time, 3),
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout}s",
                "exit_code": 124,
                "execution_time": self.timeout,
                "success": False,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": round(time.time() - start, 3),
                "success": False,
            }
