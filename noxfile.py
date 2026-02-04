"""Nox configuration for multi-version Python testing."""

import nox

# Python versions to test
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]

# Use uv for faster environment creation
nox.options.default_venv_backend = "uv"


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run tests with pytest across multiple Python versions."""
    # Install the package and test dependencies
    session.install(".")
    session.install("pytest>=8.0.0", "pytest-mock>=3.12.0")

    # Run pytest with any additional arguments
    session.run("pytest", *session.posargs)


@nox.session(python="3.12")
def lint(session):
    """Run linting (only on Python 3.12)."""
    session.install(".")
    session.install("ruff>=0.8.0")
    session.run("ruff", "check", "python/src", "python/tests")


@nox.session(python="3.12")
def format_check(session):
    """Check code formatting (only on Python 3.12)."""
    session.install(".")
    session.install("ruff>=0.8.0")
    session.run("ruff", "format", "--check", "python/src", "python/tests")


@nox.session(python="3.12")
def types(session):
    """Run type checking (only on Python 3.12)."""
    session.install(".")
    session.install("pyright>=1.1.390")
    session.run("pyright")
