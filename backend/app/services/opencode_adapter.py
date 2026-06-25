class OpenCodeAdapter:
    def analyze_repository(self, project_id: int, repo_path: str, objective: str) -> dict:
        return {
            "status": "not_implemented",
            "action": "analyze_repository",
            "project_id": project_id,
            "repo_path": repo_path,
            "objective": objective,
        }

    def search_code(self, project_id: int, repo_path: str, query: str) -> dict:
        return {
            "status": "not_implemented",
            "action": "search_code",
            "project_id": project_id,
            "repo_path": repo_path,
            "query": query,
        }

    def review_changes(self, project_id: int, repo_path: str) -> dict:
        return {
            "status": "not_implemented",
            "action": "review_changes",
            "project_id": project_id,
            "repo_path": repo_path,
        }

    def generate_plan(self, project_id: int, objective: str) -> dict:
        return {
            "status": "not_implemented",
            "action": "generate_plan",
            "project_id": project_id,
            "objective": objective,
        }
