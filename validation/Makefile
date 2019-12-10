

objects = $(wildcard sample/*)

sample.zip: $(objects)
	python $(CURDIR)/../tools/create-input.py

.PHONY: input
input: sample.zip


.PHONY: clean
clean:
	@git clean -ndfX
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-n} = y ]
	@git clean -dXf