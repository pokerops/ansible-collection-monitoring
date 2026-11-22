"""Tests for the renovate log summary development tool."""

import json
from pathlib import Path
from typing import Any

import pytest

from renovate import main, select_update, summarize

PACKAGE_FILE = "roles/monitoring/defaults/main.yml"


def dep(name: str, current: str = "1.0.0", **extra: Any) -> dict[str, Any]:
    return {"depName": name, "currentValue": current, **extra}


def packages_entry(*deps: dict[str, Any]) -> dict[str, Any]:
    return {"level": 20, "msg": "packageFiles with updates", "config": {"regex": [{"packageFile": PACKAGE_FILE, "deps": list(deps)}]}}


def lookup_failure(package: str, reason: str = "no-result") -> dict[str, Any]:
    return {"level": 20, "msg": f"Failed to look up github-releases package {package}: {reason}"}


def datasource_error(package: str, message: str) -> dict[str, Any]:
    return {"level": 20, "msg": "Datasource unknown error", "packageName": package, "err": {"message": message}}


def write_log(path: Path, *entries: dict[str, Any], noise: bool = False) -> Path:
    lines = [json.dumps(entry) for entry in entries]
    if noise:
        lines.insert(0, "not json at all")
    path.write_text("\n".join(lines) + "\n")
    return path


class TestSummarize:
    def test_reports_available_update(self):
        summary = summarize([packages_entry(dep("a/b", updates=[{"newVersion": "1.1.0", "updateType": "minor"}]))])
        assert summary.lines == [f"{PACKAGE_FILE}: a/b 1.0.0 -> 1.1.0 (minor)"]
        assert summary.found and not summary.failed

    def test_joins_multiple_updates(self):
        updates = [{"newVersion": "1.1.0", "updateType": "minor"}, {"newValue": "2.0.0", "updateType": "major"}]
        assert summarize([packages_entry(dep("a/b", updates=updates))]).lines == [f"{PACKAGE_FILE}: a/b 1.0.0 -> 1.1.0 (minor) | 2.0.0 (major)"]

    def test_reports_up_to_date(self):
        summary = summarize([packages_entry(dep("a/b", updates=[]))])
        assert summary.lines == [f"{PACKAGE_FILE}: a/b 1.0.0 -> up to date"]
        assert not summary.failed

    def test_reports_skipped_dependency(self):
        summary = summarize([packages_entry(dep("a/b", skipReason="github-token-required"))])
        assert summary.lines == [f"{PACKAGE_FILE}: a/b 1.0.0 -> skipped (github-token-required)"]
        assert not summary.failed

    def test_failed_lookup_is_not_up_to_date(self):
        summary = summarize([lookup_failure("a/b"), packages_entry(dep("a/b", updates=[]))])
        assert summary.lines == [f"{PACKAGE_FILE}: a/b 1.0.0 -> lookup failed (no-result)"]
        assert summary.failed

    def test_failed_lookup_prefers_underlying_cause(self):
        entries = [lookup_failure("a/b"), datasource_error("a/b", "bad-credentials"), packages_entry(dep("a/b"))]
        assert summarize(entries).lines == [f"{PACKAGE_FILE}: a/b 1.0.0 -> lookup failed (bad-credentials)"]

    def test_failed_lookup_matches_package_name_over_dep_name(self):
        entries = [lookup_failure("a/b"), packages_entry(dep("alias", packageName="a/b"))]
        assert summarize(entries).failed

    def test_failure_of_one_dependency_leaves_others_intact(self):
        entries = [lookup_failure("a/b"), packages_entry(dep("a/b"), dep("c/d", updates=[]))]
        summary = summarize(entries)
        assert summary.lines == [f"{PACKAGE_FILE}: a/b 1.0.0 -> lookup failed (no-result)", f"{PACKAGE_FILE}: c/d 1.0.0 -> up to date"]
        assert summary.failed

    def test_error_entries_are_reported(self):
        summary = summarize([{"level": 50, "msg": "Unsupported node environment detected."}, packages_entry(dep("a/b"))])
        assert summary.lines[0] == "error: Unsupported node environment detected."

    def test_nothing_found(self):
        summary = summarize([{"level": 20, "msg": "unrelated"}])
        assert summary.lines == [] and not summary.found


class TestMain:
    def test_success(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        log = write_log(tmp_path / "log", packages_entry(dep("a/b", updates=[])), noise=True)
        assert main([str(log)]) == 0
        assert capsys.readouterr().out == f"{PACKAGE_FILE}: a/b 1.0.0 -> up to date\n"

    def test_update_available_is_not_a_failure(self, tmp_path: Path):
        log = write_log(tmp_path / "log", packages_entry(dep("a/b", updates=[{"newVersion": "2.0.0", "updateType": "major"}])))
        assert main([str(log)]) == 0

    def test_failed_lookup_fails(self, tmp_path: Path):
        assert main([str(write_log(tmp_path / "log", lookup_failure("a/b"), packages_entry(dep("a/b"))))]) == 1

    def test_no_dependencies_fails(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        assert main([str(write_log(tmp_path / "log", {"level": 20, "msg": "unrelated"}))]) == 1
        assert "no managed dependencies found" in capsys.readouterr().out


YAML_PIN = '# renovate: datasource=github-releases depName=a/b extractVersion=^v(?<version>.+)$\nmonitoring_a_version: "1.0.0"'
IMAGE_PIN = "RENOVATE_IMAGE := 'ghcr.io/renovatebot/renovate:44.200.0'"


def update_dep(name: str, current: str, replace_string: str, *updates: tuple[str, str]) -> dict[str, Any]:
    candidates = [{"newVersion": new, "newValue": new, "updateType": kind, "bucket": "major" if kind == "major" else "non-major"} for new, kind in updates]
    return dep(name, current, replaceString=replace_string, updates=candidates)


def run_apply(root: Path, *deps: dict[str, Any], flags: tuple[str, ...] = ()) -> int:
    return main([str(write_log(root / "log", packages_entry(*deps))), "--root", str(root), *flags])


class TestSelectUpdate:
    def test_picks_newest_non_major(self):
        updates = [{"newValue": "1.1.0", "updateType": "minor"}, {"newValue": "1.2.0", "updateType": "minor"}, {"newValue": "2.0.0", "updateType": "major"}]
        assert select_update(updates, major=False) == updates[1]

    def test_picks_newest_when_majors_allowed(self):
        updates = [{"newValue": "1.2.0", "updateType": "minor"}, {"newValue": "2.0.0", "updateType": "major"}]
        assert select_update(updates, major=True) == updates[1]

    def test_orders_versions_numerically(self):
        updates = [{"newValue": "1.9.0", "updateType": "minor"}, {"newValue": "1.10.0", "updateType": "minor"}]
        assert select_update(updates, major=False) == updates[1]

    def test_only_major_is_held_back(self):
        assert select_update([{"newValue": "2.0.0", "updateType": "major"}], major=False) is None

    def test_bucket_marks_major(self):
        assert select_update([{"newValue": "2.0.0", "updateType": "digest", "bucket": "major"}], major=False) is None

    def test_no_updates(self):
        assert select_update([], major=False) is None


class TestApply:
    def test_rewrites_version_in_yaml(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(f"before: 1\n{YAML_PIN}\nafter: 2\n")
        assert run_apply(tmp_path, update_dep("a/b", "1.0.0", YAML_PIN, ("1.1.0", "minor"))) == 0
        assert (tmp_path / PACKAGE_FILE).read_text() == f"before: 1\n{YAML_PIN.replace('1.0.0', '1.1.0')}\nafter: 2\n"
        assert f"applied a/b 1.0.0 -> 1.1.0 in {PACKAGE_FILE}" in capsys.readouterr().out

    def test_rewrites_image_tag(self, tmp_path: Path):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(f"{IMAGE_PIN}\n")
        assert run_apply(tmp_path, update_dep("img", "44.200.0", IMAGE_PIN, ("44.257.9", "minor"))) == 0
        assert (tmp_path / PACKAGE_FILE).read_text() == "RENOVATE_IMAGE := 'ghcr.io/renovatebot/renovate:44.257.9'\n"

    def test_replaces_the_value_not_a_match_in_the_name(self, tmp_path: Path):
        pin = "IMG_IMAGE := 'repo/1.0.0:1.0.0'"
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(pin)
        assert run_apply(tmp_path, update_dep("repo/1.0.0", "1.0.0", pin, ("1.1.0", "minor"))) == 0
        assert (tmp_path / PACKAGE_FILE).read_text() == "IMG_IMAGE := 'repo/1.0.0:1.1.0'"

    def test_dry_run_writes_nothing(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(YAML_PIN)
        assert run_apply(tmp_path, update_dep("a/b", "1.0.0", YAML_PIN, ("1.1.0", "minor")), flags=("--dry-run",)) == 0
        assert (tmp_path / PACKAGE_FILE).read_text() == YAML_PIN
        assert "dry run, 1 update(s) would be applied" in capsys.readouterr().out

    def test_major_is_held_back(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(YAML_PIN)
        assert run_apply(tmp_path, update_dep("a/b", "1.0.0", YAML_PIN, ("2.0.0", "major"))) == 0
        assert (tmp_path / PACKAGE_FILE).read_text() == YAML_PIN
        assert "1 major update(s) not applied" in capsys.readouterr().out

    def test_major_is_applied_when_asked(self, tmp_path: Path):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(YAML_PIN)
        assert run_apply(tmp_path, update_dep("a/b", "1.0.0", YAML_PIN, ("2.0.0", "major")), flags=("--major",)) == 0
        assert '"2.0.0"' in (tmp_path / PACKAGE_FILE).read_text()

    def test_ambiguous_match_is_not_applied(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(f"{YAML_PIN}\n{YAML_PIN}\n")
        assert run_apply(tmp_path, update_dep("a/b", "1.0.0", YAML_PIN, ("1.1.0", "minor"))) == 1
        assert (tmp_path / PACKAGE_FILE).read_text() == f"{YAML_PIN}\n{YAML_PIN}\n"
        assert "expected exactly one match" in capsys.readouterr().out

    def test_changed_file_is_not_applied(self, tmp_path: Path):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text("something else\n")
        assert run_apply(tmp_path, update_dep("a/b", "1.0.0", YAML_PIN, ("1.1.0", "minor"))) == 1

    def test_missing_file_is_not_applied(self, tmp_path: Path):
        assert run_apply(tmp_path, update_dep("a/b", "1.0.0", YAML_PIN, ("1.1.0", "minor"))) == 1

    def test_nothing_is_applied_when_a_lookup_failed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(f"{YAML_PIN}\n")
        good, bad = update_dep("a/b", "1.0.0", YAML_PIN, ("1.1.0", "minor")), dep("c/d")
        log = write_log(tmp_path / "log", lookup_failure("c/d"), packages_entry(good, bad))
        assert main([str(log), "--root", str(tmp_path)]) == 1
        assert (tmp_path / PACKAGE_FILE).read_text() == f"{YAML_PIN}\n"
        assert "not applying updates" in capsys.readouterr().out

    def test_skipped_dependency_is_not_applied(self, tmp_path: Path):
        (tmp_path / PACKAGE_FILE).parent.mkdir(parents=True)
        (tmp_path / PACKAGE_FILE).write_text(YAML_PIN)
        skipped = update_dep("a/b", "1.0.0", YAML_PIN, ("1.1.0", "minor"))
        skipped["skipReason"] = "github-token-required"
        assert run_apply(tmp_path, skipped) == 0
        assert (tmp_path / PACKAGE_FILE).read_text() == YAML_PIN
