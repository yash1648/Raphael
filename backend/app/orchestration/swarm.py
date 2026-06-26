"""Swarm Manager — parallel execution of multiple agents (Ultron's drone army)."""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.agents.specialized import ResearchAgent, CodeAgent, SystemAgent, MemoryAgent
from app.llm.factory import create_llm


class SwarmTask:
    """A task for the swarm to execute."""

    def __init__(self, agent_type: str, task: str, task_id: str | None = None):
        self.agent_type = agent_type
        self.task = task
        self.task_id = task_id or f"task_{int(time.time())}"
        self.result: dict | None = None
        self.error: str | None = None
        self.started_at: float = 0
        self.completed_at: float = 0

    @property
    def duration(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0


class SwarmManager:
    """Manages parallel execution of multiple agents — the Ultron swarm."""

    def __init__(self, max_parallel: int = 4, llm=None):
        self.max_parallel = max_parallel
        self._pool = ThreadPoolExecutor(max_workers=max_parallel)
        self._llm = llm

    def _create_agent(self, agent_type: str):
        """Create an agent instance by type."""
        agents = {
            "research": ResearchAgent,
            "code": CodeAgent,
            "system": SystemAgent,
            "memory": MemoryAgent,
        }
        cls = agents.get(agent_type)
        if not cls:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls(llm=self._llm)

    def execute_parallel(self, tasks: list[SwarmTask]) -> list[SwarmTask]:
        """Execute multiple tasks in parallel across available agents."""
        if not tasks:
            return tasks

        # Start all tasks
        futures = {}
        for task in tasks:
            try:
                agent = self._create_agent(task.agent_type)
                future = self._pool.submit(self._run_single, agent, task)
                futures[future] = task
            except ValueError as e:
                task.error = str(e)
                task.completed_at = time.time()

        # Collect results as they complete
        for future in as_completed(futures):
            task = futures[future]
            try:
                future.result()
            except Exception as e:
                task.error = str(e)

        return tasks

    async def execute_parallel_async(self, tasks: list[SwarmTask]) -> list[SwarmTask]:
        """Execute tasks in parallel asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._pool, self.execute_parallel, tasks)

    def _run_single(self, agent, task: SwarmTask) -> None:
        """Run a single task with an agent."""
        task.started_at = time.time()
        try:
            result = agent.run(task.task)
            task.result = {
                "response": result.get("response", ""),
                "tool_calls": result.get("tool_calls", []),
                "iterations": result.get("iterations", 0),
            }
        except Exception as e:
            task.error = str(e)
            task.result = {"response": f"Error: {e}", "tool_calls": [], "iterations": 0}
        task.completed_at = time.time()

    def execute_goal_parallel(self, goal: str, subtasks: list[dict]) -> dict:
        """Execute a goal by running subtasks in optimized parallel batches."""
        # Parse subtasks into SwarmTasks
        swarm_tasks = []
        for st in subtasks:
            agent_type = st.get("agent", "research")
            description = st.get("task", st.get("description", ""))
            swarm_tasks.append(SwarmTask(agent_type, description))

        # Group by dependency layers (topological sort simplified)
        results = self.execute_parallel(swarm_tasks)

        # Synthesize results
        summary = []
        for task in results:
            entry = {
                "task_id": task.task_id,
                "agent": task.agent_type,
                "task": task.task,
                "duration": task.duration,
                "error": task.error,
            }
            if task.result:
                entry["summary"] = task.result.get("response", "")[:500]
            summary.append(entry)

        return {
            "goal": goal,
            "total_tasks": len(results),
            "successful": sum(1 for t in results if not t.error),
            "failed": sum(1 for t in results if t.error),
            "total_duration": max(t.duration for t in results) if results else 0,
            "tasks": summary,
        }

    def shutdown(self):
        self._pool.shutdown(wait=True)
