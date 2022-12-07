.PHONY: venv requirements tests check-black check-flake lint format

venv:
	python3 -m venv venv

requirements:
	. venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pip install -e .

tests:
	python -m pytest test
	python -m coverage html

check-black:
	python -m black --check markovify test

check-flake:
	python -m flake8 markovify test

lint: check-flake check-black

format:
	python -m black markovify test
