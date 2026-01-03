# pokerops.monitoring Python Package

A Python CLI tool for monitoring operations in the pokerops infrastructure.

## Overview

The `pokerops.monitoring` package provides a command-line interface for various monitoring tasks, including NTP drift checks and other infrastructure monitoring capabilities.

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/pokerops/ansible-collection-monitoring.git
cd ansible-collection-monitoring

# Install with uv
uv pip install -e .

# Or build and install the wheel
just build
pip install dist/pokerops_monitoring-*.whl
```

## Usage

The CLI is organized into command groups. Use `--help` to see available commands:

```bash
pokerops-monitoring --help
```

### NTP Drift Monitoring

Check NTP drift from a time server:

```bash
monitoring ntp drift --peer time.cloudflare.com
```

**Options:**

- `--peer`: NTP peer address (default: `time.cloudflare.com`)
- `--location`: Location identifier (optional)
- `--environment`: Environment name (optional)
- `--function`: Function identifier (optional)
- `--log-id`: Log identifier (default: `ntp-drift`)

**Output:**

The command outputs JSON with the following structure:

```json
{
  "@timestamp": "2024-01-01T00:00:00+00:00",
  "ntp_peer_address": "time.cloudflare.com",
  "ntp_peer_offset": 0.005,
  "host": {
    "name": "hostname"
  },
  "fields": {
    "location": "us-east",
    "environment": "production",
    "function": "monitoring",
    "log": {
      "description": "ntp-drift"
    }
  }
}
```

## Development

This project follows the hybrid CLI pattern documented in [CLAUDE.md](../CLAUDE.md).

### Project Structure

```
python/
├── README.md           # This file
├── src/
│   └── pokerops/
│       └── monitoring/  # PEP 420 namespace package
│           ├── __init__.py
│           ├── cli.py   # Main CLI application
│           └── ntp.py   # NTP monitoring commands
└── tests/
    ├── test_cli.py      # CLI tests
    └── test_ntp.py      # NTP functionality tests
```

### Development Setup

```bash
# Enter devbox shell
devbox shell

# Install dependencies
make install

# Run the CLI
just run --help

# Run tests
just test

# Build the package
just build
```

### Adding New Commands

Follow the hybrid pattern when adding new monitoring commands:

1. Create a new module (e.g., `src/pokerops/monitoring/newfeature.py`)
2. Create a Typer app for the command group
3. Implement thin CLI wrappers and pure business logic functions
4. Register the app in `cli.py`
5. Add tests in `tests/test_newfeature.py`

Example:

```python
# src/pokerops/monitoring/newfeature.py
import typer

app = typer.Typer(help="New feature commands")

@app.command("check")
def check_cmd(param: str = typer.Option(..., help="Parameter")):
    """CLI wrapper."""
    return check(param)

def check(param: str):
    """Pure business logic - no typer dependencies."""
    # Implementation here
    pass
```

Then in `cli.py`:

```python
from pokerops.monitoring.newfeature import app as newfeature_app

app.add_typer(newfeature_app, name="newfeature")
```

### Testing

Run the test suite:

```bash
# Run all tests
just test

# Run with verbose output
just test -v

# Run specific test
just test -k test_ntp_drift

# Run with coverage
just test --cov=pokerops.monitoring
```

### Building

Build the package:

```bash
just build
```

This creates:

- Source distribution: `dist/pokerops_monitoring-*.tar.gz`
- Wheel: `dist/pokerops_monitoring-*-py3-none-any.whl`

## Architecture

### Namespace Package (PEP 420)

This package uses PEP 420 namespace packages, allowing other packages to extend the `pokerops` namespace. The structure is:

- `python/src/pokerops/` - Namespace package (no `__init__.py`)
- `python/src/pokerops/monitoring/` - Actual package

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit).

## Author

Ted Cook <358176+teddyphreak@users.noreply.github.com>
