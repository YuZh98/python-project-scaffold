.PHONY: install test lint clean

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt
	. .venv/bin/activate && pre-commit install

test:
	. .venv/bin/activate && pytest tests/ -q
	. .venv/bin/activate && pytest -W error::DeprecationWarning tests/ -q

lint:
	. .venv/bin/activate && ruff check .
	. .venv/bin/activate && pyright .

clean:
	rm -rf .venv .pytest_cache .ruff_cache .coverage htmlcov __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
