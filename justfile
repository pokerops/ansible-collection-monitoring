set allow-duplicate-variables := true
set allow-duplicate-recipes := true
import '.devbox/virtenv/pokerops.ansible-utils.molecule/justfile'

MOLECULE_SCENARIO := "legacy"
MOLECULE_LOCAL_KUBECONFIG := `pwd` + "/.kubeconfig"

GIT_REPO := `git config --get remote.origin.url | sed -E 's#https://github.com/##; s#^git@github.com:##; s#\.git$$##'`
GIT_BRANCH := `git rev-parse --abbrev-ref HEAD`

configure:
	@sed -i -e \
		"s#\(monitoring_script_repo_url:\).*#\1 \"https://github.com/${GIT_REPO}.git\"#" \
		roles/monitoring/defaults/main.yml
	@sed -i -e \
		"s#\(monitoring_script_repo_version:\).*#\1 \"${GIT_BRANCH}\"#" \
		roles/monitoring/defaults/main.yml

kubectl:
	@echo "Using kubeconfig: ${MOLECULE_LOCAL_KUBECONFIG}"
	@kubectl --kubeconfig=${MOLECULE_LOCAL_KUBECONFIG} $(filter-out $@,$(MAKECMDGOALS))

pyrun *args:
  @uv --no-managed-python run python -m pokerops.monitoring {{args}}

# Run all pytest checks
pytest *args:
  @uv --no-managed-python run pytest {{args}}

# Lint code with ruff
lint *args:
  @uv --no-managed-python run ruff check {{args}} python/src python/tests

# Format code with ruff
format *args:
  @uv --no-managed-python run ruff format {{args}} python/src python/tests

# Type check with pyright
types *args:
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

pyversion:
  #!/usr/bin/env bash
  ANSIBLE_VERSION=$(dasel -i yaml 'get("version")' < galaxy.yml | sed -e "s/^['\"]// ; s/['\"]$//")
  PYTHON_VERSION=$(dasel -i toml 'project.version' < pyproject.toml | sed -e "s/^['\"]// ; s/['\"]$//")
  REPO_VERSION=$(dasel -i yaml 'monitoring_script_repo_version' < roles/monitoring/defaults/main.yml  | sed -e "s/^['\"]// ; s/['\"]$//")
  if [ "${ANSIBLE_VERSION}" != "${PYTHON_VERSION}" ]; then
    echo "Python version '${PYTHON_VERSION}' and Ansible version '${ANSIBLE_VERSION}' do not match"
    exit 1
  fi
  if [ "${PYTHON_VERSION}" != "${REPO_VERSION}" ]; then
    echo "Module target version '${REPO_VERSION}' and Python version '${PYTHON_VERSION}' do not match"
    exit 1
  fi
  echo "All versions match release ${PYTHON_VERSION}"
