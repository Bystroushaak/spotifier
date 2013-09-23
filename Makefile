.PHONY: all
.PHONY: modules
.PHONY: toolkit
.PHONY: run
.PHONY: clean
.PHONY: distclean
.PHONY: help

all:
	git submodule init
	git submodule update