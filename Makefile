PYTHON := python3.11
VENV ?= .venv
POETRY ?= false

.PHONY: setup install lint format typecheck test test-integration coverage up down logs migrate revision alembic

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

install:
	pip install -r requirements.txt

lint:
	black --check src tests
	isort --check-only src tests
	flake8 src tests

format:
	black src tests
	isort src tests

typecheck:
	mypy src/app

test:
	pytest tests/unit

test-integration:
	pytest tests/integration -m integration

coverage:
	pytest --cov=src/app --cov-report=xml --cov-report=html

up:
	docker-compose up --build

logs:
	docker-compose logs -f api

down:
	docker-compose down -v

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "manual"
