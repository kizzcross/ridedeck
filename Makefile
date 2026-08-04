.DEFAULT_GOAL := help
BACKEND := cd backend && . .venv/bin/activate &&

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

## ---- Docker (full stack) ----
up: ## Start the whole stack with Docker Compose
	docker compose up --build

down: ## Stop the stack
	docker compose down

logs: ## Tail backend logs
	docker compose logs -f backend

## ---- Local backend (venv) ----
venv: ## Create venv + install dev deps
	cd backend && python3.13 -m venv .venv && . .venv/bin/activate && \
	  pip install --upgrade pip && pip install -r requirements-dev.txt

migrate: ## Apply migrations
	$(BACKEND) python manage.py migrate

makemigrations: ## Create migrations
	$(BACKEND) python manage.py makemigrations

run: ## Run the dev server locally
	$(BACKEND) python manage.py runserver

seed: ## Load development seed data
	$(BACKEND) python manage.py seed_dev

test: ## Run backend test suite
	$(BACKEND) pytest -q

lint: ## Ruff lint
	$(BACKEND) ruff check .

createadmin: ## Promote / create a Platform Admin (make createadmin EMAIL=you@x.com)
	$(BACKEND) python manage.py create_platform_admin $(EMAIL)

schema: ## Dump the OpenAPI schema to backend/schema.yml
	$(BACKEND) python manage.py spectacular --file schema.yml

## ---- Frontend ----
front-install: ## Install frontend deps
	cd frontend && npm install

front-dev: ## Run Vite dev server
	cd frontend && npm run dev

.PHONY: help up down logs venv migrate makemigrations run seed test lint createadmin schema front-install front-dev
