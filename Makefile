# author: Pedro Crespo
.DEFAULT_GOAL := help

export VCS_URL:=$(shell git config --get remote.origin.url)
export VCS_REF:=$(shell git rev-parse HEAD)
export VCS_REF_SHORT:=$(shell git rev-parse --short HEAD)
export VSC_IS_DIRTY:=$(if $(shell git status -s),'modified/untracked','')

export BUILD_DATE:=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

SERVICE_NAME    := osparc-python
SERVICE_VERSION := $(shell cat VERSION)

export DOCKER_REGISTRY ?= local
export DOCKER_IMAGE_TAG ?= latest
export DOCKER_IMAGE_NAMESPACE = ${DOCKER_REGISTRY}/simcore/services/comp

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

docker-compose-latest.yml : docker-compose.yml
	docker-compose -f $< config > $@


.PHONY: build
build: docker-compose-latest.yml ${RUN_SCRIPT} ## Builds image
	# building local/simcore/services/comp/${SERVICE_NAME}:${DOCKER_IMAGE_TAG}
	docker-compose -f $< build osparc-python
	@touch $<


.PHONY: shell
shell: docker-compose-latest.yml
	@docker-compose -f $< run osparc-python /bin/bash $(if $(CMD_ARGUMENTS),-c "$(CMD_ARGUMENTS)",)
	@touch $<


.PHONY: label
label: docker-compose-latest.yml
	docker-compose -f << run osparc-python pip list --format=json



# RUN ---

.PHONY: unit-test
unit-test: ## Runs unit tests [w/ fail fast]
	@pytest -vv -x --ff tests/unit

.PHONY: integration-test
integration-test: build ## Runs integration tests [w/ fail fast] (needs built container)
	@pytest -vv -x --ff tests/integration


.PHONY: up
up: docker-compose-latest.yml ## Starts service
	$(MAKE) -C validation clean input
	docker-compose -f $< up
	@touch $<

.PHONY: down
down: docker-compose-latest.yml ## Stops service
	# running ${DOCKER_IMAGE_NAMESPACE}/${SERVICE_NAME}:${DOCKER_IMAGE_TAG}
	@docker-compose -f $< down
	@touch $<



tag-version:
	# local:latest  --> registry:version
	docker tag \
		local/simcore/services/comp/${SERVICE_NAME}:latest \
		${DOCKER_REGISTRY}/simcore/services/comp/${SERVICE_NAME}:${SERVICE_VERSION}


.PHONY: info
info: ## info
	@echo "APP_NAME               = ${APP_NAME}"
	@echo "APP_VERSION            = ${APP_VERSION}"
	@echo "DOCKER_IMAGE_NAMESPACE = ${DOCKER_IMAGE_NAMESPACE}"
	docker image inspect ${DOCKER_IMAGE_NAMESPACE}/${SERVICE_NAME}:${DOCKER_IMAGE_TAG} | jq .[0].Config.Labels



.PHONY: regenerate_cookiecutter
regenerate_cookiecutter:
	pip install cookiecutter
	cookiecutter  --no-input --overwrite-if-exists --config-file=.cookiecutterrc gh:ITISFoundation/cookiecutter-osparc-service --output-dir ../


.PHONY: clean
clean:
	@git clean -dnXf -e .vscode/
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-n} = y ]
	@git clean -dXf -e .vscode/
