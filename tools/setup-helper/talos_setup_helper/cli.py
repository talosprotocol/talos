import click
from rich.console import Console

console = Console()

@click.group()
def main():
    """Talos Local Setup Helper - Secure Infrastructure Agent"""
    pass

from pathlib import Path
from .agent import Agent

APP_DIR = Path.home() / ".talos" / "helper"

@main.command()
@click.argument('token')
@click.option('--dashboard', default='http://localhost:3000', help='Dashboard URL')
def pair(token: str, dashboard: str):
    """Pair this helper with the Talos Dashboard"""
    console.print(f"[bold blue]Initiating pairing with {dashboard}...[/bold blue]")
    try:
        agent = Agent(APP_DIR)
        agent.pair(dashboard, token)
        console.print("[bold green]Pairing successful![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Pairing failed: {e}[/bold red]")

@main.command()
def start():
    """Start the agent event loop"""
    console.print(f"[bold green]Starting Talos Setup Helper (Root: {APP_DIR})...[/bold green]")
    try:
        agent = Agent(APP_DIR)
        agent.run()
    except Exception as e:
        console.print(f"[bold red]Agent error: {e}[/bold red]")

if __name__ == '__main__':
    main()
