# author: Pedro Crespo
.DEFAULT_GOAL := help

export VCS_URL:=$(shell git config --get remote.origin.url)
export VCS_REF:=$(shell git rev-parse --short HEAD)
export VCS_STATUS_CLIENT:=$(if $(shell git status -s),'modified/untracked','clean')

export BUILD_DATE:=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

## ${DOCKER_IMAGE_NAMESPACE}/osparc-python:${DOCKER_IMAGE_TAG}
export DOCKER_IMAGE_NAMESPACE ?= local/simcore/services/comp
export DOCKER_IMAGE_TAG ?= production


.PHONY: help
help: ## help on rule's targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.venv:
	# building python's virtual environment
	@python3 -m venv .venv

devenv: .venv ## build virtual env and installs development tools in it
	# upgrading installing managers
	@$</bin/pip3 install --upgrade \
		pip \
		wheel \
		setuptools
	# installing linters, formatters, ... for vscode
	@$</bin/pip3 install \
		pylint \
		autopep8 \
		rope
	# installing tooling
	@$</bin/pip3 install -r tools/requirements.txt
	@echo "To activate the venv, execute 'source $</bin/activate'"



METADATA_DIR     := docker/labels
METADATA_SOURCES := $(shell find ${METADATA_DIR}/ -type f -name '*.json')
RUN_SCRIPT       := service.cli/do_run

${RUN_SCRIPT}: ${METADATA_SOURCES}
	@.venv/bin/python3 tools/run_creator.py --folder ${METADATA_DIR} --runscript $@

docker-compose.yml: ${METADATA_SOURCES}
	@.venv/bin/python3 tools/update_compose_labels.py --input ${METADATA_DIR} --compose $@

docker-compose-final.yml : docker-compose.yml
	docker-compose -f $< config > $@


.PHONY: build
build: docker-compose-final.yml ${RUN_SCRIPT} ## Builds image
	# building ${DOCKER_IMAGE_NAMESPACE}/osparc-python:${DOCKER_IMAGE_TAG}
	docker-compose -f $< build osparc-python


.PHONY: shell
shell: docker-compose-final.yml
	docker-compose -f $< run osparc-python /bin/bash


.PHONY: up
up: docker-compose-final.yml ## Starts service
	docker-compose -f $< up
	@touch $<

.PHONY: down
down: docker-compose-final.yml ## Stops service
	@docker-compose -f $< down
	@touch $<


.PHONY: unit-test integration-test
unit-test: ## Runs unit tests [w/ fail fast]
	pytest -x -v --junitxml=pytest_unittest.xml --log-level=warning tests/unit

integration-test: ## Runs integration tests [w/ fail fast] (needs built container)
	pytest -x -v --junitxml=pytest_integrationtest.xml --log-level=warning tests/integration


.PHONY: push-release push
push-release: check-release check-pull push

check-pull:
	# check if the service is already online
	@docker login ${DOCKER_REGISTRY};\
	SERVICE_VERSION=$$(cat VERSION);\
	docker pull \
		${DOCKER_REGISTRY}/simcore/services/comp/osparc-python:$$SERVICE_VERSION; \
	if [ $$? -eq 0 ] ; then \
		echo "image already in registry ${DOCKER_REGISTRY}";\
		false;\
	else \
		echo "no image available"; \
	fi;

check-release:
	# check if this is a releasable version number. Major shall be > 0
	@MAJOR_VERSION=$$(cut -f 1 -d '.' VERSION);\
	echo $$MAJOR_VERSION;\
	if [ $$MAJOR_VERSION -eq 0 ] ; then \
		echo "Service major is below 1!!"; \
		false; \
	else\
		echo "Service is releasable";\
	fi


push:
	# push both latest and :$$SERVICE_VERSION tags
	docker login ${DOCKER_REGISTRY};\
	SERVICE_VERSION=$$(cat VERSION);\
	docker tag \
		${DOCKER_REGISTRY}/simcore/services/comp/osparc-python:latest \
		${DOCKER_REGISTRY}/simcore/services/comp/osparc-python:$$SERVICE_VERSION;\
	docker push \
		${DOCKER_REGISTRY}/simcore/services/comp/osparc-python:$$SERVICE_VERSION;\
	docker push \
		${DOCKER_REGISTRY}/simcore/services/comp/osparc-python:latest;

pull:
	# pull latest service version if available
	docker pull \
		${DOCKER_REGISTRY}/simcore/services/comp/osparc-python:latest || true;




.PHONY: regenerate_cookiecutter
regenerate_cookiecutter:
	pip install cookiecutter
	cookiecutter  --no-input --overwrite-if-exists --config-file=.cookiecutterrc gh:ITISFoundation/cookiecutter-osparc-service --output-dir ../

.PHONY: info
# target: info – Displays some parameters of makefile environments
info:
	@echo '+ VCS_* '
	@echo '  - ULR                : ${VCS_URL}'
	@echo '  - REF                : ${VCS_REF}'
	@echo '  - (STATUS)REF_CLIENT : (${VCS_STATUS_CLIENT})'
	@echo '+ BUILD_DATE           : ${BUILD_DATE}'
	@echo '+ OS_VERSION           : ${OS_VERSION}'
	@echo '+ DOCKER_REGISTRY      : ${DOCKER_REGISTRY}'


.PHONY: clean
clean:
	@git clean -dnXf -e .vscode/
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-n} = y ]
	@git clean -dXf -e .vscode/
