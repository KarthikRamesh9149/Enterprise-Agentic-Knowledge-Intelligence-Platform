SHELL := /bin/sh

.PHONY: up down logs migrate seed backend-test backend-lint backend-typecheck frontend-install frontend-build frontend-typecheck evals smoke-test verify

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python -m app.scripts.seed

backend-test:
	cd backend && pytest

backend-lint:
	cd backend && ruff check .

backend-typecheck:
	cd backend && mypy app

frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

frontend-typecheck:
	cd frontend && npm run typecheck

evals:
	curl -X POST http://localhost:8000/evals/run -H "Content-Type: application/json" -d "{}"

smoke-test:
	curl -f http://localhost:8000/health

verify:
	$(MAKE) backend-lint
	$(MAKE) backend-test
	$(MAKE) frontend-typecheck
	$(MAKE) frontend-build
	docker compose config

