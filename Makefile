export 

MOLECULE_SCENARIO ?= legacy
MOLECULE_LOCAL_KUBECONFIG ?= $$(pwd)/.kubeconfig
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)

include ${MAKEFILE}

configure:
	@sed -iE \
		"s#\(monitoring_script_repo_version:\).*#\1 \"${GIT_BRANCH}\"#" \
		roles/monitoring/defaults/main.yml

kubectl:
	@echo "Using kubeconfig: ${MOLECULE_LOCAL_KUBECONFIG}"
	@kubectl --kubeconfig=${MOLECULE_LOCAL_KUBECONFIG} $(filter-out $@,$(MAKECMDGOALS))
