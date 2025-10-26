export 

MOLECULE_SCENARIO ?= legacy
MOLECULE_LOCAL_KUBECONFIG ?= $$(pwd)/.kubeconfig

include ${MAKEFILE}

kubectl:
	@echo "Using kubeconfig: ${MOLECULE_LOCAL_KUBECONFIG}"
	@kubectl --kubeconfig=${MOLECULE_LOCAL_KUBECONFIG} $(filter-out $@,$(MAKECMDGOALS))
