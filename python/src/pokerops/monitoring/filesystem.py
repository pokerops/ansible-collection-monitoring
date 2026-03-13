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
    name: Optional[str] = typer.Option(None, help="Filename filter"), # pyright: ignore[reportCallInDefaultInitializer]
    mtime: Optional[str] = typer.Option(None, help="Modification time filter"), # pyright: ignore[reportCallInDefaultInitializer]
    ctime: Optional[str] = typer.Option(None, help="Change time filter"), # pyright: ignore[reportCallInDefaultInitializer]
    recursive: bool = typer.Option(True, help="Enable recursive search"), # pyright: ignore[reportCallInDefaultInitializer]
    log_id: str = typer.Option("filesystem-files", help="Log identifier"), # pyright: ignore[reportCallInDefaultInitializer]
    location: str = typer.Option("", help="Location identifier"), # pyright: ignore[reportCallInDefaultInitializer]
    environment: str = typer.Option("", help="Environment name"), # pyright: ignore[reportCallInDefaultInitializer]
    function: str = typer.Option("", help="Function identifier"), # pyright: ignore[reportCallInDefaultInitializer]
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


def argument(option: str, value: Optional[str]) -> str:
    if value:
        return f"{option} {value}"
    return ""


def find(path: Path, arguments: Optional[Iterable[str]] = None) -> Tuple[Optional[str], Optional[List[Path]]]:
    """Recursive filtered search for files in a directory

    Returns:
        Tuple of (error, result):
        - On success: (None, list of matching files)
        - On error: (error_message, None)
    """
    args = arguments or []
    find_args = " ".join(args)

    command = ["find", str(path)] + [arg for arg in find_args.split() if arg]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        files = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]

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
    args: List[str] = [
        argument("-maxdepth", "1" if not recursive else None),
        argument("-type", "f"),
        argument("-name", name),
        argument("-mtime", mtime),
        argument("-ctime", ctime),
    ]

    args = [a for a in args if a]

    error, file_list = find(
        path=Path(path).resolve(),
        arguments=args,
    )

    file_list = file_list or []

    files_info: List[dict] = []
    total_size = 0
    newest: Optional[float] = None
    oldest: Optional[float] = None

    for p in file_list:
        try:
            stat = p.stat()

            size = stat.st_size
            file_mtime = stat.st_mtime
            file_ctime = stat.st_ctime

            files_info.append(
                {
                    "path": str(p),
                    "name": p.name,
                    "size_bytes": size,
                    "mtime": file_mtime,
                    "ctime": file_ctime,
                }
            )

            total_size += size

            if newest is None or file_mtime > newest:
                newest = file_mtime

            if oldest is None or file_mtime < oldest:
                oldest = file_mtime

        except Exception:
            continue

    file_data = {
        "filesystem": {
            "path": path,
            "ctime": ctime,
            "mtime": mtime,
            "files": files_info,
            "count": len(files_info),
            "size_bytes": total_size,
            "newest_file_timestamp": newest or 0,
            "oldest_file_timestamp": oldest or 0,
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

    if error:
        stderr = Console(stderr=True)
        stderr.print(f"Unexpected error occurred while scanning path: {path}")
        raise typer.Exit(code=1)
