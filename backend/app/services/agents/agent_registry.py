from fastapi import HTTPException

from app.services.agents.base_agent import BaseAgent
from app.services.decision_engine import DecisionEngine
from app.services.opencode_adapter import OpenCodeAdapter


class PlannerAgent(BaseAgent):
    name: str = "planner"
    description: str = "Analyzes project context and generates structured plans"
    allowed_tools: list[str] = [
        "memory.get_project_context",
        "memory.get_project_summary",
        "memory.get_active_work",
    ]

    def execute(self, project_id: int, objective: str, executor=None) -> dict:
        summary_result = executor.execute("memory.get_project_summary", project_id=project_id)
        active_result = executor.execute("memory.get_active_work", project_id=project_id)

        task_counts = summary_result["result"]["task_counts"]
        blocked_tasks = active_result["result"]["blocked_tasks"]
        in_progress_tasks = active_result["result"]["in_progress_tasks"]

        recommendations = []

        if task_counts["blocked"] > 0:
            blocked_names = [t["title"] for t in blocked_tasks]
            recommendations.append(
                f"Resolve {task_counts['blocked']} blocked task(s) first: {', '.join(blocked_names)}"
            )
        elif task_counts["in_progress"] > 0:
            in_progress_names = [t["title"] for t in in_progress_tasks]
            recommendations.append(
                f"Finish {task_counts['in_progress']} in-progress task(s): {', '.join(in_progress_names)}"
            )
        elif task_counts["todo"] > 0:
            recommendations.append(
                f"Start highest-priority todo task among {task_counts['todo']} pending"
            )
        else:
            recommendations.append("Project appears complete — no outstanding tasks")

        return {
            "agent": self.name,
            "objective": objective,
            "project_status": {
                "completed": task_counts["completed"],
                "in_progress": task_counts["in_progress"],
                "blocked": task_counts["blocked"],
                "todo": task_counts["todo"],
            },
            "recommendations": recommendations,
        }


class ResearchAgent(BaseAgent):
    name: str = "researcher"
    description: str = "Searches project data to answer questions and find information"
    allowed_tools: list[str] = [
        "search.search_project",
    ]

    def execute(self, project_id: int, objective: str, executor=None) -> dict:
        search_result = executor.execute("search.search_project", project_id=project_id, query=objective)

        if not search_result["success"]:
            error_msg = search_result.get("error", "")
            if "404:" in error_msg:
                raise HTTPException(status_code=404, detail="Project not found")
            return {
                "agent": self.name,
                "objective": objective,
                "results": {"tasks": [], "sessions": [], "artifacts": []},
                "statistics": {"tasks": 0, "sessions": 0, "artifacts": 0, "total": 0},
                "summary": "No project information matched the query.",
            }

        results = search_result["result"]
        tasks = results.get("tasks", [])
        sessions = results.get("sessions", [])
        artifacts = results.get("artifacts", [])

        total = len(tasks) + len(sessions) + len(artifacts)

        parts = []
        if tasks:
            parts.append(f"{len(tasks)} matching task(s)")
        if sessions:
            parts.append(f"{len(sessions)} session(s)")
        if artifacts:
            parts.append(f"{len(artifacts)} artifact(s)")

        if parts:
            summary = f"Found {' and '.join(parts)} related to {objective}."
        else:
            summary = "No project information matched the query."

        return {
            "agent": self.name,
            "objective": objective,
            "results": {
                "tasks": tasks,
                "sessions": sessions,
                "artifacts": artifacts,
            },
            "statistics": {
                "tasks": len(tasks),
                "sessions": len(sessions),
                "artifacts": len(artifacts),
                "total": total,
            },
            "summary": summary,
        }


class ArchitectAgent(BaseAgent):
    name: str = "architect"
    description: str = "Analyzes project world state and architecture readiness"
    allowed_tools: list[str] = [
        "memory.get_project_context",
        "opencode.analyze_repository",
        "opencode.generate_plan",
    ]

    def execute(self, project_id: int, objective: str, executor=None) -> dict:
        context_result = executor.execute("memory.get_project_context", project_id=project_id)

        if not context_result["success"]:
            error_msg = context_result.get("error", "")
            if "404:" in error_msg:
                raise HTTPException(status_code=404, detail="Project not found")
            return {
                "agent": self.name,
                "objective": objective,
                "project_overview": {"tasks": 0, "sessions": 0, "artifacts": 0},
                "health": {"status": "unknown", "score": 0, "reason": "Unable to retrieve project context"},
                "opencode": {},
                "recommendations": [],
            }

        context = context_result["result"]
        tasks = context.get("tasks", [])
        sessions = context.get("recent_sessions", [])
        artifacts = context.get("recent_artifacts", [])

        task_counts = {
            "todo": sum(1 for t in tasks if t.get("status") == "todo"),
            "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
            "blocked": sum(1 for t in tasks if t.get("status") == "blocked"),
            "completed": sum(1 for t in tasks if t.get("status") == "completed"),
        }

        engine = DecisionEngine()
        summary = {"task_counts": task_counts}
        health = engine.project_health(summary)

        total = sum(task_counts.values())
        recommendations = []
        if task_counts["blocked"] > 0:
            recommendations.append("Resolve blockers before changing architecture.")
        elif task_counts["in_progress"] > 0:
            recommendations.append("Stabilize current implementation before architectural changes.")
        elif total > 0 and task_counts["completed"] == total:
            recommendations.append("Architecture appears stable.")
        else:
            recommendations.append("Continue incremental implementation.")

        opencode_plan = OpenCodeAdapter().generate_plan(
            project_id=project_id,
            objective=objective,
        )

        return {
            "agent": self.name,
            "objective": objective,
            "project_overview": {
                "tasks": len(tasks),
                "sessions": len(sessions),
                "artifacts": len(artifacts),
            },
            "health": health,
            "opencode": opencode_plan,
            "recommendations": recommendations,
        }


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def list_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def agent_exists(self, name: str) -> bool:
        return name in self._agents


def create_default_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(PlannerAgent())
    registry.register(ResearchAgent())
    registry.register(ArchitectAgent())
    return registry


agent_registry = create_default_registry()
