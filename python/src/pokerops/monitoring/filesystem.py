import json
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import typer
from pokerops.monitoring import tools
from rich.console import Console

app = typer.Typer(help="Filesystem monitoring commands")


@app.command("files")
def filesystem_files_cmd(
    path: str = typer.Argument(help="Filesystem path to check"),
    name: Optional[str] = typer.Option(None, help="Filename filter"),  # pyright: ignore[reportCallInDefaultInitializer]
    mtime: Optional[str] = typer.Option(None, help="Modification time filter"),  # pyright: ignore[reportCallInDefaultInitializer]
    ctime: Optional[str] = typer.Option(None, help="Change time filter"),  # pyright: ignore[reportCallInDefaultInitializer]
    min_size: Optional[str] = typer.Option(None, help="Minimum file size in bytes"),
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
        min_size=min_size,
        recursive=recursive,
        location=location,
        environment=environment,
        function=function,
        log_id=log_id,
    )


def argument(option: str, value: Optional[str]) -> str:
    return (value and f"{option} {value}") or ""


def find(
    path: Path,
    arguments: Optional[Iterable[str]] = None
) -> Tuple[Optional[str], Optional[List[Tuple[Path, int]]]]:
    """Recursive filtered search returning (path, size)"""

    args = arguments or []
    find_args = " ".join(args)

    command = (
        ["find", str(path)]
        + [arg for arg in find_args.split() if arg]
        + ["-exec", "stat", "-c", "%n|%s", "{}", ";"]
    )

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        files: List[Tuple[Path, int]] = []

        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            p, size = line.split("|", 1)
            files.append((Path(p), int(size)))

        return (None, files)

    except subprocess.CalledProcessError as e:
        error_msg = f"find command failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f": {e.stderr.strip()}"
        return (error_msg, None)

    except Exception as e:
        return (f"Error executing find: {str(e)}", None)


def files(
    path: str,
    location: str,
    environment: str,
    function: str,
    name: Optional[str] = None,
    mtime: Optional[str] = None,
    ctime: Optional[str] = None,
    min_size: Optional[str] = None,
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
            argument("-size", f"+{min_size}c" if min_size else None),
        ),
    )

    if file_list is not None:
        file_data = {
            "filesystem": {
                "path": path,
                "ctime": ctime,
                "mtime": mtime,
                "files": [
                    {"path": str(p), "size": size}
                    for p, size in file_list
                ],
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
