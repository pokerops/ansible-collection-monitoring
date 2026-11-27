"""Summarize a renovate debug log as one line per managed dependency, and apply the updates it found.

Development tool for the renovate justfile recipe, it is not part of the package installed on servers.
Renovate's local platform only reports updates, so they are applied here by replacing the text renovate matched.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOOKUP_FAILURE = re.compile(r"Failed to look up \S+ package (\S+): (.+)")


@dataclass
class Update:
    """A version change to write to a file."""

    path: str
    name: str
    replace_string: str
    current: str
    new: str


@dataclass
class Summary:
    """Result of summarizing a renovate log."""

    lines: list[str] = field(default_factory=list)
    updates: list[Update] = field(default_factory=list)
    held: int = 0
    found: bool = False
    failed: bool = False


def read_entries(path: Path) -> list[dict[str, Any]]:
    """Read renovate JSON log entries, ignoring lines that are not JSON."""
    entries: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        try:
            entries.append(json.loads(line))
        except ValueError:
            continue
    return entries


def lookup_failures(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Map package names to why their lookup failed, preferring the underlying datasource error.

    A failed lookup leaves a dependency without updates, which must not read as up to date.
    """
    failures: dict[str, str] = {}
    causes: dict[str, str] = {}
    for entry in entries:
        match = LOOKUP_FAILURE.match(entry.get("msg", ""))
        if match:
            failures[match.group(1)] = match.group(2)
        if entry.get("msg") == "Datasource unknown error":
            package, message = entry.get("packageName"), (entry.get("err") or {}).get("message")
            if package and message:
                causes[package] = message
    return {**failures, **causes}


def is_major(update: dict[str, Any]) -> bool:
    """Whether a renovate update is a major version change."""
    return update.get("updateType") == "major" or update.get("bucket") == "major"


def version_key(update: dict[str, Any]) -> tuple[int, ...]:
    """Order updates by the numbers in their version."""
    return tuple(int(number) for number in re.findall(r"\d+", str(update.get("newVersion", update.get("newValue", "")))))


def select_update(updates: list[dict[str, Any]], major: bool) -> dict[str, Any] | None:
    """Pick the newest update to apply, leaving out major updates unless asked for."""
    candidates = [update for update in updates if update.get("newValue") and (major or not is_major(update))]
    return max(candidates, key=version_key) if candidates else None


def dependency_state(dep: dict[str, Any], failures: dict[str, str]) -> tuple[str, bool]:
    """Describe a dependency as a state string, and whether its lookup failed."""
    if dep.get("skipReason"):
        return f"skipped ({dep['skipReason']})", False
    package = dep.get("packageName") or dep.get("depName")
    failure = failures.get(package) if package else None
    if failure:
        return f"lookup failed ({failure})", True
    updates = dep.get("updates") or []
    if updates:
        return " | ".join(f"{update.get('newVersion', update.get('newValue'))} ({update.get('updateType')})" for update in updates), False
    return "up to date", False


def summarize(entries: list[dict[str, Any]], major: bool = False) -> Summary:
    """Summarize renovate log entries, one line per managed dependency, and collect the updates to apply."""
    summary = Summary()
    failures = lookup_failures(entries)
    for entry in entries:
        if entry.get("level", 0) >= 50:
            summary.lines.append(f"error: {entry.get('msg', '')}")
        if entry.get("msg") != "packageFiles with updates":
            continue
        for files in entry.get("config", {}).values():
            for file in files:
                for dep in file.get("deps", []):
                    summary.found = True
                    state, failed = dependency_state(dep, failures)
                    summary.failed = summary.failed or failed
                    summary.lines.append(f"{file['packageFile']}: {dep.get('depName')} {dep.get('currentValue')} -> {state}")
                    update = None if dep.get("skipReason") else select_update(dep.get("updates") or [], major)
                    summary.held += 1 if not update and any(is_major(candidate) for candidate in dep.get("updates") or []) else 0
                    if update and dep.get("replaceString") and dep.get("currentValue") and not failed:
                        summary.updates.append(
                            Update(file["packageFile"], dep.get("depName", ""), dep["replaceString"], dep["currentValue"], update["newValue"])
                        )
    return summary


def apply_updates(updates: list[Update], root: Path) -> tuple[list[str], bool]:
    """Write updates under root, returning a message per update and whether any could not be applied."""
    messages: list[str] = []
    failed = False
    for update in updates:
        path = root / update.path
        text = path.read_text() if path.is_file() else ""
        head, found, tail = update.replace_string.rpartition(update.current)
        if text.count(update.replace_string) != 1 or not found:
            messages.append(f"cannot apply {update.name} to {update.path}: expected exactly one match of the text renovate found")
            failed = True
            continue
        path.write_text(text.replace(update.replace_string, f"{head}{update.new}{tail}"))
        messages.append(f"applied {update.name} {update.current} -> {update.new} in {update.path}")
    return messages, failed


def main(argv: list[str] | None = None) -> int:
    """Print the summary of a renovate log and apply its updates, failing when nothing was found or a lookup failed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="renovate log, as written with LOG_FORMAT=json")
    parser.add_argument("--root", type=Path, default=Path("."), help="directory the reported files are relative to")
    parser.add_argument("--dry-run", action="store_true", help="only report updates, do not write them")
    parser.add_argument("--major", action="store_true", help="apply major updates too, which are otherwise left for review")
    args = parser.parse_args(argv)
    summary = summarize(read_entries(args.log), major=args.major)
    for line in summary.lines:
        print(line)
    if not summary.found:
        print("no managed dependencies found, check the renovate annotations and managerFilePatterns")
        return 1
    if summary.failed:
        print("not applying updates, some lookups failed")
        return 1
    if summary.held:
        print(f"{summary.held} major update(s) not applied, review them and pass --major to apply")
    if args.dry_run:
        print(f"dry run, {len(summary.updates)} update(s) would be applied")
        return 0
    messages, failed = apply_updates(summary.updates, args.root)
    for message in messages:
        print(message)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
