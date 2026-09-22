# telechan-watcher — Docker helpers
# Run `make` or `make help` to list targets.

IMAGE := telechan-watcher

.PHONY: help build up down stop restart ps logs logs-web config login shell clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Build the image
	docker compose build

up: ## Start watcher + web in the background (builds if needed)
	docker compose up -d --build

down: ## Stop and remove containers
	docker compose down

stop: ## Stop containers, keeping them for auto-restart after Docker starts
	docker compose stop

restart: ## Restart both services
	docker compose restart

ps: ## Show container status
	docker compose ps

logs: ## Follow logs from both services
	docker compose logs -f

logs-web: ## Follow the web service logs
	docker compose logs -f web

config: ## Validate the compose file
	docker compose config

login: ## One-time interactive Telegram login (needs a TTY; stop watcher first)
	docker compose run --rm watcher

shell: ## Open a shell inside the watcher image
	docker compose run --rm watcher bash

clean: ## Remove the built image
	docker rmi $(IMAGE) 2>/dev/null || true
