.PHONY: install test lint typecheck format coverage clean

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt
	. .venv/bin/activate && pip install -e .
	. .venv/bin/activate && pre-commit install

test:
	. .venv/bin/activate && pytest tests/ -q
	. .venv/bin/activate && pytest -W error::DeprecationWarning tests/ -q

lint:
	. .venv/bin/activate && ruff check .

typecheck:
	. .venv/bin/activate && pyright .

format:
	. .venv/bin/activate && ruff format .

coverage:
	. .venv/bin/activate && pytest --cov=src --cov-report=term-missing -q
	. .venv/bin/activate && coverage report

clean:
	rm -rf .venv .pytest_cache .ruff_cache .coverage htmlcov __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
