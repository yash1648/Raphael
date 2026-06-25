from app.services import DecisionEngine

engine = DecisionEngine()


def make_task(title: str, status: str, priority: int = 0) -> dict:
    return {"title": title, "status": status, "priority": priority}


def make_summary(**counts) -> dict:
    return {
        "task_counts": {
            "completed": counts.get("completed", 0),
            "in_progress": counts.get("in_progress", 0),
            "blocked": counts.get("blocked", 0),
            "todo": counts.get("todo", 0),
        }
    }


def make_active_work(blocked: list | None = None, in_progress: list | None = None) -> dict:
    return {
        "blocked_tasks": blocked or [],
        "in_progress_tasks": in_progress or [],
    }


class TestPrioritizeTasks:
    def test_blocked_first(self):
        tasks = [
            make_task("Todo", "todo", 1),
            make_task("Blocked", "blocked", 5),
            make_task("In Progress", "in_progress", 3),
        ]
        result = engine.prioritize_tasks(tasks)
        assert result[0]["title"] == "Blocked"
        assert result[1]["title"] == "In Progress"
        assert result[2]["title"] == "Todo"

    def test_highest_priority_within_status(self):
        tasks = [
            make_task("Low", "blocked", 1),
            make_task("High", "blocked", 10),
        ]
        result = engine.prioritize_tasks(tasks)
        assert result[0]["title"] == "High"
        assert result[1]["title"] == "Low"

    def test_completed_last(self):
        tasks = [
            make_task("Done", "completed"),
            make_task("Active", "in_progress"),
        ]
        result = engine.prioritize_tasks(tasks)
        assert result[0]["title"] == "Active"
        assert result[1]["title"] == "Done"

    def test_empty_list(self):
        assert engine.prioritize_tasks([]) == []


class TestFindBlockers:
    def test_returns_blocked_tasks(self):
        tasks = [
            make_task("A", "blocked"),
            make_task("B", "todo"),
            make_task("C", "blocked"),
        ]
        result = engine.find_blockers(tasks)
        assert len(result) == 2
        assert result[0]["title"] == "A"
        assert result[1]["title"] == "C"

    def test_no_blockers(self):
        tasks = [make_task("A", "todo"), make_task("B", "completed")]
        assert engine.find_blockers(tasks) == []

    def test_empty_list(self):
        assert engine.find_blockers([]) == []


class TestRecommendNextAction:
    def test_blocked_recommendation(self):
        result = engine.recommend_next_action(
            make_summary(blocked=2),
            make_active_work(blocked=[make_task("X", "blocked"), make_task("Y", "blocked")]),
        )
        assert result["action"] == "resolve_blockers"
        assert "X" in result["reason"]

    def test_in_progress_recommendation(self):
        result = engine.recommend_next_action(
            make_summary(in_progress=2),
            make_active_work(in_progress=[make_task("A", "in_progress")]),
        )
        assert result["action"] == "finish_in_progress"

    def test_todo_recommendation(self):
        result = engine.recommend_next_action(
            make_summary(todo=3),
            make_active_work(),
        )
        assert result["action"] == "start_todo"
        assert "3" in result["reason"]

    def test_complete_recommendation(self):
        result = engine.recommend_next_action(
            make_summary(completed=5),
            make_active_work(),
        )
        assert result["action"] == "no_action_needed"

    def test_empty_recommendation(self):
        result = engine.recommend_next_action(make_summary(), make_active_work())
        assert result["action"] == "no_action_needed"

    def test_blocked_overrides_in_progress(self):
        result = engine.recommend_next_action(
            make_summary(blocked=1, in_progress=2),
            make_active_work(blocked=[make_task("B", "blocked")], in_progress=[make_task("IP", "in_progress")]),
        )
        assert result["action"] == "resolve_blockers"


class TestProjectHealth:
    def test_blocked_project(self):
        result = engine.project_health(make_summary(blocked=2, completed=3, total=5))
        assert result["status"] == "blocked"
        assert 0 <= result["score"] <= 100

    def test_active_project_in_progress(self):
        result = engine.project_health(make_summary(in_progress=2, completed=3, todo=1))
        assert result["status"] == "active"
        assert result["score"] > 50

    def test_active_project_todo_only(self):
        result = engine.project_health(make_summary(todo=5))
        assert result["status"] == "active"
        assert result["score"] == 20

    def test_active_project_partial(self):
        result = engine.project_health(make_summary(completed=3, todo=2))
        assert result["status"] == "active"
        assert 60 <= result["score"] <= 90

    def test_completed_project(self):
        result = engine.project_health(make_summary(completed=10))
        assert result["status"] == "complete"
        assert result["score"] == 100

    def test_empty_project(self):
        result = engine.project_health(make_summary())
        assert result["status"] == "complete"
        assert result["score"] == 100
