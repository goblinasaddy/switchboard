import typer

# Initialize Typer App
app = typer.Typer(
    name="switchboard",
    help="SwitchBoard: A local-first AI Runtime Platform orchestrating local AI workloads.",
    no_args_is_help=True
)

# Lazy import of command implementations to avoid loading weight when running help
def register_commands() -> None:
    from switchboard.cli.commands.run import run_command
    from switchboard.cli.commands.doctor import doctor_command
    from switchboard.cli.commands.version import version_command
    
    app.command(name="run", help="Bootstrap and execute the SwitchBoard platform kernel.")(run_command)
    app.command(name="doctor", help="Check local environment compatibility and service connections.")(doctor_command)
    app.command(name="version", help="Output platform version information.")(version_command)

register_commands()

if __name__ == "__main__":
    app()
