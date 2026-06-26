"""Memory agent — manages vector memory storage, search, and recall."""

from app.agents.base import Agent, Tool
from app.memory.vector_memory import VectorMemory, MemoryEntry


class MemoryAgent(Agent):
    """Specialized agent for memory operations — store, search, recall, summarize."""

    def __init__(self, llm=None, persist_directory: str = "./chroma_memory"):
        super().__init__(
            name="Raphael-Memory",
            description="Memory specialist — stores, retrieves, and manages semantic memory",
            llm=llm,
            system_prompt="""You are Raphael's memory agent. You manage the persistent memory system.

You can:
1. Store new memories (conversations, facts, decisions, code)
2. Search semantically across all past memories
3. Recall recent memories
4. Categorize and organize information

Use memory to help Raphael remember:
- Past conversations and their outcomes
- Facts learned about users and projects
- Decisions made and their rationale
- Code patterns and solutions
- Things to follow up on later
""",
        )
        self._memory = VectorMemory(persist_directory=persist_directory)
        self._register_tools()

    def _register_tools(self):
        self.register_tool(Tool(
            name="store_memory",
            description="Store a memory entry",
            fn=self._store,
            parameters={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The content to remember"},
                    "memory_type": {"type": "string", "description": "Type: general, fact, decision, code, conversation", "default": "general"},
                    "source": {"type": "string", "description": "Source of this memory", "default": ""},
                },
                "required": ["content"],
            },
        ))
        self.register_tool(Tool(
            name="search_memory",
            description="Semantically search memories",
            fn=self._search,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "n_results": {"type": "integer", "description": "Number of results", "default": 5},
                },
                "required": ["query"],
            },
        ))
        self.register_tool(Tool(
            name="recall_recent",
            description="Get recent memories",
            fn=self._recall_recent,
            parameters={
                "type": "object",
                "properties": {
                    "n": {"type": "integer", "description": "Number of recent entries", "default": 10},
                },
            },
        ))
        self.register_tool(Tool(
            name="memory_count",
            description="Get total number of stored memories",
            fn=self._count,
            parameters={"type": "object", "properties": {}},
        ))

    def _store(self, content: str, memory_type: str = "general", source: str = "") -> str:
        entry = MemoryEntry(content=content, memory_type=memory_type, source=source)
        return self._memory.store(entry)

    def _search(self, query: str, n_results: int = 5) -> list[dict]:
        return self._memory.search(query, n_results=n_results)

    def _recall_recent(self, n: int = 10) -> list[dict]:
        return self._memory.recall_recent(n=n)

    def _count(self) -> int:
        return self._memory.count()
