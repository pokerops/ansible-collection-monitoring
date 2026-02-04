install:
  @make install

configure:
  @make configure

requirements:
  @make requirements 

run *args:
  @uv --no-managed-python run python -m pokerops.monitoring {{args}}

# Run all pytest checks
test *args:
  @uv --no-managed-python run pytest {{args}}

# Lint code with ruff
lint *args:
  @uv --no-managed-python run ruff check {{args}} python/src python/tests

# Format code with ruff
format *args:
  @uv --no-managed-python run ruff format {{args}} python/src python/tests

# Type check with pyright
pyright *args:
  @uv --no-managed-python run pyright {{args}}

# Run nox (all sessions) - uv manages Python versions
nox *args='-p':
  @uv run nox {{args}}

# List nox sessions
nox-list:
  @uv run nox --list

# Run nox test session (default: all tests in parallel)
nox-test session='tests -p':
  @uv run nox -s {{session}}

# Build the package
build:
  @uv --no-managed-python build

# Check default values
defaults:
  #!/usr/bin/env bash
  REPO_VERSION=$(dasel -f roles/monitoring/defaults/main.yml .monitoring_script_repo_version);
  if [ "${REPO_VERSION}" != "master" ]; then
    echo "Error: found default package version '${REPO_VERSION}', expected 'master'";
    exit 1;
  fi

version:
  #!/usr/bin/env bash
  ANSIBLE_VERSION=$(dasel -r yaml -f galaxy.yml .version | sed -e "s/^['\"]// ; s/['\"]$//")
  PYTHON_VERSION=$(dasel -r toml -f pyproject.toml .project.version | sed -e "s/^['\"]// ; s/['\"]$//")
  REPO_VERSION=$(dasel -f roles/monitoring/defaults/main.yml .monitoring_script_repo_version | sed -e "s/^['\"]// ; s/['\"]$//")
  if [ "${ANSIBLE_VERSION}" != "${PYTHON_VERSION}" ]; then
    echo "Python version '${PYTHON_VERSION}' and Ansible version '${ANSIBLE_VERSION}' do not match"
    EXIT=1
  fi
  if [ "${PYTHON_VERSION}" != "${REPO_VERSION}" ]; then
    echo "Module target version '${REPO_VERSION}' and Python version '${PYTHON_VERSION}' do not match"
    EXIT=1
  fi
  echo "All versions match release ${PYTHON_VERSION}"
