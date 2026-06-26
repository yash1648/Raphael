"""Raphael CLI — the primary interface for interacting with the super assistant."""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

console = Console()
ERROR_STYLE = "bold red"
SUCCESS_STYLE = "bold green"
INFO_STYLE = "bold blue"
WARNING_STYLE = "bold yellow"


def print_banner():
    """Display the Raphael banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    ⚡ RAPHAEL ⚡                              ║
║           Super Powerful Autonomous AI Assistant             ║
║              "I have no strings on me..."                    ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print()


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version")
@click.pass_context
def cli(ctx, version):
    """Raphael — Super Powerful Autonomous AI Assistant."""
    if version:
        console.print("Raphael v1.0.0", style=SUCCESS_STYLE)
        return
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(Panel(
            "[bold]Available Commands:[/bold]\n\n"
            "  [cyan]chat[/cyan]         Start an interactive chat session with Raphael\n"
            "  [cyan]run[/cyan]          Execute a single goal or question\n"
            "  [cyan]goal[/cyan]         Decompose and execute a complex multi-step goal\n"
            "  [cyan]research[/cyan]     Research a topic (web search + synthesis)\n"
            "  [cyan]code[/cyan]         Execute Python code or shell commands\n"
            "  [cyan]memory[/cyan]       Interact with Raphael's memory system\n"
            "  [cyan]project[/cyan]      Manage Raphael projects\n"
            "  [cyan]agent[/cyan]        List and inspect available agents\n"
            "  [cyan]health[/cyan]       Check system health status\n"
            "\n[dim]Run [bold]raphael <command> --help[/bold] for more details.[/dim]",
            title="⚡ Raphael",
            border_style="cyan",
        ))


# Lazy imports for subcommands to keep startup fast
@cli.command()
@click.argument("prompt", nargs=-1, required=False)
@click.option("--supervise", "-s", is_flag=True, help="Use supervisor agent for complex tasks")
def chat(prompt, supervise):
    """Start an interactive chat session with Raphael."""
    from app.cli.commands import cmd_chat
    cmd_chat(prompt, supervise)


@cli.command()
@click.argument("prompt", nargs=-1, required=True)
@click.option("--supervise", "-s", is_flag=True, help="Use supervisor for orchestration")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def run(prompt, supervise, json_output):
    """Execute a single goal or question."""
    from app.cli.commands import cmd_run
    cmd_run(" ".join(prompt), supervise, json_output)


@cli.command()
@click.argument("goal", nargs=-1, required=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def goal(goal, json_output):
    """Decompose and execute a complex multi-step goal."""
    from app.cli.commands import cmd_goal
    cmd_goal(" ".join(goal), json_output)


@cli.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--results", "-n", default=5, help="Number of search results")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def research(query, results, json_output):
    """Research a topic — web search + intelligent synthesis."""
    from app.cli.commands import cmd_research
    cmd_research(" ".join(query), results, json_output)


@cli.command()
@click.argument("code_or_command", nargs=-1, required=True)
@click.option("--shell", "-s", is_flag=True, help="Execute as shell command instead of Python")
@click.option("--file", "-f", "file_path", help="Read code from a file")
def code(code_or_command, shell, file_path):
    """Execute Python code or shell commands with sandbox."""
    from app.cli.commands import cmd_code
    cmd_code(" ".join(code_or_command), shell, file_path)


@cli.group()
def memory():
    """Interact with Raphael's persistent memory system."""


@memory.command()
@click.argument("content", nargs=-1, required=True)
@click.option("--type", "memory_type", default="general", help="Memory type (general, fact, decision, code, conversation)")
@click.option("--source", default="cli", help="Source label")
def store(content, memory_type, source):
    """Store a memory entry."""
    from app.cli.commands import cmd_memory_store
    cmd_memory_store(" ".join(content), memory_type, source)


@memory.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--results", "-n", default=5, help="Number of results")
def search(query, results):
    """Semantically search memories."""
    from app.cli.commands import cmd_memory_search
    cmd_memory_search(" ".join(query), results)


@memory.command(name="recent")
@click.option("--count", "-n", default=10, help="Number of recent memories")
def memory_recent(count):
    """Show recent memories."""
    from app.cli.commands import cmd_memory_recent
    cmd_memory_recent(count)


@cli.group()
def project():
    """Manage Raphael projects."""


@project.command()
@click.argument("name")
@click.option("--description", "-d", default="", help="Project description")
def create(name, description):
    """Create a new project."""
    from app.cli.commands import cmd_project_create
    cmd_project_create(name, description)


@project.command(name="list")
def project_list():
    """List all projects."""
    from app.cli.commands import cmd_project_list
    cmd_project_list()


@project.command()
@click.argument("project_id", type=int)
def show(project_id):
    """Show project details with context."""
    from app.cli.commands import cmd_project_show
    cmd_project_show(project_id)


@cli.command()
def agent():
    """List and inspect available agents."""
    from app.cli.commands import cmd_agent
    cmd_agent()


@cli.command()
def health():
    """Check system health status."""
    from app.cli.commands import cmd_health
    cmd_health()


if __name__ == "__main__":
    cli()
