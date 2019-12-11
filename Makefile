.DEFAULT_GOAL := help

export VCS_URL:=$(shell git config --get remote.origin.url)
export VCS_REF:=$(shell git rev-parse HEAD)
export VCS_REF_SHORT:=$(shell git rev-parse --short HEAD)
export VSC_IS_DIRTY:=$(if $(shell git status -s),'modified/untracked','')

export BUILD_DATE:=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

export DOCKER_IMAGE_NAMESPACE ?= local
# ${DOCKER_IMAGE_NAMESPACE}/osparc-python:${DOCKER_IMAGE_TAG}

$(if $(wildcard .env),include .env,)


.PHONY: help
help: ## help on rule's targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_- ]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.venv:
	# building python's virtual environment
	@python3 -m venv .venv
	# upgrading installing managers
	@.venv/bin/pip install --upgrade \
		pip \
		wheel \
		setuptools

devenv: .venv tools/requirements.txt tests/requirements.txt ## build virtual env and installs development tools in it
	# installing tooling
	@$</bin/pip install -r tools/requirements.txt
	# installing testing
	@$</bin/pip install -r tests/requirements.txt
	#
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
	# building local/simcore/services/comp/osparc-python:${DOCKER_IMAGE_TAG}
	docker-compose -f $< build osparc-python
	@touch $<



# RUN ---
CMD_ARGUMENTS ?= $(cmd)

.PHONY: shell
shell: docker-compose-latest.yml
	@docker-compose -f $< run osparc-python /bin/bash $(if $(CMD_ARGUMENTS),-c "$(CMD_ARGUMENTS)",)
	@touch $<


.PHONY: up
up: docker-compose-latest.yml ## Starts service
	$(MAKE) -C validation clean input
	docker-compose -f $< up
	@touch $<

.PHONY: down
down: docker-compose-latest.yml ## Stops service
	# running ${DOCKER_IMAGE_NAMESPACE}/osparc-python:${DOCKER_IMAGE_TAG}
	@docker-compose -f $< down
	@touch $<


.PHONY: unit-test
unit-test: ## Runs unit tests [w/ fail fast]
	@pytest -vv -x --ff tests/unit

.PHONY: integration-test
integration-test: build ## Runs integration tests [w/ fail fast] (needs built container)
	@pytest -vv -x --ff tests/integration


# VERSIONING ---
SERVICE_VERSION := $(shell cat VERSION)

.PHONY: tag-version
tag-version: ## image versioning: image built locally
	# tags local:latest --> registry:${SERVICE_VERSION}
	docker tag \
		local/osparc-python:latest \
		${DOCKER_REGISTRY}/simcore/services/comp/osparc-python:${SERVICE_VERSION}


.PHONY: patch-version minor-version major-version
patch-version minor-version major-version: ## commits version as patch (bug fixes not affecting the API), minor/minor (backwards-compatible/INcompatible API addition or changes)
	# upgrades as $(subst -version,,$@) version, commits and tags
	@bump2version --verbose --list $(subst -version,,$@)
	# Last commit and tag
	@git log -1 --pretty
	@git tag -l -n1



# MISC ----
.PHONY: info
info: ## info
	#
	docker image inspect local/osparc-python:latest | jq .[0].Config.Labels


.PHONY: clean
clean:
	@git clean -dnXf -e .vscode/
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-n} = y ]
	@git clean -dXf -e .vscode/
