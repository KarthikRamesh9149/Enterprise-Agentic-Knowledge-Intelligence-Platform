# Local Development

## Start

```bash
docker compose up --build
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.scripts.seed
```

## Backend

```bash
cd backend
pip install -e ".[dev]"
pytest
ruff check .
mypy app
```

## Frontend

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

## Demo Data

Upload Markdown files from `demo-data`, process them, then ask the sample questions from `docs/demo-script.md`.

