
.PHONY: install migrate run dev build up down

install:
	poetry install

migrate:
	poetry run alembic upgrade head

run:
	poetry run uvicorn src.app:create_app --host 0.0.0.0 --port 8000

dev:
	poetry run uvicorn src.app:create_app --reload --host 0.0.0.0 --port 8000

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down

dmu:
	docker compose down
	docker compose build
	docker compose up