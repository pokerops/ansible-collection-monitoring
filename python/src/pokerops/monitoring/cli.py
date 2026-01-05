"""CLI implementation for pokerops-monitoring."""

import typer
from pokerops.monitoring.filesystem import app as filesystem_app
from pokerops.monitoring.ntp import app as ntp_app
from rich.console import Console

app = typer.Typer(
    name="pokerops-monitoring",
    help="Monitoring scripts for pokerops",
    add_completion=False,
)
console = Console()

# NTP command group
app.add_typer(ntp_app, name="ntp")
app.add_typer(filesystem_app, name="filesystem")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Main callback for pokerops-monitoring."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
