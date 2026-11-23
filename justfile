set allow-duplicate-variables := true
set allow-duplicate-recipes := true

import '.devbox/virtenv/pokerops.ansible-utils.molecule/justfile'

MOLECULE_SCENARIO := "legacy"
MOLECULE_LOCAL_KUBECONFIG := `pwd` + "/.kubeconfig"
MOLECULE_KVM_IMAGE := 'https://cloud-images.ubuntu.com/resolute/current/resolute-server-cloudimg-amd64.img'

RENOVATE_IMAGE := 'ghcr.io/renovatebot/renovate:44.257.9'

kubectl:
	@echo "Using kubeconfig: ${MOLECULE_LOCAL_KUBECONFIG}"
	@kubectl --kubeconfig=${MOLECULE_LOCAL_KUBECONFIG} $(filter-out $@,$(MAKECMDGOALS))

run *args:
  @uv --python-preference=only-managed run python -m pokerops.monitoring {{args}}

# Lint python with ruff, then yaml and ansible with the imported lint recipe, which the local recipe shadows
lint *args:
  @uv --python-preference=only-managed run ruff check {{args}} python/src python/tests bin
  @{{just_executable()}} --justfile "{{source_directory()}}/.devbox/virtenv/pokerops.ansible-utils.molecule/justfile" --working-directory "{{justfile_directory()}}" lint

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

# Run the check-* recipes named by the arguments, nox and version by default, e.g. check types build
check *targets:
  #!/usr/bin/env bash
  set -euo pipefail
  TARGETS=({{targets}})
  if [ "${#TARGETS[@]}" -eq 0 ]; then
    TARGETS=(nox version)
  fi
  exec {{just_executable()}} --justfile "{{justfile()}}" "${TARGETS[@]/#/check-}"

# Check python formatting, run 'just format' to apply it
check-format:
  @uv --python-preference=only-managed run ruff format --check python/src python/tests bin

# Apply python formatting
format *args:
  @uv --python-preference=only-managed run ruff format {{args}} python/src python/tests bin

check-pytest *args:
  @uv --python-preference=only-managed run pytest {{args}}

check-types:
  @uv --python-preference=only-managed run pyright

check-nox:
  @uv run nox -p

check-build:
  @uv --python-preference=only-managed build

# Unit test the Vector transforms, the templates are rendered with ansible and tested with the vector version in the role defaults
check-vector:
  #!/usr/bin/env bash
  set -euo pipefail
  VERSION=$(dasel -i yaml 'monitoring_vector_version' < roles/monitoring/defaults/main.yml | sed -e "s/^['\"]// ; s/['\"]$//")
  RENDERED=$(mktemp -d)
  trap 'rm -rf "${RENDERED}"' EXIT
  TEMPLATES=playbooks/vector/templates
  VARS=tests/vector/vars.yml
  render() {
    {{UV_RUN}} ansible localhost -m ansible.builtin.template -a "src=${PWD}/${TEMPLATES}/$1.yaml.j2 dest=${RENDERED}/$1.yaml" -e "@${VARS}" "${@:2}" > /dev/null
  }
  for BEAT in filebeat heartbeat metricbeat; do
    render "${BEAT}" -e "beat_name=${BEAT}" -e "beat_port=9200" -e "beat_elasticsearch_index=${BEAT}"
  done
  for NAME in alloy filesystem ntp rabbitmq; do
    render "${NAME}"
  done
  docker run --rm --network none \
    -v "${RENDERED}:/rendered:ro" -v "${PWD}/tests/vector:/tests:ro" \
    "timberio/vector:${VERSION}-debian" test "/rendered/*.yaml" "/tests/*.test.yaml"

# Check that the script repository defaults are the canonical repository and a release version
check-defaults:
  #!/usr/bin/env bash
  DEFAULTS=roles/monitoring/defaults/main.yml
  REPO_URL=$(dasel -i yaml 'monitoring_script_repo_url' < ${DEFAULTS} | sed -e "s/^['\"]// ; s/['\"]$//")
  REPO_VERSION=$(dasel -i yaml 'monitoring_script_repo_version' < ${DEFAULTS} | sed -e "s/^['\"]// ; s/['\"]$//")
  if [ "${REPO_URL}" != "https://github.com/pokerops/ansible-collection-monitoring.git" ]; then
    echo "Error: found default repository url '${REPO_URL}', expected the pokerops repository"
    exit 1
  fi
  if ! echo "${REPO_VERSION}" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Error: found default repository version '${REPO_VERSION}', expected a release (X.Y.Z)"
    exit 1
  fi
  echo "Defaults target release ${REPO_VERSION}"

check-version:
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
