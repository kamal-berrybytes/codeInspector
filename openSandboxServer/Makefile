.PHONY: help up down logs restart status

help:
	@echo "Available commands:"
	@echo "  make up      - Start the openSandboxServer in the background using docker-compose"
	@echo "  make down    - Stop and remove the openSandboxServer containers"
	@echo "  make restart - Restart the openSandboxServer containers"
	@echo "  make logs    - View the logs of the openSandboxServer"
	@echo "  make status  - Check the status of the openSandboxServer containers"

up:
	docker compose -f docker-compose.example.yaml up -d
	@echo "\nServer is starting up on http://localhost:8090"
	@echo "You can check the logs with 'make logs'"

down:
	docker compose -f docker-compose.example.yaml down

restart:
	docker compose -f docker-compose.example.yaml down
	docker compose -f docker-compose.example.yaml up -d

logs:
	docker compose -f docker-compose.example.yaml logs -f

status:
	docker compose -f docker-compose.example.yaml ps
