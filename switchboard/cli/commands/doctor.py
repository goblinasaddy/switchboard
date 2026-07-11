import sys
import typer
from rich.console import Console
from switchboard.config.loader import load_config

console = Console()

def doctor_command() -> None:
    """
    Run diagnostic checks to verify system compatibility and dependencies.
    """
    console.print("[bold blue]Executing SwitchBoard Environment Diagnostic Checks...[/bold blue]\n")
    all_ok = True

    # 1. Check Python Version
    py_major, py_minor = sys.version_info.major, sys.version_info.minor
    if py_major == 3 and py_minor >= 12:
        console.print(f"  [green][OK][/green] Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (Compatible)")
    else:
        console.print(f"  [red][FAIL][/red] Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (Incompatible: requires 3.12+)")
        all_ok = False

    # 2. Check Configuration Load
    try:
        settings = load_config()
        console.print(f"  [green][OK][/green] Settings parsed successfully. Env mode: [bold cyan]{settings.env}[/bold cyan]")
    except Exception as e:
        console.print(f"  [red][FAIL][/red] Configuration load failed: {e}")
        all_ok = False
        settings = None

    # 3. Check physical hardware defaults (simulated warning for low RAM/VRAM)
    if settings:
        console.print(f"  [green][OK][/green] Conf. limits -> Max VRAM: {settings.max_vram_gb} GB, Max RAM: {settings.max_ram_gb} GB")
        if settings.max_vram_gb < 6.0:
            console.print("    [yellow][WARN][/yellow] Warning: Configured VRAM is below recommended minimum of 6.0 GB.")

    # 4. Check Compute Layer and Mock Provider loading
    if settings:
        import asyncio
        from switchboard.kernel.bootstrap import bootstrap_platform

        async def _check_compute() -> bool:
            try:
                kernel = await bootstrap_platform()
                await kernel.initialize()
                await kernel.start()
                
                compute_manager = kernel.get_service("compute_manager")
                await compute_manager.load_provider("mock")
                models = await compute_manager.list_models()
                model_names = [m.name for m in models]
                console.print(f"  [green][OK][/green] Compute Layer loaded provider 'mock'. Models: {model_names}")
                
                # Check Ollama connection
                try:
                    await compute_manager.load_provider("ollama")
                    ollama_models = await compute_manager.list_models()
                    ollama_model_names = [m.name for m in ollama_models]
                    console.print(f"  [green][OK][/green] Ollama connection verified at {settings.ollama_url}. Models: {ollama_model_names}")
                except Exception:
                    console.print(f"  [yellow][WARN][/yellow] Ollama offline at {settings.ollama_url}. (Ollama backend not running)")

                await kernel.shutdown()
                return True
            except Exception as ex:
                console.print(f"  [red][FAIL][/red] Compute Layer verification failed: {ex}")
                return False

        compute_ok = asyncio.run(_check_compute())
        if not compute_ok:
            all_ok = False

    # 5. Diagnostics check summary
    print()
    if all_ok:
        console.print("[bold green]All compatibility checks passed! SwitchBoard is ready to run.[/bold green]")
    else:
        console.print("[bold red]Diagnostics failed. Please correct the incompatibilities noted above.[/bold red]")
        raise typer.Exit(code=1)
