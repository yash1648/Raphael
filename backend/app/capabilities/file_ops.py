"""File system operations tool — safe read/write/list with path validation."""

import os
from pathlib import Path


class FileOpsTool:
    """Safe file system operations with restricted scope."""

    def __init__(self, allowed_base: str | None = None):
        self.allowed_base = Path(allowed_base).resolve() if allowed_base else None

    def _resolve_path(self, path: str) -> Path:
        p = Path(path).resolve()
        if self.allowed_base:
            try:
                p.relative_to(self.allowed_base)
            except ValueError:
                raise PermissionError(f"Access denied: {path} is outside allowed base {self.allowed_base}")
        return p

    def read_file(self, path: str) -> str:
        """Read file contents."""
        p = self._resolve_path(path)
        if not p.exists():
            return f"Error: File not found: {path}"
        if not p.is_file():
            return f"Error: Not a file: {path}"
        try:
            return p.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, path: str, content: str) -> str:
        """Write content to file (creates parent dirs)."""
        p = self._resolve_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            p.write_text(content, encoding="utf-8")
            return f"Written {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def list_directory(self, path: str, pattern: str = "*") -> list[dict]:
        """List directory contents."""
        p = self._resolve_path(path)
        if not p.exists():
            return [{"error": f"Directory not found: {path}"}]
        if not p.is_dir():
            return [{"error": f"Not a directory: {path}"}]

        items = []
        for entry in sorted(p.glob(pattern)):
            items.append({
                "name": entry.name,
                "path": str(entry),
                "type": "directory" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else 0,
                "modified": entry.stat().st_mtime,
            })
        return items

    def file_info(self, path: str) -> dict:
        """Get file metadata."""
        p = self._resolve_path(path)
        if not p.exists():
            return {"error": f"Not found: {path}"}
        stat = p.stat()
        return {
            "name": p.name,
            "path": str(p),
            "type": "directory" if p.is_dir() else "file",
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
        }
