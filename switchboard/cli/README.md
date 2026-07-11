# cli Subsystem

## Purpose
The `cli` subsystem provides the command-line interface entry points for SwitchBoard developers and orchestrators, allowing them to bootstrap the platform, run diagnostic tests, check versions, and execute workflows.

## Responsibilities
- Modularize subcommands (run, doctor, version) using the `Typer` library.
- Configure CLI arguments, options, overrides, and environment triggers.

## Public APIs
- `app`: The main Typer command group.

## Future Work
- Add custom interactive shell mode.
- Support runtime management commands (e.g. `switchboard model pull <name>`, `switchboard plugin install <name>`).
