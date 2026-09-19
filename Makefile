lint:
	uv run isort .
	uv run black .
	uv run pylint --recursive=y deployment monitoring tests

unit_test:
	uv run pytest tests/unit_tests

integration_test:
	bash ./tests/integration_tests/run.sh

run: lint unit_test integration_test
	echo HO GYA
