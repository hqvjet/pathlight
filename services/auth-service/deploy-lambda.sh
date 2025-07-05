#!/bin/bash
# =============================================================================
# 🚀 PathLight Auth Service - AWS Lambda Deployment Script
# =============================================================================

set -e

echo "🔧 Preparing PathLight Auth Service for AWS Lambda deployment..."

# Create deployment directory
DEPLOY_DIR="lambda-deployment"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

echo "📦 Copying source files..."
cp -r src/ $DEPLOY_DIR/
cp requirements.txt $DEPLOY_DIR/
cp .env.lambda $DEPLOY_DIR/.env
cp Dockerfile.lambda $DEPLOY_DIR/Dockerfile

echo "📝 Creating Lambda handler..."
cat > $DEPLOY_DIR/lambda_handler.py << 'EOF'
import os
import sys
import json
from mangum import Mangum

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI app
from src.main import app

# Create the Lambda handler
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    return handler(event, context)
EOF

echo "📝 Creating serverless.yml for deployment..."
cat > $DEPLOY_DIR/serverless.yml << 'EOF'
service: pathlight-auth-service

provider:
  name: aws
  runtime: python3.12
  region: us-east-1
  timeout: 30
  memorySize: 512
  environment:
    APP_NAME: PathLight Auth Service
    ENVIRONMENT: production
    DEBUG: false
    SERVICE_PORT: 8000
    # Add your environment variables here or use AWS Parameter Store

functions:
  auth:
    handler: lambda_handler.lambda_handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    zip: true
    slim: true
    strip: false
EOF

echo "📝 Updating requirements.txt for Lambda..."
cat > $DEPLOY_DIR/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
APScheduler==3.10.4
mangum==0.17.0
python-dotenv==1.0.0
EOF

echo "📝 Creating Lambda-optimized Dockerfile..."
cat > $DEPLOY_DIR/Dockerfile << 'EOF'
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements first for better caching
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY .env ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD ["lambda_handler.lambda_handler"]
EOF

echo "📝 Creating deployment instructions..."
cat > $DEPLOY_DIR/DEPLOY.md << 'EOF'
# 🚀 PathLight Auth Service - AWS Lambda Deployment

## Prerequisites
1. AWS CLI configured
2. Serverless Framework installed: `npm install -g serverless`
3. Serverless Python Requirements plugin: `serverless plugin install -n serverless-python-requirements`

## Deployment Options

### Option 1: Serverless Framework (Recommended)
```bash
cd lambda-deployment
serverless deploy
```

### Option 2: AWS Lambda Container Image
```bash
cd lambda-deployment

# Build and tag the image
docker build -t pathlight-auth-service .

# Tag for ECR
docker tag pathlight-auth-service:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pathlight-auth-service:latest

# Push to ECR (create repository first)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pathlight-auth-service:latest

# Create Lambda function with container image
aws lambda create-function \
  --function-name pathlight-auth-service \
  --package-type Image \
  --code ImageUri=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pathlight-auth-service:latest \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role
```

### Option 3: ZIP Package
```bash
cd lambda-deployment
pip install -r requirements.txt -t .
zip -r function.zip . -x "*.pyc" "__pycache__/*"

# Upload via AWS CLI
aws lambda create-function \
  --function-name pathlight-auth-service \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://function.zip
```

## Environment Configuration
Make sure to set these environment variables in your Lambda function:
- DATABASE_URL
- JWT_SECRET_KEY  
- JWT_REFRESH_SECRET_KEY
- SMTP_USERNAME
- SMTP_PASSWORD
- FRONTEND_URL
- ADMIN_USERNAME
- ADMIN_PASSWORD

## Database Setup
- Use AWS RDS for PostgreSQL
- Update DATABASE_URL in environment variables
- Run migrations manually or via Lambda deployment
EOF

echo "✅ Lambda deployment package ready in '$DEPLOY_DIR/' directory"
echo "📖 See $DEPLOY_DIR/DEPLOY.md for deployment instructions"
