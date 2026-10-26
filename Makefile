.PHONY: install data test run

install:
	python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt

data:
	.venv/bin/python scripts/generate_sample_data.py

test:
	.venv/bin/pytest -q

run:
	.venv/bin/streamlit run app.py
