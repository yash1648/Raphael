"""Vector memory system using ChromaDB for semantic search and recall."""

import uuid
from datetime import datetime, timezone
from typing import Any

import chromadb
from chromadb.config import Settings


class MemoryEntry:
    """A single memory entry with content and metadata."""

    def __init__(
        self,
        content: str,
        memory_type: str = "general",
        project_id: int = 0,
        source: str = "",
        metadata: dict[str, Any] | None = None,
        entry_id: str | None = None,
        timestamp: str | None = None,
    ):
        self.id = entry_id or str(uuid.uuid4())
        self.content = content
        self.memory_type = memory_type
        self.project_id = project_id
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "project_id": self.project_id,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class VectorMemory:
    """Persistent vector memory using ChromaDB with semantic search."""

    def __init__(self, persist_directory: str = "./chroma_memory"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        # Main collections
        self._collections = {}

    def _get_collection(self, name: str = "raphael_memory"):
        if name not in self._collections:
            try:
                self._collections[name] = self.client.get_collection(name)
            except Exception:
                try:
                    self._collections[name] = self.client.create_collection(name)
                except Exception:
                    raise
        return self._collections[name]

    def store(self, entry: MemoryEntry, collection: str = "raphael_memory") -> str:
        """Store a memory entry."""
        col = self._get_collection(collection)
        col.add(
            documents=[entry.content],
            metadatas=[{
                "memory_type": entry.memory_type,
                "project_id": str(entry.project_id),
                "source": entry.source,
                "timestamp": entry.timestamp,
                **entry.metadata,
            }],
            ids=[entry.id],
        )
        return entry.id

    def store_many(self, entries: list[MemoryEntry], collection: str = "raphael_memory") -> list[str]:
        """Store multiple memory entries at once."""
        col = self._get_collection(collection)
        ids = []
        documents = []
        metadatas = []
        for entry in entries:
            ids.append(entry.id)
            documents.append(entry.content)
            metadatas.append({
                "memory_type": entry.memory_type,
                "project_id": str(entry.project_id),
                "source": entry.source,
                "timestamp": entry.timestamp,
                **entry.metadata,
            })
        col.add(documents=documents, metadatas=metadatas, ids=ids)
        return ids

    def search(
        self,
        query: str,
        n_results: int = 5,
        project_id: int | None = None,
        memory_type: str | None = None,
        collection: str = "raphael_memory",
    ) -> list[dict]:
        """Semantic search across memory."""
        col = self._get_collection(collection)
        where_filter = {}
        if project_id is not None:
            where_filter["project_id"] = str(project_id)
        if memory_type:
            where_filter["memory_type"] = memory_type

        results = col.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None,
        )

        entries = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                entries.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return entries

    def recall_recent(self, n: int = 10, project_id: int | None = None, collection: str = "raphael_memory") -> list[dict]:
        """Retrieve most recent memory entries."""
        col = self._get_collection(collection)
        where_filter = {}
        if project_id is not None:
            where_filter["project_id"] = str(project_id)

        results = col.get(
            where=where_filter if where_filter else None,
            limit=n,
        )
        entries = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                entries.append({
                    "id": doc_id,
                    "content": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
        return entries

    def delete(self, entry_id: str, collection: str = "raphael_memory") -> None:
        """Delete a memory entry by ID."""
        col = self._get_collection(collection)
        col.delete(ids=[entry_id])

    def count(self, collection: str = "raphael_memory") -> int:
        """Get total memory entries count."""
        col = self._get_collection(collection)
        return col.count()
