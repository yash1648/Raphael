"""Raphael super-assistant API routes — exposes LLM, agents, capabilities, and memory."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.specialized import ResearchAgent, CodeAgent, SystemAgent, MemoryAgent
from app.capabilities.web_search import WebSearchTool
from app.capabilities.code_executor import CodeExecutor
from app.llm.factory import create_llm, list_providers
from app.memory.vector_memory import VectorMemory, MemoryEntry
from app.orchestration.supervisor import SupervisorAgent
from app.orchestration.swarm import SwarmManager, SwarmTask

router = APIRouter(prefix="/raphael", tags=["raphael"])


# ── Request/Response Models ──

class ChatRequest(BaseModel):
    message: str
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    provider: str = "openai"
    model: str | None = None


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    usage: dict


class AgentExecuteRequest(BaseModel):
    task: str
    agent_type: str = "supervisor"  # supervisor, research, code, system, memory


class AgentExecuteResponse(BaseModel):
    agent: str
    response: str
    tool_calls: list[dict] = []
    iterations: int = 0


class CodeExecuteRequest(BaseModel):
    code: str
    language: str = "python"  # python or shell


class CodeExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    success: bool


class SearchRequest(BaseModel):
    query: str
    num_results: int = 5


class MemoryStoreRequest(BaseModel):
    content: str
    memory_type: str = "general"
    source: str = "api"


class MemorySearchRequest(BaseModel):
    query: str
    n_results: int = 5


class SwarmRequest(BaseModel):
    goal: str
    tasks: list[dict]  # [{"agent": "research", "task": "..."}, ...]


# ── Routes ──

@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    """Chat with Raphael's LLM engine."""
    try:
        llm = create_llm(body.provider, model=body.model)
        result = llm.generate(
            prompt=body.message,
            system_prompt=body.system_prompt or "You are Raphael, a super powerful autonomous AI assistant.",
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
        return ChatResponse(
            response=result.content,
            provider=result.provider,
            model=result.model,
            usage=result.usage,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/execute", response_model=AgentExecuteResponse)
def execute_agent(body: AgentExecuteRequest):
    """Execute a task with a specific agent."""
    agent_map = {
        "supervisor": SupervisorAgent,
        "research": ResearchAgent,
        "code": CodeAgent,
        "system": SystemAgent,
        "memory": MemoryAgent,
    }
    agent_cls = agent_map.get(body.agent_type)
    if not agent_cls:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {body.agent_type}. Available: {list(agent_map.keys())}")

    try:
        agent = agent_cls()
        result = agent.run(body.task)
        return AgentExecuteResponse(
            agent=body.agent_type,
            response=result.get("response", ""),
            tool_calls=result.get("tool_calls", []),
            iterations=result.get("iterations", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/code", response_model=CodeExecuteResponse)
def execute_code(body: CodeExecuteRequest):
    """Execute code in the sandbox."""
    executor = CodeExecutor()
    if body.language == "shell":
        result = executor.execute_shell(body.code)
    else:
        result = executor.execute_python(body.code)
    return CodeExecuteResponse(
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        exit_code=result.get("exit_code", -1),
        execution_time=result.get("execution_time", 0),
        success=result.get("success", False),
    )


@router.post("/web/search")
def web_search(body: SearchRequest):
    """Search the web."""
    web = WebSearchTool()
    try:
        results = web.search_web(body.query, body.num_results)
        return {"query": body.query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web/fetch")
def web_fetch(url: str):
    """Fetch and extract content from a URL."""
    web = WebSearchTool()
    try:
        result = web.fetch_page(url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/store")
def memory_store(body: MemoryStoreRequest):
    """Store a memory entry."""
    try:
        memory = VectorMemory()
        entry = MemoryEntry(content=body.content, memory_type=body.memory_type, source=body.source)
        entry_id = memory.store(entry)
        return {"status": "stored", "id": entry_id, "content_preview": body.content[:100]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/search")
def memory_search(body: MemorySearchRequest):
    """Search memories semantically."""
    try:
        memory = VectorMemory()
        results = memory.search(body.query, n_results=body.n_results)
        return {"query": body.query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/recent")
def memory_recent(n: int = 10):
    """Get recent memories."""
    try:
        memory = VectorMemory()
        results = memory.recall_recent(n=n)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/count")
def memory_count():
    """Get total memory count."""
    try:
        memory = VectorMemory()
        return {"count": memory.count()}
    except Exception as e:
        # ChromaDB may not be available in all environments
        return {"count": 0, "note": f"Memory unavailable: {e}"}


@router.post("/orchestrate/swarm")
def orchestrate_swarm(body: SwarmRequest):
    """Execute a swarm of tasks in parallel."""
    try:
        manager = SwarmManager()
        tasks = [SwarmTask(t["agent"], t["task"]) for t in body.tasks]
        results = manager.execute_parallel(tasks)

        task_results = []
        for t in results:
            task_results.append({
                "task_id": t.task_id,
                "agent": t.agent_type,
                "task": t.task,
                "duration": t.duration,
                "error": t.error,
                "result_preview": (t.result.get("response", "")[:500] if t.result else ""),
            })

        return {
            "goal": body.goal,
            "total_tasks": len(task_results),
            "successful": sum(1 for t in results if not t.error),
            "failed": sum(1 for t in results if t.error),
            "tasks": task_results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
def list_llm_providers():
    """List available LLM providers."""
    return {"providers": list_providers()}


@router.get("/status")
def raphael_status():
    """Get comprehensive Raphael system status."""
    try:
        memory = VectorMemory()
        memory_count_val = memory.count()
    except Exception:
        memory_count_val = -1

    return {
        "name": "Raphael",
        "version": "1.0.0",
        "llm_providers": list_providers(),
        "memory_entries": memory_count_val,
        "agents": ["supervisor", "research", "code", "system", "memory"],
        "capabilities": ["web_search", "code_execution", "file_operations", "vector_memory"],
        "status": "operational",
    }
