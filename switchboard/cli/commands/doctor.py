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

                # Check Context Engine
                try:
                    context_manager = kernel.get_service("context_manager")
                    repo_model = await context_manager.scan()
                    langs_summary = {k.value: v for k, v in repo_model.languages.items()}
                    console.print(f"  [green][OK][/green] Context Engine indexed codebase: {repo_model.total_files} files, {repo_model.total_symbols} symbols. Languages: {langs_summary}")
                except Exception as ex:
                    console.print(f"  [red][FAIL][/red] Context Engine indexing failed: {ex}")
                    raise

                # Check Task System
                try:
                    from switchboard.types.task import TaskContext, TaskStatus
                    task_manager = kernel.get_service("task_manager")
                    import os
                    context = TaskContext(repository_root=os.getcwd())
                    task = await task_manager.create_task(
                        name="Doctor Diagnostic Run",
                        objective="Perform diagnostic validation checks",
                        context=context
                    )
                    if task.status == TaskStatus.CREATED:
                        console.print(f"  [green][OK][/green] Task System registered diagnostic task: {task.task_id}")
                    else:
                        raise ValueError(f"Diagnostic task created in invalid status: {task.status}")
                except Exception as ex:
                    console.print(f"  [red][FAIL][/red] Task System verification failed: {ex}")
                    raise

                # Check Execution Engine
                try:
                    execution_engine = kernel.get_service("execution_engine")
                    state = await execution_engine.monitor.get_queue_state()
                    res = execution_engine.monitor.get_resource_snapshot()
                    console.print(
                        f"  [green][OK][/green] Execution Engine verified. "
                        f"Queues -> Waiting: {state.waiting_count}, Ready: {state.ready_count}, Running: {state.running_count}. "
                        f"Available VRAM: {res.available_vram_gb:.1f}/{res.total_vram_gb:.1f} GB"
                    )
                except Exception as ex:
                    console.print(f"  [red][FAIL][/red] Execution Engine verification failed: {ex}")
                    raise

                # Check Memory Engine
                try:
                    memory_engine = kernel.get_service("memory_engine")
                    entry = await memory_engine.store_memory(
                        type="knowledge",
                        payload={"doctor_check": "ok"},
                        tags=["doctor_check"]
                    )
                    # Clean up diagnostic memory
                    memory_engine.store.delete_entry(entry.memory_id)
                    console.print(
                        f"  [green][OK][/green] Memory Engine verified. "
                        f"Store: {memory_engine.store.__class__.__name__}"
                    )
                except Exception as ex:
                    console.print(f"  [red][FAIL][/red] Memory Engine verification failed: {ex}")
                    raise

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
