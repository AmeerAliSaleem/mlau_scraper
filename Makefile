.PHONY: install dashboard

install:
	uv sync

dashboard:
	uv run streamlit run src/dashboard.py