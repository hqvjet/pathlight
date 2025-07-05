# Agentic Service CI/CD Documentation

## Overview

This document describes the complete CI/CD pipeline for the Agentic Service, including automated testing, security scanning, Docker building, and AWS Lambda deployment.

## 🏗️ Architecture

The service follows a controller-router pattern with the following structure:

```
agentic-service/
├── src/
│   ├── main.py              # FastAPI app & Lambda handler
│   ├── config.py            # Configuration management
│   ├── controllers/         # Business logic
│   │   └── file_controller.py
│   ├── routers/             # API routes
│   │   └── file_routes.py
│   └── services/            # Utility services
│       ├── file_service.py
│       └── text_service.py
├── tests/                   # Test files
├── .github/                 # CI/CD configuration
│   └── workflows/
│       └── agentic-service.yml
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
├── Makefile                # Local development commands
└── deploy-lambda.sh        # Manual deployment script
```

## 🚀 Available Endpoints

### File Processing
- `POST /api/v1/vectorize` - Upload files and create embeddings for their content
- `GET /api/v1/s3/files` - List files in S3 bucket
- `GET /api/v1/s3/files/{filename}` - Retrieve a specific file from S3 with download URL

### Health & Debug
- `GET /health` - Service health status
- `GET /debug/config` - Configuration information
- `GET /` - Basic service information

## 🚀 CI/CD Pipeline

### Pipeline Stages

1. **🧪 Testing & Quality**
   - Unit tests with pytest
   - Code coverage analysis
   - Code formatting with Black
   - Linting with flake8
   - Type checking with mypy
   - Security scanning with bandit and safety

2. **🔒 Security Scanning**
   - Dependency vulnerability scanning
   - Code security analysis
   - Docker image vulnerability scanning

3. **🏗️ Build & Deploy**
   - Docker image building
   - Push to Amazon ECR
   - AWS Lambda deployment
   - Function URL configuration
   - Health check validation

4. **🧹 Cleanup**
   - Remove old ECR images
   - Cleanup temporary resources

### Trigger Conditions

- **Push to main**: Deploys to production
- **Push to develop**: Deploys to staging
- **Pull requests**: Runs tests and quality checks only
- **Manual trigger**: Allows custom environment selection

## 🔧 Setup Instructions

### 1. GitHub Repository Setup

1. Create a new repository or use existing one
2. Ensure your code is in the `agentic-service/` directory
3. Copy all CI/CD files to your repository

### 2. GitHub Secrets Configuration

Navigate to your repository **Settings** → **Secrets and variables** → **Actions** and add:

#### Required Secrets:
```
AWS_ACCESS_KEY_ID         # AWS access key for deployment
AWS_SECRET_ACCESS_KEY     # AWS secret key for deployment
OPENAI_API_KEY           # OpenAI API key for the service
AWS_S3_BUCKET_NAME       # S3 bucket name for file storage
```

#### Optional Environment-Specific Secrets:
```
DEV_OPENAI_API_KEY       # Development environment
DEV_AWS_S3_BUCKET_NAME   
STAGING_OPENAI_API_KEY   # Staging environment
STAGING_AWS_S3_BUCKET_NAME
PROD_OPENAI_API_KEY      # Production environment
PROD_AWS_S3_BUCKET_NAME
```

### 3. AWS IAM Setup

Create an IAM user with the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:*",
                "ecr:*",
                "s3:*",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "sts:GetCallerIdentity",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

### 4. Branch Protection (Optional)

Set up branch protection rules:

1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - ✅ Require pull request reviews
   - ✅ Include administrators

## 🛠️ Local Development

### Prerequisites

- Python 3.12
- Docker
- AWS CLI configured
- Make (optional, for using Makefile commands)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd agentic-service
   ```

2. **Create virtual environment**:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

4. **Create environment file**:
   ```bash
   make .env
   # Edit .env file with your values
   ```

5. **Run tests**:
   ```bash
   make test
   ```

6. **Run locally**:
   ```bash
   make run
   ```

### Available Make Commands

```bash
make help              # Show all available commands
make install          # Install dependencies
make test             # Run all tests
make test-unit        # Run unit tests only
make test-integration # Run integration tests only
make lint             # Run linting
make format           # Format code
make format-check     # Check code formatting
make type-check       # Run type checking
make security         # Run security checks
make quality          # Run all quality checks
make build            # Build Docker image
make run              # Run service locally
make run-docker       # Run service in Docker
make deploy           # Deploy to AWS Lambda
make deploy-dev       # Deploy to development
make deploy-staging   # Deploy to staging
make deploy-prod      # Deploy to production
make clean            # Clean up temporary files
make setup-dev        # Setup development environment
make ci-test          # Run all CI checks locally
```

## 🔍 Testing

### Test Structure

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **API tests**: Test HTTP endpoints

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=html
```

### Test Configuration

Tests are configured in `pyproject.toml`:

- Minimum coverage: 70%
- Test discovery: `test_*.py` files
- Markers: `unit`, `integration`, `slow`

## 🐳 Docker

### Building Images

```bash
# Build for development
make build

# Build for specific environment
docker build -t agentic-service:prod .
```

### Running Containers

```bash
# Run with Make
make run-docker

# Run manually
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="your-key" \
  -e AWS_S3_BUCKET_NAME="your-bucket" \
  agentic-service:dev
```

## 🚀 Deployment

### Automatic Deployment

Deployments are automatic based on branch:

- **main branch** → Production environment
- **develop branch** → Staging environment
- **Manual trigger** → Custom environment

### Manual Deployment

```bash
# Deploy to development
make deploy-dev

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-prod

# Deploy to custom environment
./deploy-lambda.sh custom-env
```

### Deployment Artifacts

After deployment, you'll get:

- **Lambda Function**: `agentic-service-{environment}`
- **Function URL**: Public HTTPS endpoint
- **ECR Repository**: Container images
- **CloudWatch Logs**: Function logs

## 📊 Monitoring

### Health Checks

The service provides health check endpoints:

- `GET /health` - Service health status
- `GET /debug/config` - Configuration information
- `GET /` - Basic service information

### Logging

Logs are available in:

- **CloudWatch**: AWS Lambda function logs
- **GitHub Actions**: CI/CD pipeline logs
- **Local**: Console output during development

### Metrics

Monitor the following metrics:

- **Response times**: Function execution duration
- **Error rates**: Failed requests and errors
- **Memory usage**: Lambda memory consumption
- **Invocation count**: Request volume

## 🔧 Troubleshooting

### Common Issues

1. **Import errors in tests**:
   - Ensure `src/` is in Python path
   - Check that all dependencies are installed

2. **AWS deployment failures**:
   - Verify AWS credentials and permissions
   - Check that all required secrets are set
   - Ensure ECR repository exists

3. **Docker build failures**:
   - Check Dockerfile syntax
   - Verify all files are present
   - Ensure base image is available

4. **Lambda timeout errors**:
   - Increase memory allocation
   - Optimize code performance
   - Check for infinite loops

### Debug Commands

```bash
# Check configuration
curl https://your-function-url/debug/config

# Check health
curl https://your-function-url/health

# View logs
aws logs tail /aws/lambda/agentic-service-prod --follow

# Test locally
make run
curl localhost:8000/health
```

## 📈 Performance Optimization

### Lambda Optimization

1. **Memory allocation**: Start with 1024MB, adjust based on usage
2. **Timeout settings**: Set appropriate timeouts (max 15 minutes)
3. **Cold start optimization**: Use provisioned concurrency if needed
4. **Package size**: Minimize dependencies and use layers

### Code Optimization

1. **Async operations**: Use async/await for I/O operations
2. **Connection pooling**: Reuse connections to external services
3. **Caching**: Cache frequently accessed data
4. **Error handling**: Implement proper error handling and retries

## 🔒 Security Best Practices

1. **Secrets management**: Use GitHub Secrets, never commit secrets
2. **IAM permissions**: Follow principle of least privilege
3. **Input validation**: Validate all inputs and file uploads
4. **Rate limiting**: Implement rate limiting for API endpoints
5. **HTTPS only**: Ensure all communications use HTTPS
6. **Regular updates**: Keep dependencies updated

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Mangum Documentation](https://mangum.io/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review GitHub Actions logs
3. Check AWS CloudWatch logs
4. Create an issue in the repository
