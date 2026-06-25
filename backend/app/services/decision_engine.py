STATUS_ORDER = {"blocked": 0, "in_progress": 1, "todo": 2, "completed": 3}


class DecisionEngine:
    def prioritize_tasks(self, tasks: list[dict]) -> list[dict]:
        def sort_key(task):
            return (
                STATUS_ORDER.get(task.get("status", "todo"), 99),
                -task.get("priority", 0),
            )

        return sorted(tasks, key=sort_key)

    def find_blockers(self, tasks: list[dict]) -> list[dict]:
        return [t for t in tasks if t.get("status") == "blocked"]

    def recommend_next_action(self, summary: dict, active_work: dict) -> dict:
        counts = summary.get("task_counts", {})
        blocked_tasks = active_work.get("blocked_tasks", [])
        in_progress_tasks = active_work.get("in_progress_tasks", [])

        if counts.get("blocked", 0) > 0:
            names = [t["title"] for t in blocked_tasks]
            return {
                "action": "resolve_blockers",
                "reason": f"Resolve {counts['blocked']} blocked task(s): {', '.join(names)}",
            }

        if counts.get("in_progress", 0) > 0:
            names = [t["title"] for t in in_progress_tasks]
            return {
                "action": "finish_in_progress",
                "reason": f"Finish {counts['in_progress']} in-progress task(s): {', '.join(names)}",
            }

        if counts.get("todo", 0) > 0:
            return {
                "action": "start_todo",
                "reason": f"Start highest-priority todo task among {counts['todo']} pending",
            }

        return {
            "action": "no_action_needed",
            "reason": "Project appears complete — no outstanding tasks",
        }

    def project_health(self, summary: dict) -> dict:
        counts = summary.get("task_counts", {})
        completed = counts.get("completed", 0)
        in_progress = counts.get("in_progress", 0)
        blocked = counts.get("blocked", 0)
        todo = counts.get("todo", 0)
        total = completed + in_progress + blocked + todo

        if total == 0:
            return {"status": "complete", "score": 100, "reason": "No tasks defined"}

        if blocked > 0:
            completion_ratio = completed / total if total > 0 else 0
            score = max(10, int(completion_ratio * 100 - blocked * 5))
            return {
                "status": "blocked",
                "score": score,
                "reason": f"{blocked} task(s) blocked — resolve before continuing",
            }

        if in_progress > 0:
            completion_ratio = completed / total
            score = min(90, int(50 + completion_ratio * 40))
            return {
                "status": "active",
                "score": score,
                "reason": f"{in_progress} task(s) in progress — {completed}/{total} complete",
            }

        if todo > 0 and completed == 0:
            return {
                "status": "active",
                "score": 20,
                "reason": f"{todo} pending task(s) — no work started yet",
            }

        if todo > 0 and completed > 0:
            ratio = completed / total
            score = int(60 + ratio * 30)
            return {
                "status": "active",
                "score": min(90, score),
                "reason": f"{completed}/{total} tasks complete — {todo} remaining",
            }

        return {
            "status": "complete",
            "score": 100,
            "reason": "All tasks completed",
        }
