"""Tests for the vector memory system (ChromaDB)."""

import tempfile
import shutil

from app.memory.vector_memory import VectorMemory, MemoryEntry


def _cleanup(memory):
    """Clean up the temp directory after test."""
    if hasattr(memory, 'client'):
        pass


def test_store_and_count():
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(persist_directory=tmpdir)
        entry = MemoryEntry(content="Test memory content", memory_type="test")
        entry_id = memory.store(entry)
        assert entry_id is not None
        assert len(entry_id) > 0
        assert memory.count() == 1


def test_store_and_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(persist_directory=tmpdir)
        memory.store(MemoryEntry(content="Python is a programming language", memory_type="fact"))
        memory.store(MemoryEntry(content="The sky is blue on a clear day", memory_type="fact"))

        results = memory.search("programming language", n_results=5)
        assert len(results) > 0
        assert any("Python" in r["content"] for r in results)


def test_search_with_project_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(persist_directory=tmpdir)
        memory.store(MemoryEntry(content="Project Alpha details", memory_type="general", project_id=1))
        memory.store(MemoryEntry(content="Project Beta details", memory_type="general", project_id=2))

        results = memory.search("details", project_id=1, n_results=5)
        assert len(results) > 0
        # All results should be from project 1
        for r in results:
            assert r["metadata"]["project_id"] == "1"


def test_recall_recent():
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(persist_directory=tmpdir)
        for i in range(5):
            memory.store(MemoryEntry(content=f"Memory entry {i}", memory_type="test"))

        recent = memory.recall_recent(n=3)
        assert len(recent) == 3


def test_delete_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(persist_directory=tmpdir)
        entry = MemoryEntry(content="To be deleted", memory_type="test")
        entry_id = memory.store(entry)
        assert memory.count() == 1

        memory.delete(entry_id)
        assert memory.count() == 0


def test_store_many():
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(persist_directory=tmpdir)
        entries = [
            MemoryEntry(content=f"Batch entry {i}", memory_type="batch")
            for i in range(10)
        ]
        ids = memory.store_many(entries)
        assert len(ids) == 10
        assert memory.count() == 10


def test_search_returns_distance():
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(persist_directory=tmpdir)
        memory.store(MemoryEntry(content="Artificial intelligence and machine learning", memory_type="fact"))
        memory.store(MemoryEntry(content="I like pizza with pepperoni", memory_type="fact"))

        results = memory.search("AI", n_results=5)
        assert len(results) > 0
        assert "distance" in results[0]
        assert results[0]["distance"] >= 0


def test_memory_entry_defaults():
    entry = MemoryEntry(content="Test")
    assert entry.id is not None
    assert entry.memory_type == "general"
    assert entry.project_id == 0
    assert entry.source == ""
    assert entry.metadata == {}
    assert entry.timestamp is not None


def test_memory_entry_to_dict():
    entry = MemoryEntry(content="Test", memory_type="fact", source="test")
    d = entry.to_dict()
    assert d["content"] == "Test"
    assert d["memory_type"] == "fact"
    assert d["source"] == "test"
