# Configuration Guide

## Environment Variables (.env file)

The `.env` file should contain **ONLY sensitive information** that cannot be committed to version control.

### Required Variables

```bash
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# AWS Credentials (REQUIRED)
ACCESS_KEY_ID=your_access_key_here
SECRET_ACCESS_KEY=your_secret_key_here
S3_BUCKET_NAME=your_bucket_name_here

# OpenSearch Credentials (REQUIRED for production)
OPENSEARCH_HOST=your-opensearch-domain.region.es.amazonaws.com
OPENSEARCH_USERNAME=your_opensearch_user
OPENSEARCH_PASSWORD=your_opensearch_password
OPENSEARCH_INDEX_NAME=pathlight-vector-db
```

### Optional Environment Variables

```bash
# Environment Override (auto-detected if not set)
ENVIRONMENT=local  # Options: local, lambda, container, testing

# AWS Configuration
REGION=ap-northeast-1  # Default: ap-northeast-1
OPENSEARCH_PORT=443    # Default: 443

# OpenSearch Behavior (environment-aware defaults)
OPENSEARCH_ENABLED=false  # Default: false for local, true for lambda
FORCE_OPENSEARCH_LOCAL=true  # Default: false (force connection in local)

# Service Configuration
SERVICE_PORT=8000  # Default: 8000
LOG_LEVEL=INFO  # Default: INFO
```

## Application Settings (Hard-coded)

These settings are defined in `config.py` and can be modified in code:

- **File Processing**: Max size (100MB), allowed extensions (pdf, docx, txt, md, pptx, xlsx)
- **Chunking**: Max tokens per chunk (512), embedding model (text-embedding-3-small)
- **OpenSearch**: Default port (443), SSL settings, index name (pathlight_materials)

## Environment Behavior

### Local Development
- OpenSearch: **Disabled by default** (expects VPC unreachable)
- Logging: INFO level
- Validation: Relaxed (warnings instead of errors)

### Lambda Production
- OpenSearch: **Required** (will fail if not accessible)
- Logging: INFO level  
- Validation: Strict (errors will stop execution)

### Testing
- OpenSearch: **Disabled** (automatically detected)
- All external services: Skipped or mocked

## Quick Setup

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials

3. Run setup script:
   ```bash
   ./setup-env.sh
   ```

4. Start the service:
   ```bash
   # Local development
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Troubleshooting

### OpenSearch Connection Issues in Local

If you see OpenSearch timeout errors in local development:

1. **Expected behavior**: Set `OPENSEARCH_ENABLED=false` in `.env`
2. **With VPN/tunnel**: Set `FORCE_OPENSEARCH_LOCAL=true` in `.env`
3. **Local OpenSearch**: Use docker-compose to run local OpenSearch

### Lambda Deployment Issues

Ensure these are configured in Lambda environment:
- All required environment variables
- VPC configuration for OpenSearch access
- Security groups allowing OpenSearch communication
- Lambda execution role with proper permissions
