import datetime
import json
import platform

import typer

app = typer.Typer(help="Filesystem monitoring commands")


@app.command("files")
def filesystem_files_cmd(
    path: str = typer.Argument(help="Filesystem path to check"),
    log_id: str = typer.Option("filesystem-files", help="Log identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    location: str = typer.Option("", help="Location identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    environment: str = typer.Option("", help="Environment name"),  # pyright: ignore[reportCallInDefaultInitializer]
    function: str = typer.Option("", help="Function identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    debug: bool = typer.Option(False, help="Enable debug mode"),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    return files(path, location, environment, function, log_id, debug)


def files(
    path: str,
    location: str,
    environment: str,
    function: str,
    log_id: str = "ntp-drift",
    debug: bool = False,
):
    if debug:
        typer.echo(f"Checking filesystem at path: {path}")
