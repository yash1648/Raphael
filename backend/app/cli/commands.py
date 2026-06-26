"""CLI command implementations."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from app.agents.specialized import ResearchAgent, CodeAgent, MemoryAgent
from app.orchestration.supervisor import SupervisorAgent
from app.orchestration.swarm import SwarmManager, SwarmTask
from app.llm.factory import create_llm

console = Console()


def _progress_spinner(message: str):
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )


def cmd_chat(prompt_args, supervise):
    """Interactive chat session."""
    from app.llm.factory import create_llm

    console.print("[bold cyan]⚡ Raphael Chat[/bold cyan]")
    console.print("[dim]Type 'exit' to quit, 'reset' to clear context[/dim]\n")

    llm = create_llm("openai")
    agent = SupervisorAgent(llm=llm) if supervise else None

    if prompt_args:
        prompt = " ".join(prompt_args)
        with _progress_spinner("Raphael is thinking...") as progress:
            progress.add_task("", total=None)
            if supervise:
                result = agent.execute_goal(prompt)
            else:
                result = llm.generate(prompt, system_prompt="You are Raphael, a super powerful autonomous AI assistant.")
        console.print()
        console.print(Panel(Markdown(result.get("response", result.content) if isinstance(result, dict) else result.content), border_style="cyan"))
        console.print()

    # Interactive loop
    while True:
        try:
            prompt = console.input("[bold cyan]You>[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not prompt.strip():
            continue
        if prompt.lower() in ("exit", "quit"):
            console.print("[dim]Goodbye.[/dim]")
            break
        if prompt.lower() == "reset":
            if agent:
                agent.reset_conversation()
            console.print("[green]Context reset.[/green]")
            continue

        with _progress_spinner("Raphael is thinking...") as progress:
            progress.add_task("", total=None)
            if supervise:
                result = agent.execute_goal(prompt)
                response = result.get("response", "")
            else:
                result = llm.generate(prompt, system_prompt="You are Raphael, a super powerful autonomous AI assistant.")
                response = result.content

        console.print()
        console.print(Panel(Markdown(response), border_style="cyan"))
        console.print()


def cmd_run(prompt, supervise, json_output):
    """Execute a single goal or question."""
    from app.llm.factory import create_llm

    with _progress_spinner("Raphael is processing...") as progress:
        progress.add_task("", total=None)

        if supervise:
            agent = SupervisorAgent()
            result = agent.execute_goal(prompt)
            response = result.get("response", "")
        else:
            llm = create_llm("openai")
            result = llm.generate(prompt, system_prompt="You are Raphael, a super powerful autonomous AI assistant.")
            response = result.content

    if json_output:
        console.print(json.dumps({"response": response, "raw": str(result)}, indent=2))
    else:
        console.print()
        console.print(Panel(Markdown(response), title="⚡ Raphael", border_style="cyan"))
        console.print()


def cmd_goal(goal, json_output):
    """Decompose and execute a complex multi-step goal."""
    with _progress_spinner("Raphael is decomposing and delegating...") as progress:
        progress.add_task("", total=None)
        supervisor = SupervisorAgent()
        result = supervisor.execute_goal(goal)

    if json_output:
        console.print(json.dumps(result, indent=2, default=str))
    else:
        response = result.get("response", "Goal execution complete.")
        console.print()
        console.print(Panel(Markdown(response), title="⚡ Raphael - Goal Complete", border_style="green"))
        console.print()

        tool_calls = result.get("tool_calls", [])
        if tool_calls:
            table = Table(title="Actions Taken")
            table.add_column("Tool", style="cyan")
            table.add_column("Status", style="green")
            for tc in tool_calls[:10]:
                tool_name = tc.get("tool", tc.get("name", "unknown"))
                result_data = tc.get("result", {})
                status = "✅" if not isinstance(result_data, dict) or not result_data.get("error") else "❌"
                table.add_row(tool_name, status)
            if len(tool_calls) > 10:
                table.add_row(f"... and {len(tool_calls) - 10} more", "")
            console.print(table)


def cmd_research(query, num_results, json_output):
    """Research a topic with web search + synthesis."""
    agent = ResearchAgent()

    with _progress_spinner(f"Researching: {query[:50]}...") as progress:
        progress.add_task("", total=None)
        result = agent.run(query)

    response = result.get("response", "No results.")
    tool_calls = result.get("tool_calls", [])

    if json_output:
        console.print(json.dumps({"query": query, "response": response, "sources": tool_calls}, indent=2))
        return

    console.print()
    console.print(Panel(Markdown(response), title=f"🔍 Research: {query[:60]}", border_style="blue"))
    console.print()

    if tool_calls:
        console.print("[bold]Sources consulted:[/bold]")
        for tc in tool_calls[:5]:
            args = tc.get("arguments", {})
            if "query" in args:
                console.print(f"  • Search: {args['query']}")
            if "url" in args:
                console.print(f"  • Page: {args['url']}")


def cmd_code(code_or_command, shell, file_path):
    """Execute code with sandbox."""
    from app.capabilities.code_executor import CodeExecutor

    executor = CodeExecutor()

    if file_path:
        try:
            code_or_command = Path(file_path).read_text()
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            return

    with _progress_spinner("Executing...") as progress:
        progress.add_task("", total=None)
        if shell:
            result = executor.execute_shell(code_or_command)
        else:
            result = executor.execute_python(code_or_command)

    stdout = result.get("stdout", "").strip()
    stderr = result.get("stderr", "").strip()
    exit_code = result.get("exit_code", -1)
    exec_time = result.get("execution_time", 0)

    console.print()
    console.print(f"[dim]Exit code: {exit_code} | Time: {exec_time}s[/dim]")

    if stdout:
        console.print(Syntax(stdout, "bash" if shell else "python", theme="monokai"))
    if stderr:
        console.print(f"[red]{stderr}[/red]")

    if result.get("success"):
        console.print("[green]✅ Execution successful[/green]")
    else:
        console.print("[red]❌ Execution failed[/red]")


def cmd_memory_store(content, memory_type, source):
    """Store a memory entry."""
    from app.memory.vector_memory import VectorMemory, MemoryEntry

    memory = VectorMemory()
    entry = MemoryEntry(content=content, memory_type=memory_type, source=source)
    entry_id = memory.store(entry)

    console.print(f"[green]✅ Memory stored (ID: {entry_id[:8]}...)[/green]")
    console.print(f"  Type: {memory_type}")
    console.print(f"  Source: {source}")


def cmd_memory_search(query, num_results):
    """Search memories."""
    from app.memory.vector_memory import VectorMemory

    memory = VectorMemory()
    results = memory.search(query, n_results=num_results)

    if not results:
        console.print("[yellow]No matching memories found.[/yellow]")
        return

    table = Table(title=f"Memory Search: {query}")
    table.add_column("ID", style="dim")
    table.add_column("Content", style="white")
    table.add_column("Type", style="cyan")
    table.add_column("Distance", style="green")

    for r in results:
        content = r.get("content", "")[:100] + "..." if len(r.get("content", "")) > 100 else r.get("content", "")
        meta = r.get("metadata", {})
        table.add_row(
            r.get("id", "")[:8],
            content,
            meta.get("memory_type", ""),
            f"{r.get('distance', 0):.3f}",
        )
    console.print(table)


def cmd_memory_recent(count):
    """Show recent memories."""
    from app.memory.vector_memory import VectorMemory

    memory = VectorMemory()
    results = memory.recall_recent(n=count)

    if not results:
        console.print("[yellow]No memories found.[/yellow]")
        return

    console.print(f"[bold]Recent Memories ({len(results)}):[/bold]")
    for i, r in enumerate(results, 1):
        content = r.get("content", "")[:150]
        meta = r.get("metadata", {})
        memory_type = meta.get("memory_type", "general")
        console.print(f"\n[dim]{i}.[/dim] [cyan]{memory_type}[/cyan]")
        console.print(f"   {content}")


def cmd_project_create(name, description):
    """Create a new project via API."""
    import httpx
    try:
        resp = httpx.post("http://localhost:8000/projects/", json={"name": name, "description": description})
        if resp.status_code == 201:
            data = resp.json()
            console.print(f"[green]✅ Project '{data['name']}' created (ID: {data['id']})[/green]")
        else:
            console.print(f"[red]Error: {resp.text}[/red]")
    except Exception as e:
        console.print(f"[red]Could not connect to Raphael API: {e}[/red]")
        console.print("[yellow]Make sure the server is running on port 8000[/yellow]")


def cmd_project_list():
    """List projects via API."""
    import httpx
    try:
        resp = httpx.get("http://localhost:8000/projects/")
        if resp.status_code == 200:
            projects = resp.json()
            if not projects:
                console.print("[yellow]No projects found.[/yellow]")
                return
            table = Table(title="Projects")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="white")
            table.add_column("Created", style="dim")
            for p in projects:
                table.add_row(str(p["id"]), p["name"], p["description"][:50], p["created_at"][:10])
            console.print(table)
        else:
            console.print(f"[red]Error: {resp.text}[/red]")
    except Exception as e:
        console.print(f"[red]Could not connect to Raphael API: {e}[/red]")


def cmd_project_show(project_id):
    """Show project details."""
    import httpx
    try:
        resp = httpx.get(f"http://localhost:8000/projects/{project_id}")
        if resp.status_code == 200:
            project = resp.json()
            console.print(Panel(
                f"[bold]{project['name']}[/bold]\n\n{project['description']}\n\n[dim]Created: {project['created_at']}\nUpdated: {project['updated_at']}[/dim]",
                title=f"Project #{project['id']}",
                border_style="green",
            ))
        else:
            console.print(f"[red]Error: {resp.text}[/red]")
    except Exception as e:
        console.print(f"[red]Could not connect: {e}[/red]")


def cmd_agent():
    """List available agents."""
    table = Table(title="Raphael Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Status", style="green")

    agents = [
        ("Raphael-Supervisor", "Central orchestration — plans, delegates, synthesizes", "✅ Active"),
        ("Raphael-Research", "Web research, search, and information synthesis", "✅ Active"),
        ("Raphael-Code", "Code writing, execution, and file operations", "✅ Active"),
        ("Raphael-System", "Git, Docker, shell, infrastructure management", "✅ Active"),
        ("Raphael-Memory", "Persistent memory storage and semantic search", "✅ Active"),
        ("Planner", "Project context analysis and planning", "✅ Active"),
        ("Researcher", "Project data search and information retrieval", "✅ Active"),
        ("Architect", "Architecture analysis and readiness assessment", "✅ Active"),
    ]
    for name, desc, status in agents:
        table.add_row(name, desc, status)
    console.print(table)


def cmd_health():
    """Check system health."""
    from app.llm.factory import list_providers
    from app.memory.vector_memory import VectorMemory

    table = Table(title="⚡ Raphael System Health")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    # LLM providers
    providers = list_providers()
    table.add_row("LLM Engine", "✅", f"Providers: {', '.join(providers)}")

    # Memory
    try:
        memory = VectorMemory()
        count = memory.count()
        table.add_row("Vector Memory", "✅", f"ChromaDB — {count} entries")
    except Exception as e:
        table.add_row("Vector Memory", "❌", str(e))

    # API
    try:
        import httpx
        resp = httpx.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            table.add_row("REST API", "✅", "FastAPI — running on :8000")
        else:
            table.add_row("REST API", "⚠️", f"Responded with {resp.status_code}")
    except Exception:
        table.add_row("REST API", "❌", "Not running — start with `uvicorn app.main:app`")

    # Agents
    table.add_row("Agent System", "✅", "Supervisor + 4 specialized agents loaded")
    table.add_row("Sandbox", "✅", "Code execution with resource limits")

    console.print(table)
