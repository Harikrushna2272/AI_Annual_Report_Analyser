.PHONY: install install-dev clean lint test format

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	black .
	isort .
	mypy .
	pylint annual_report_analysis tests

test:
	pytest tests/ -v

format:
	black .
	isort .
