# author: Pedro Crespo
.DEFAULT_GOAL := help

export VCS_URL:=$(shell git config --get remote.origin.url)
export VCS_REF:=$(shell git rev-parse --short HEAD)
export VCS_STATUS_CLIENT:=$(if $(shell git status -s),'modified/untracked','clean')

export BUILD_DATE:=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

SERVICE_NAME    := osparc-python
SERVICE_VERSION := $(shell cat VERSION)

export DOCKER_REGISTRY  ?= local
export DOCKER_IMAGE_TAG ?= production

ifeq (${DOCKER_REGISTRY}, itisfoundation)
	export DOCKER_IMAGE_NAMESPACE = ${DOCKER_REGISTRY}
else
	export DOCKER_IMAGE_NAMESPACE = ${DOCKER_REGISTRY}/simcore/services/comp
endif

# ${DOCKER_IMAGE_NAMESPACE}/${SERVICE_NAME}:${DOCKER_IMAGE_TAG}

CMD_ARGUMENTS ?= $(cmd)

.PHONY: help
help: ## help on rule's targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.venv:
	# building python's virtual environment
	@python3 -m venv .venv
	# upgrading installing managers
	@.venv/bin/pip install --upgrade \
		pip \
		wheel \
		setuptools


devenv: .venv tools/requirements.txt tests/requirements.txt ## build virtual env and installs development tools in it
	# installing linters, formatters, ... for vscode
	@$</bin/pip install \
		pylint \
		autopep8 \
		rope
	# installing tooling
	@$</bin/pip install -r tools/requirements.txt
	# installing testing
	@$</bin/pip install -r tests/requirements.txt
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
	# building ${DOCKER_IMAGE_NAMESPACE}/${SERVICE_NAME}:${DOCKER_IMAGE_TAG}
	docker-compose -f $< build osparc-python
	@touch $<


.PHONY: shell
shell: docker-compose-final.yml
	@docker-compose -f $< run osparc-python /bin/bash $(if $(CMD_ARGUMENTS),-c "$(CMD_ARGUMENTS)",)
	@touch $<


label: docker-compose-final.yml
	docker-compose -f << run osparc-python pip list --format json



.PHONY: unit-test
unit-test: ## Runs unit tests [w/ fail fast]
	@pytest -vv -x --ff tests/unit

.PHONY: integration-test
integration-test: build ## Runs integration tests [w/ fail fast] (needs built container)
	@pytest -vv -x --ff tests/integration


.PHONY: up
up: docker-compose-final.yml ## Starts service
	docker-compose -f $< up
	@touch $<

.PHONY: down
down: docker-compose-final.yml ## Stops service
	@docker-compose -f $< down
	@touch $<






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
	docker login ${DOCKER_REGISTRY}
	# tagging with version
	SERVICE_VERSION=$$(cat VERSION);\
	docker tag \
		${DOCKER_IMAGE_NAMESPACE}/${SERVICE_NAME}:latest \
		${DOCKER_IMAGE_NAMESPACE}/${SERVICE_NAME}:${SERVICE_VERSION}

	docker push \
		${DOCKER_IMAGE_NAMESPACE}/${SERVICE_NAME}:latest
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


.PHONY: clean
clean:
	@git clean -dnXf -e .vscode/
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-n} = y ]
	@git clean -dXf -e .vscode/
