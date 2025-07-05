# Makefile for Agentic Service

.PHONY: help install test lint format security build run clean deploy

# Variables
PYTHON := python3.12
PIP := pip
SERVICE_NAME := agentic-service
ENV := dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov pytest-asyncio black flake8 mypy safety bandit

test: ## Run tests
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	$(PYTHON) -m pytest tests/ -v -m "unit"

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	$(PYTHON) -m pytest tests/ -v -m "integration"

lint: ## Run linting
	@echo "🔍 Running linting..."
	flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code
	@echo "🎨 Formatting code..."
	black src/ tests/
	@echo "✅ Code formatted"

format-check: ## Check code formatting
	@echo "🔍 Checking code formatting..."
	black --check --diff src/ tests/

type-check: ## Run type checking
	@echo "🔍 Running type checking..."
	mypy src/ --ignore-missing-imports

security: ## Run security checks
	@echo "🔒 Running security checks..."
	safety check -r requirements.txt
	bandit -r src/ -f json -o bandit-report.json || true
	@echo "✅ Security checks completed"

quality: lint format-check type-check security ## Run all quality checks

build: ## Build Docker image
	@echo "🏗️ Building Docker image..."
	docker build -t $(SERVICE_NAME):$(ENV) .
	@echo "✅ Docker image built"

run: ## Run the service locally
	@echo "🚀 Starting service locally..."
	cd src && $(PYTHON) main.py

run-docker: build ## Run the service in Docker
	@echo "🐳 Running service in Docker..."
	docker run -p 8000:8000 \
		-e OPENAI_API_KEY="$(OPENAI_API_KEY)" \
		-e AWS_ACCESS_KEY_ID="$(AWS_ACCESS_KEY_ID)" \
		-e AWS_SECRET_ACCESS_KEY="$(AWS_SECRET_ACCESS_KEY)" \
		-e AWS_S3_BUCKET_NAME="$(AWS_S3_BUCKET_NAME)" \
		$(SERVICE_NAME):$(ENV)

deploy: ## Deploy to AWS Lambda
	@echo "🚀 Deploying to AWS Lambda..."
	./deploy-lambda.sh $(ENV)

deploy-dev: ## Deploy to development environment
	@echo "🚀 Deploying to development..."
	ENV=dev $(MAKE) deploy

deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	ENV=staging $(MAKE) deploy

deploy-prod: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	ENV=prod $(MAKE) deploy

clean: ## Clean up temporary files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "bandit-report.json" -delete
	@echo "✅ Cleanup completed"

setup-dev: install ## Setup development environment
	@echo "🛠️ Setting up development environment..."
	pre-commit install || echo "pre-commit not available"
	@echo "✅ Development environment setup completed"

ci-test: install quality test ## Run all CI checks locally
	@echo "✅ All CI checks passed"

# Environment setup helpers
.env: ## Create .env file template
	@echo "Creating .env template..."
	@cat > .env << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your_s3_bucket_name_here

# Service Configuration
LOG_LEVEL=INFO
MAX_TOKENS_PER_CHUNK=500
MAX_FILE_SIZE_MB=10
SERVICE_PORT=8000
EOF
	@echo "✅ .env template created. Please fill in your values."

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "Service documentation available at: http://localhost:8000/docs"
	@echo "Available endpoints:"
	@echo "  POST /api/v1/vectorize - Upload files and create embeddings"
	@echo "  GET /api/v1/s3/files - List files in S3 bucket"
	@echo "  GET /api/v1/s3/files/{filename} - Get file from S3 with download URL"
	@echo "  GET /health - Health check"
	@echo "  GET /debug/config - Debug configuration"
	@echo "Run 'make run' and visit the URL above"
