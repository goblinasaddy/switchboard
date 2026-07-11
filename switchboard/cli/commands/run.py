import asyncio
import typer
from rich.console import Console
from switchboard.kernel.bootstrap import bootstrap_platform

console = Console()

def run_command(
    config: str = typer.Option(None, "--config", "-c", help="Path to setting TOML file."),
    log_level: str = typer.Option(None, "--log-level", "-l", help="Logger level override (DEBUG, INFO, etc.).")
) -> None:
    """
    Bootstrap, initialize, and execute the SwitchBoard platform.
    """
    overrides = {}
    if log_level:
        overrides["log_level"] = log_level

    async def _main_loop() -> None:
        kernel = await bootstrap_platform(config_path=config, overrides=overrides)
        
        # Transition state: Uninitialized -> Initializing -> Stopped (if failed)
        await kernel.initialize()
        
        # Transition state: Initializing -> Running
        await kernel.start()
        
        console.print("\n[bold green]SwitchBoard Platform successfully started and running.[/bold green]")
        console.print("Press Ctrl+C to safely shut down.\n")
        
        # Keep running until cancelled
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger = kernel.get_service("event_bus") # generic log/check
            if logger:
                console.print("[yellow]Cancellation received...[/yellow]")
        finally:
            # Transition state: Running -> Shutting Down -> Stopped
            await kernel.shutdown()

    try:
        asyncio.run(_main_loop())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown signal received. Cleaning up systems...[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal platform error: {e}[/bold red]")
        raise typer.Exit(code=1)
