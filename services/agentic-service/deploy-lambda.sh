#!/bin/bash

# AWS Lambda Deployment Script for Agentic Service
# Usage: ./deploy-lambda.sh [ENVIRONMENT]

set -e

# Configuration
ENVIRONMENT=${1:-dev}
SERVICE_NAME="agentic-service"
FUNCTION_NAME="${SERVICE_NAME}-${ENVIRONMENT}"
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${SERVICE_NAME}"

echo "🚀 Deploying ${FUNCTION_NAME} to AWS Lambda..."
echo "📍 Region: ${REGION}"
echo "🏷️  ECR Repository: ${ECR_REPOSITORY}"

# Check if required tools are installed
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t ${SERVICE_NAME}:${ENVIRONMENT} .

# Tag image for ECR
docker tag ${SERVICE_NAME}:${ENVIRONMENT} ${ECR_REPOSITORY}:${ENVIRONMENT}
docker tag ${SERVICE_NAME}:${ENVIRONMENT} ${ECR_REPOSITORY}:latest

# Login to ECR
echo "🔑 Logging into ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_REPOSITORY}

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names ${SERVICE_NAME} --region ${REGION} 2>/dev/null || {
    echo "📦 Creating ECR repository..."
    aws ecr create-repository --repository-name ${SERVICE_NAME} --region ${REGION}
}

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push ${ECR_REPOSITORY}:${ENVIRONMENT}
docker push ${ECR_REPOSITORY}:latest

# Get the image URI
IMAGE_URI="${ECR_REPOSITORY}:${ENVIRONMENT}"

# Check if Lambda function exists
if aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} 2>/dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --image-uri ${IMAGE_URI} \
        --region ${REGION}
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name ${FUNCTION_NAME} \
        --timeout 900 \
        --memory-size 3008 \
        --region ${REGION}
else
    echo "🆕 Creating new Lambda function..."
    
    # Create IAM role if it doesn't exist
    ROLE_NAME="${SERVICE_NAME}-lambda-role"
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
    
    if ! aws iam get-role --role-name ${ROLE_NAME} 2>/dev/null; then
        echo "🔐 Creating IAM role..."
        
        # Create trust policy
        cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        # Create the role
        aws iam create-role \
            --role-name ${ROLE_NAME} \
            --assume-role-policy-document file://trust-policy.json
        
        # Attach basic Lambda execution policy
        aws iam attach-role-policy \
            --role-name ${ROLE_NAME} \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        # Attach S3 read access policy (adjust based on your needs)
        aws iam attach-role-policy \
            --role-name ${ROLE_NAME} \
            --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
        
        rm trust-policy.json
        
        echo "⏳ Waiting for IAM role to be available..."
        sleep 10
    fi
    
    # Create Lambda function
    aws lambda create-function \
        --function-name ${FUNCTION_NAME} \
        --package-type Image \
        --code ImageUri=${IMAGE_URI} \
        --role ${ROLE_ARN} \
        --timeout 900 \
        --memory-size 3008 \
        --region ${REGION} \
        --environment Variables='{
            "LOG_LEVEL":"INFO",
            "MAX_TOKENS_PER_CHUNK":"500",
            "MAX_FILE_SIZE_MB":"10"
        }'
fi

# Create or update function URL (for HTTP access)
echo "🌐 Setting up Function URL..."
aws lambda create-function-url-config \
    --function-name ${FUNCTION_NAME} \
    --auth-type NONE \
    --cors '{
        "AllowCredentials": false,
        "AllowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "AllowOrigins": ["*"],
        "AllowHeaders": ["*"],
        "MaxAge": 86400
    }' \
    --region ${REGION} 2>/dev/null || \
aws lambda update-function-url-config \
    --function-name ${FUNCTION_NAME} \
    --auth-type NONE \
    --cors '{
        "AllowCredentials": false,
        "AllowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "AllowOrigins": ["*"],
        "AllowHeaders": ["*"],
        "MaxAge": 86400
    }' \
    --region ${REGION}

# Get function URL
FUNCTION_URL=$(aws lambda get-function-url-config --function-name ${FUNCTION_NAME} --region ${REGION} --query FunctionUrl --output text)

echo "✅ Deployment completed successfully!"
echo "🔗 Function URL: ${FUNCTION_URL}"
echo "📝 Function Name: ${FUNCTION_NAME}"
echo "🏷️  Image URI: ${IMAGE_URI}"
echo ""
echo "💡 Test your deployment:"
echo "   curl ${FUNCTION_URL}"
echo "   curl ${FUNCTION_URL}health"
echo "   curl ${FUNCTION_URL}api/v1/s3/files"
echo ""
echo "🔧 To update environment variables:"
echo "   aws lambda update-function-configuration --function-name ${FUNCTION_NAME} --environment Variables='{\"OPENAI_API_KEY\":\"your-key\",\"AWS_S3_BUCKET_NAME\":\"your-bucket\"}'"
