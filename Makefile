.PHONY: install test dashboard

install:
	uv sync

test:
	uv run pytest

dashboard:
	uv run streamlit run src/dashboard.py