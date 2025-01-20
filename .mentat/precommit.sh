ruff format .
ruff check --unsafe-fixes --fix --ignore E722,F821 .
pylint --disable=all --enable=E0001 --ignore=venv .