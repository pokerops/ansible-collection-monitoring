import json
import subprocess
from collections.abc import Iterable
from pathlib import Path

import typer
from rich.console import Console

from pokerops.monitoring import tools

app = typer.Typer(help="Filesystem monitoring commands")


@app.command("files")
def filesystem_files_cmd(
    path: str = typer.Argument(help="Filesystem path to check"),
    name: str | None = typer.Option(None, help="Filename filter"),  # pyright: ignore[reportCallInDefaultInitializer]
    mtime: str | None = typer.Option(None, help="Modification time filter"),  # pyright: ignore[reportCallInDefaultInitializer
    ctime: str | None = typer.Option(None, help="Change time filter"),  # pyright: ignore[reportCallInDefaultInitializer]
    recursive: bool = typer.Option(True, help="Enable recursive search"),  # pyright: ignore[reportCallInDefaultInitializer]
    log_id: str = typer.Option("filesystem-files", help="Log identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    location: str = typer.Option("", help="Location identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    environment: str = typer.Option("", help="Environment name"),  # pyright: ignore[reportCallInDefaultInitializer]
    function: str = typer.Option("", help="Function identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    return files(
        path=path,
        name=name,
        mtime=mtime,
        ctime=ctime,
        recursive=recursive,
        location=location,
        environment=environment,
        function=function,
        log_id=log_id,
    )


def argument(option: str, value: str | None) -> str:
    return (value and f"{option} {value}") or ""


def find(path: Path, arguments: Iterable[str] | None = None) -> tuple[str | None, list[Path] | None]:
    """Recursive filtered search for files in a directory

    Returns:
        Tuple of (error, result):
        - On success: (None, list of matching files)
        - On error: (error_message, None)
    """
    args = arguments or []
    find_args = " ".join(args)

    # Build the find command
    command = ["find", str(path)] + [arg for arg in find_args.split() if arg]

    try:
        # Execute find command
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Parse output into list of Path objects
        files = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]

        return (None, files)

    except subprocess.CalledProcessError as e:
        # Return error message as Left
        error_msg = f"find command failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f": {e.stderr.strip()}"
        return (error_msg, None)

    except Exception as e:
        # Catch any other exceptions (e.g., file not found)
        return (f"Error executing find: {str(e)}", None)


def files(
    path: str,
    location: str,
    environment: str,
    function: str,
    name: str | None = None,
    mtime: str | None = None,
    ctime: str | None = None,
    recursive: bool = True,
    log_id: str = "filesystem-files",
) -> None:
    """Scan filesystem path and report files matching criteria.

    Args:
        path: Directory path to scan
        location: Location identifier
        environment: Environment name
        function: Function identifier
        name: Filename filter (e.g., "*.txt", "file.log")
        mtime: Modification time filter in days (e.g., "-7" for within 7 days, "+1" for older than 1 day)
        ctime: Change time filter in days (e.g., "-7" for within 7 days, "+1" for older than 1 day)
        recursive: Whether to scan recursively
        log_id: Log identifier
    """
    error, file_list = find(
        path=Path(path).resolve(),
        arguments=(
            argument("-maxdepth", "1" if not recursive else None),
            argument("-type", "f"),
            argument("-name", name),
            argument("-mtime", mtime),
            argument("-ctime", ctime),
        ),
    )

    if file_list is not None:
        file_data = {
            "filesystem": {
                "path": path,
                "ctime": ctime,
                "mtime": mtime,
                "files": [str(p) for p in file_list],
                "count": len(file_list),
                "error": error,
            }
        }
        data = {
            **file_data,
            **tools.metadata(
                location=location,
                environment=environment,
                function=function,
                log_id=log_id,
            ),
        }
        print(json.dumps(data))
        return

    # Handle error case
    error_data = {
        "filesystem": {
            "path": path,
            "ctime": ctime,
            "mtime": mtime,
            "files": [str(p) for p in (file_list or [])],
            "error": error,
        }
    }
    data = {
        **error_data,
        **tools.metadata(
            location=location,
            environment=environment,
            function=function,
            log_id=log_id,
        ),
    }
    print(json.dumps(data))
    stderr = Console(stderr=True)
    stderr.print(f"Unexpected error occurred while scanning path: {path}")
    raise typer.Exit(code=1)
