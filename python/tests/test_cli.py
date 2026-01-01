"""Tests for CLI entrypoint."""

from pokerops.monitoring.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_help():
    """Test that CLI help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Monitoring scripts for pokerops" in result.stdout
    assert "ntp" in result.stdout


def test_cli_no_command_shows_help():
    """Test that running CLI without command shows help."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Monitoring scripts for pokerops" in result.stdout
    assert "Commands" in result.stdout


def test_ntp_command_exists():
    """Test that ntp command is registered."""
    result = runner.invoke(app, ["ntp", "--help"])
    assert result.exit_code == 0
    assert "NTP monitoring commands" in result.stdout
    assert "drift" in result.stdout
