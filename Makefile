.PHONY: setup run test clean

setup:
	@echo "Setting up development environment..."
	@bash scripts/setup/local_dev_setup.sh

run:
	@echo "Starting services..."
	@docker-compose -f infrastructure/docker/docker-compose.yml up

run-dev:
	@echo "Starting services in development mode..."
	@docker-compose -f infrastructure/docker/docker-compose.yml -f infrastructure/docker/docker-compose.dev.yml up

test:
	@echo "Running tests..."
	@pytest backend/ingestion_service/tests
	@pytest backend/classification_service/tests
	@pytest backend/knowledge_base/tests
	@cd frontend && npm test

clean:
	@echo "Cleaning up..."
	@docker-compose -f infrastructure/docker/docker-compose.yml down -v
	@rm -rf backend/*/venv
	@find . -type d -name "__pycache__" -exec rm -r {} + 