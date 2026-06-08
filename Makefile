.PHONY: install check run run-dev

PYTHON ?= python
PIP ?= pip

install:
	$(PIP) install -r requirements.txt

check:
	$(PYTHON) -m py_compile app.py config.py mover.py cookidoo_mover.py

run:
	gunicorn --bind 0.0.0.0:5000 app:app

run-dev:
	flask --app app run --debug --host 0.0.0.0 --port 5000
