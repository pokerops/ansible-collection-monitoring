import json
import re
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer
from pokerops.monitoring import tools

app = typer.Typer(help="Filesystem monitoring commands")


@app.command("files")
def filesystem_files_cmd(
    path: str = typer.Argument(help="Filesystem path to check"),
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
        mtime=mtime,
        ctime=ctime,
        recursive=recursive,
        location=location,
        environment=environment,
        function=function,
        log_id=log_id,
    )


def filter_time(t: datetime, filter: str) -> bool:
    """Parse time filter string into seconds threshold.

    Format: [+/-][number][unit]
    - Prefix: + for older than, - for newer than
    - Units: s(seconds), m(minutes), h(hours), d(days)

    Examples:
        "-7d" -> files modified in last 7 days
        "+1h" -> files modified more than 1 hour ago

    Returns:
        Threshold timestamp as float, or None if invalid format
    """
    match = re.match(r"^([+-])(\d+)([smhd])$", filter)

    if match:
        direction, amount, unit = match.groups()
        time = int(amount)

        # Convert to seconds
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        delta = timedelta(seconds=time * multipliers[unit])

        # Compare times
        now = datetime.now(UTC)
        if direction == "-":
            return t > now - delta  # Newer than
        else:
            return t < now - delta  # Older than
    return False


def filter_file_time(time_fn: Callable[[Path], datetime], time_filter: str | None) -> Callable[[Path], bool]:
    """Check if file time matches the filter criteria."""
    if time_filter:
        return lambda p: filter_time(time_fn(p), time_filter)
    else:
        return lambda _: True


def filter_mtime(time_filter: str | None) -> Callable[[Path], bool]:
    """Filter file by modification time."""
    return filter_file_time(
        lambda p: datetime.fromtimestamp(p.stat().st_mtime, tz=UTC),
        time_filter,
    )


def filter_ctime(time_filter: str | None) -> Callable[[Path], bool]:
    """Filter file by change time."""
    return filter_file_time(
        lambda p: datetime.fromtimestamp(p.stat().st_ctime, tz=UTC),
        time_filter,
    )


def search(
    path: Path,
    files: list[Path] | None = None,
    filters: Iterable[Callable[[Path], bool]] | None = None,
    recursive: bool = True,
    errors: list[dict[str, str]] | None = None,
) -> tuple[list[Path], list[dict[str, str]]]:
    """Recursive filtered search for files in a directory.

    Returns:
        Tuple of (matching files, errors encountered)
    """
    file_list = [] if files is None else files
    error_list = [] if errors is None else errors
    filter_list = list(filters) if filters else []
    if path.exists():
        try:
            for entry in path.iterdir():
                if entry.is_file():
                    if not filter_list or all(f(entry) for f in filter_list):
                        file_list.append(entry)
                elif entry.is_dir() and recursive:
                    search(entry, file_list, filter_list, recursive, error_list)
        except (OSError, PermissionError) as e:
            error_list.append(
                {
                    "path": str(path),
                    "error": type(e).__name__,
                    "message": str(e),
                }
            )
    return file_list, error_list


def files(
    path: str,
    location: str,
    environment: str,
    function: str,
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
        mtime: Modification time filter (e.g., "-7d", "+1h")
        ctime: Change time filter (e.g., "-7d", "+1h")
        recursive: Whether to scan recursively
        log_id: Log identifier
    """
    file_list, error_list = search(
        path=Path(path).resolve(),
        files=[],
        filters=(filter_mtime(mtime), filter_ctime(ctime)),
        recursive=recursive,
    )
    file_data = {
        "filesystem": {
            "path": path,
            "ctime": ctime or "",
            "mtime": mtime or "",
            "files": [str(p) for p in file_list],
            "count": len(file_list),
            "errors": error_list,
            "error_count": len(error_list),
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
