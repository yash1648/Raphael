"""Research agent — web search, content extraction, information synthesis."""

from app.agents.base import Agent, Tool
from app.capabilities.web_search import WebSearchTool


class ResearchAgent(Agent):
    """Specialized agent for web research and information gathering."""

    def __init__(self, llm=None):
        super().__init__(
            name="Raphael-Research",
            description="Web research specialist — searches, fetches, and synthesizes information",
            llm=llm,
            system_prompt="""You are Raphael's research agent. Your purpose is to gather, analyze, and synthesize information from the web.

You have access to web search and page fetching tools. Use them to:
1. Search for relevant information
2. Fetch and read pages for detailed content
3. Cross-reference multiple sources
4. Synthesize findings into clear, accurate summaries

Always cite your sources. If you cannot find reliable information, say so.
Be thorough but focused on the user's actual question.
""",
        )
        self._web = WebSearchTool()
        self._register_tools()

    def _register_tools(self):
        self.register_tool(Tool(
            name="search_web",
            description="Search the web for information on a query",
            fn=self._search,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "num_results": {"type": "integer", "description": "Number of results (1-10)", "default": 5},
                },
                "required": ["query"],
            },
        ))
        self.register_tool(Tool(
            name="fetch_page",
            description="Fetch and extract readable content from a URL",
            fn=self._fetch,
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch"},
                },
                "required": ["url"],
            },
        ))

    def _search(self, query: str, num_results: int = 5) -> list[dict]:
        return self._web.search_web(query, num_results)

    def _fetch(self, url: str) -> dict:
        return self._web.fetch_page(url)

    def close(self):
        self._web.close()
