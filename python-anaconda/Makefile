export APP_NAME=$(notdir $(CURDIR))
export APP_VERSION=$(shell cat VERSION)

# APP_DESCRIPTION
# APP_USAGE
# APP_URL

export BUILD_DATE:=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
export VCS_URL:=$(shell git config --get remote.origin.url)
export VCS_REF:=$(shell git rev-parse HEAD)

export DOCKER_IMAGE_NAME:=itisfoundation/${APP_NAME}:${APP_VERSION}


SAMPLE_DIR = $(abspath $(CURDIR)/../validation/sample)


.PHONY: build
build: docker-compose.yml
	# building image ${DOCKER_IMAGE_NAME}
	@docker-compose -f $< build
	# Adding swiss.itis.python.requirements label
	@export PIP_REQUIREMENTS="$(shell docker run -it --entrypoint python ${DOCKER_IMAGE_NAME} -m pip list --format=json)"; docker-compose -f $< build


.tmp: $(SAMPLE_DIR)
	mkdir -p .tmp
	cp -r -t .tmp $(SAMPLE_DIR)

.PHONY: shell
shell: # .tmp
	@docker-compose run -w /work -v $(CURDIR)/$<:/work ${APP_NAME} /bin/bash
	# removing .tmp
	@rm -rf .tmp


.PHONY: info
info: ## displays image labels for ${DOCKER_IMAGE_NAME}
	# image labels
	@docker image inspect ${DOCKER_IMAGE_NAME} | jq .[0].Config.Labels
