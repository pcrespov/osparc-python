.DEFAULT_GOAL := all

objects = $(wildcard *.in)
outputs := $(objects:.in=.txt)

all: $(outputs)

%.txt: %.in
	pip-compile --output-file $@ $<


