"""Tests for the multi-agent orchestration system."""

from app.orchestration.swarm import SwarmManager, SwarmTask


class TestSwarmTask:
    def test_task_creation(self):
        task = SwarmTask(agent_type="research", task="Find information")
        assert task.agent_type == "research"
        assert task.task == "Find information"
        assert task.task_id is not None
        assert task.result is None
        assert task.error is None

    def test_task_duration(self):
        task = SwarmTask(agent_type="code", task="Write code")
        assert task.duration == 0  # Not started


class TestSwarmManager:
    def test_manager_creation(self):
        manager = SwarmManager(max_parallel=2)
        assert manager.max_parallel == 2
        manager.shutdown()

    def test_execute_empty_tasks(self):
        manager = SwarmManager()
        results = manager.execute_parallel([])
        assert results == []
        manager.shutdown()

    def test_execute_single_task_fails_gracefully(self):
        """Swarm should handle unknown agent types gracefully."""
        manager = SwarmManager()
        task = SwarmTask(agent_type="nonexistent", task="test")
        results = manager.execute_parallel([task])
        assert len(results) == 1
        # Should have error set (from ValueError caught in execute_parallel)
        assert results[0].error is not None
        manager.shutdown()
