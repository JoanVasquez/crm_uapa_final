.PHONY: lint pylint flake8 black isort format

lint:
	poetry run black .
	poetry run flake8 .
	poetry run isort .

pylint:
	poetry run pylint --rcfile=.pylintrc .

