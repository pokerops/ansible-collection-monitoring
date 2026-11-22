set allow-duplicate-variables := true
set allow-duplicate-recipes := true

import '.devbox/virtenv/pokerops.ansible-utils.molecule/justfile'

MOLECULE_SCENARIO := "legacy"
MOLECULE_LOCAL_KUBECONFIG := `pwd` + "/.kubeconfig"
MOLECULE_KVM_IMAGE := 'https://cloud-images.ubuntu.com/resolute/current/resolute-server-cloudimg-amd64.img'

GIT_REPO := `git config --get remote.origin.url | sed -E 's#https://github.com/##; s#^git@github.com:##; s#\.git$$##'`
GIT_BRANCH := `git rev-parse --abbrev-ref HEAD`

RENOVATE_IMAGE := 'ghcr.io/renovatebot/renovate:44.257.9'

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
  @uv --python-preference=only-managed run python -m pokerops.monitoring {{args}}

# Run all pytest checks
pytest *args:
  @uv --python-preference=only-managed run pytest {{args}}

# Lint code with ruff
lint *args:
  @uv --python-preference=only-managed run ruff check {{args}} python/src python/tests bin

# Format code with ruff
format *args:
  @uv --python-preference=only-managed run ruff format {{args}} python/src python/tests bin

# Type check with pyright
types *args:
  @uv --python-preference=only-managed run pyright {{args}}

# Run nox (all sessions) - uv manages Python versions
nox *args='-p':
  @uv run nox {{args}}

# Build the package
pybuild:
  @uv --python-preference=only-managed build

# Check default values
defaults:
  #!/usr/bin/env bash
  REPO_VERSION=$(dasel -f roles/monitoring/defaults/main.yml .monitoring_script_repo_version);
  if [ "${REPO_VERSION}" != "master" ]; then
    echo "Error: found default package version '${REPO_VERSION}', expected 'master'";
    exit 1;
  fi

# Run the checks that need no libvirt: python tests, lint, format and types on every python version, and version consistency
check: nox pyversion

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

alias update := renovate

# Apply component version updates found by renovate, --dry-run only reports them and --major includes major updates
renovate *args:
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "warning: GITHUB_TOKEN is not set, release lookups will be skipped" >&2
  fi
  # renovate reads its github.com lookup credential from GITHUB_COM_TOKEN, passed by name so it stays out of the process list
  export GITHUB_COM_TOKEN="${GITHUB_TOKEN:-}"
  # Renovate local mode only sees files known to git, so an untracked config is silently ignored
  if ! git ls-files --error-unmatch renovate.json > /dev/null 2>&1; then
    echo "error: renovate.json is not tracked by git, run 'git add -N renovate.json'" >&2
    exit 1
  fi
  RENOVATE=(docker run --rm --network host -v "${PWD}:/repo:ro" -w /repo -e GITHUB_COM_TOKEN {{RENOVATE_IMAGE}})
  echo "Validating renovate configuration"
  "${RENOVATE[@]}" renovate-config-validator --strict renovate.json
  LOG=$(mktemp)
  STATUS=0
  "${RENOVATE[@]}" env LOG_LEVEL=debug LOG_FORMAT=json renovate --platform=local > "${LOG}" 2>&1 || STATUS=$?
  SUMMARY=0
  uv --python-preference=only-managed run --no-project python bin/renovate.py "${LOG}" {{args}} || SUMMARY=$?
  if [ "${STATUS}" -ne 0 ] || [ "${SUMMARY}" -ne 0 ]; then
    echo "renovate did not complete cleanly (renovate status ${STATUS}, summary status ${SUMMARY}), full log at ${LOG}" >&2
    exit 1
  fi
  rm -f "${LOG}"
