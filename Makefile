.PHONY: check nice

check: nice

nice:
	poetry run black src/
	poetry run isort src/
	poetry run mypy src/
