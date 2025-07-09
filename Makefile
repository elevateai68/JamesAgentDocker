# Makefile for the James Agent Project

# Build images and start all services
up:
	docker-compose up -d --build

# Stop and remove all services
down:
	docker-compose down --remove-orphans

# Restart all services
restart:
	docker-compose restart

# View live logs for all services
logs:
	docker-compose logs -f

# Automatically format all Python code with Black
format:
	black .

# Check code formatting and lint for potential errors
lint:
	@echo "--- Checking code formatting with Black... ---"
	black --check .
	@echo "\n--- Linting with Flake8... ---"
	flake8 .