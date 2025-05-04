
.PHONY: install migrate run dev build up down

install:
	poetry install
run:
	poetry run uvicorn src.app:create_app --host 0.0.0.0 --port 8000

dev:
	docker compose up app
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