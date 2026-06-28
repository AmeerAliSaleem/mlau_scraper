.PHONY: install lint format test dashboard

install:
	uv sync

lint:
	uv run ruff check src tests

format:
	uv run ruff check --fix src tests

test:
	uv run pytest

dashboard:
	uv run streamlit run src/dashboard.py