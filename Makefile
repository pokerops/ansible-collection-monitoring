export 

MOLECULE_SCENARIO ?= legacy
MOLECULE_LOCAL_KUBECONFIG ?= $$(pwd)/.kubeconfig

GIT_REPO ?= $(shell git config --get remote.origin.url | sed -E 's#https://github.com/##; s#^git@github.com:##; s#\.git$$##')
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)

include ${MAKEFILE}

configure:
	@sed -iE \
		"s#\(monitoring_script_repo_url:\).*#\1 \"https://github.com/${GIT_REPO}.git\"#" \
		roles/monitoring/defaults/main.yml
	@sed -iE \
		"s#\(monitoring_script_repo_version:\).*#\1 \"${GIT_BRANCH}\"#" \
		roles/monitoring/defaults/main.yml

kubectl:
	@echo "Using kubeconfig: ${MOLECULE_LOCAL_KUBECONFIG}"
	@kubectl --kubeconfig=${MOLECULE_LOCAL_KUBECONFIG} $(filter-out $@,$(MAKECMDGOALS))
