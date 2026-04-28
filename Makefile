.PHONY: dev lint format type-check test build check

dev:
	python start_services.py

lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint

format:
	cd backend && ruff format app tests
	cd frontend && npm run format

type-check:
	cd backend && python -m mypy app
	cd frontend && npm run type-check

test:
	cd backend && python -m pytest tests/
	cd frontend && npm run test

build:
	cd frontend && npm run build

check: lint type-check test build
