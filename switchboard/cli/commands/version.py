import typer
from rich.console import Console

console = Console()

def version_command() -> None:
    """
    Print the current SwitchBoard version.
    """
    console.print("[bold green]SwitchBoard Platform[/bold green] - Version [bold white]0.1.0[/bold white]")
