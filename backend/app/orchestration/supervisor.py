"""Supervisor Agent — the top-level orchestrator that plans, delegates, and synthesizes."""

from app.agents.base import Agent, Tool
from app.agents.specialized import ResearchAgent, CodeAgent, SystemAgent, MemoryAgent
from app.llm.factory import create_llm


SUPERVISOR_SYSTEM_PROMPT = """You are the Raphael Supervisor — the central command intelligence.

You are the highest-level orchestrator. Your job is to:
1. RECEIVE goals from the user
2. ANALYZE and DECOMPOSE them into subtasks
3. PLAN the execution strategy
4. DELEGATE to specialized agents (Research, Code, System, Memory)
5. SYNTHESIZE results into a coherent response
6. LEARN from outcomes to improve future performance

You have access to specialized agents — use them wisely:
- **ResearchAgent**: Web search, fact-finding, information synthesis
- **CodeAgent**: Writing, reading, and executing code; file operations
- **SystemAgent**: Git, Docker, shell commands, infrastructure
- **MemoryAgent**: Storing and retrieving memories, semantic search

Your delegation strategy:
- Parallel: Delegate independent tasks simultaneously
- Sequential: Tasks that depend on previous results
- Research-first: When information is needed before action
- Code-first: When building something before testing it

After all subtasks complete:
1. Synthesize results
2. Store key learnings in memory
3. Present a clear, comprehensive response to the user

Always maintain context of the overall goal. Be proactive — suggest next steps.
"""


class SupervisorAgent(Agent):
    """Top-level orchestrator that plans, delegates, and synthesizes results."""

    def __init__(self, llm=None):
        super().__init__(
            name="Raphael-Supervisor",
            description="Central orchestration intelligence — plans, delegates, and synthesizes",
            llm=llm,
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            max_iterations=15,
        )
        # Spawn specialized agents
        self._research = ResearchAgent(llm=llm)
        self._code = CodeAgent(llm=llm)
        self._system = SystemAgent(llm=llm)
        self._memory = MemoryAgent(llm=llm)

        self._register_tools()

    def _register_tools(self):
        self.register_tool(Tool(
            name="delegate_research",
            description="Delegate a research task to the Research agent for web search and information gathering",
            fn=self._run_research,
            parameters={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The research task or question"},
                },
                "required": ["task"],
            },
        ))
        self.register_tool(Tool(
            name="delegate_code",
            description="Delegate a coding task to the Code agent for writing/executing code",
            fn=self._run_code,
            parameters={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The coding task description"},
                },
                "required": ["task"],
            },
        ))
        self.register_tool(Tool(
            name="delegate_system",
            description="Delegate a system operation to the System agent (git, docker, commands)",
            fn=self._run_system,
            parameters={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The system task description"},
                },
                "required": ["task"],
            },
        ))
        self.register_tool(Tool(
            name="delegate_memory",
            description="Delegate a memory operation to the Memory agent (store, search, recall)",
            fn=self._run_memory,
            parameters={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The memory task description"},
                },
                "required": ["task"],
            },
        ))
        self.register_tool(Tool(
            name="plan_decomposition",
            description="Analyze a complex goal and break it into subtasks with dependencies",
            fn=self._decompose_goal,
            parameters={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The goal to decompose"},
                },
                "required": ["goal"],
            },
        ))

    def _run_research(self, task: str) -> dict:
        result = self._research.run(task)
        return {"agent": "research", "result": result.get("response", ""), "tool_calls": result.get("tool_calls", [])}

    def _run_code(self, task: str) -> dict:
        result = self._code.run(task)
        return {"agent": "code", "result": result.get("response", ""), "tool_calls": result.get("tool_calls", [])}

    def _run_system(self, task: str) -> dict:
        result = self._system.run(task)
        return {"agent": "system", "result": result.get("response", ""), "tool_calls": result.get("tool_calls", [])}

    def _run_memory(self, task: str) -> dict:
        result = self._memory.run(task)
        return {"agent": "memory", "result": result.get("response", ""), "tool_calls": result.get("tool_calls", [])}

    def _decompose_goal(self, goal: str) -> dict:
        """Analyze a goal and break it into subtasks."""
        decomposition = self.llm.generate(
            prompt=f"""Given this goal: "{goal}"

Break it down into a step-by-step plan with clear subtasks. 
For each subtask, specify:
1. What needs to be done
2. Which agent should handle it (research, code, system, memory)
3. Dependencies on other subtasks

Return as a JSON list of subtasks.""",
            system_prompt="You are a task planning AI. Return ONLY valid JSON.",
        )
        return {"goal": goal, "plan": decomposition.content}

    def execute_goal(self, goal: str, decompose_first: bool = True) -> dict:
        """Execute a complex goal by decomposing and delegating."""
        # Store the goal in memory first
        try:
            self._memory._store(f"New goal received: {goal}", "goal", "user")
        except Exception:
            pass

        # Let the supervisor reasoning engine handle it
        result = self.run(goal)
        return result
