.PHONY: help clean dev docs package test

help:
	@echo "This project assumes that an active Python virtualenv is present."
	@echo "The following make targets are available:"
	@echo "  dev        install all deps for dev environment"
	@echo "  devjs      Run the react dev environment"
	@echo "  clean      remove all old packages"
	@echo "  test       run tests"
	@echo "  deploy     Push to PyPi"
	@echo "  package    Build the PyPi package"

clean:
	rm -rf dist/*
	rm -rf moons_src/build/*

dev:
	pip install --upgrade pip
	pip install wheel -U
	pip install tox -U

test:
	tox

deploy:
	pip install twine
	twine upload dist/*

package:
	pip install -U hatch
	cd moons_src;yarn install;yarn build
	hatch build

devjs:
	cd moons_src;yarn install;yarn start
