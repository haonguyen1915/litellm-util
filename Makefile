.PHONY: install dev lint test build clean publish publish-test

install:
	poetry install --no-dev

dev:
	poetry install
h
lint:
	ruff check src/
	ruff format --check src/
	mypy src/

test:
	pytest

build: clean
	poetry build

clean:
	rm -rf dist/

publish: build
	poetry publish

publish-test: build
	poetry publish -r testpypi
