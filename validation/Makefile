

objects = $(wildcard sample/*)


.PHONY: help
help: ## help on rule's targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.PHONY: input
input: sample.zip ## creates input/sample.zip


sample.zip: $(objects)
	python $(CURDIR)/../tools/setup-validation.py


.PHONY: clean
clean: ## clean outputs
	@git clean -ndfX
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-n} = y ]
	@git clean -dXf