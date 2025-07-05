# GitHub Action Secrets Required for CI/CD

This document lists all the secrets that need to be configured in your GitHub repository for the CI/CD pipeline to work properly.

## Required Secrets

### AWS Credentials
```
AWS_ACCESS_KEY_ID         # AWS Access Key ID for deployment
AWS_SECRET_ACCESS_KEY     # AWS Secret Access Key for deployment
```

### Application Secrets
```
OPENAI_API_KEY           # OpenAI API key for the service
AWS_S3_BUCKET_NAME       # S3 bucket name for file storage
```

## Optional Secrets (Environment-specific)

### Development Environment
```
DEV_OPENAI_API_KEY       # Development OpenAI API key
DEV_AWS_S3_BUCKET_NAME   # Development S3 bucket
```

### Staging Environment
```
STAGING_OPENAI_API_KEY       # Staging OpenAI API key
STAGING_AWS_S3_BUCKET_NAME   # Staging S3 bucket
```

### Production Environment
```
PROD_OPENAI_API_KEY       # Production OpenAI API key
PROD_AWS_S3_BUCKET_NAME   # Production S3 bucket
```

## How to Set Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Navigate to **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Add each secret with the exact name listed above

## IAM Permissions

The AWS credentials should have the following permissions:

### Required IAM Policies:
- `AWSLambdaFullAccess` (or custom Lambda permissions)
- `AmazonEC2ContainerRegistryFullAccess` (for ECR)
- `AmazonS3ReadOnlyAccess` (for S3 file retrieval)
- `IAMFullAccess` (for creating Lambda execution roles)

### Custom IAM Policy Example:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:*",
                "ecr:*",
                "s3:GetObject",
                "s3:ListBucket",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## Environment Variables in Lambda

The following environment variables will be automatically set in Lambda:

- `LOG_LEVEL`
- `MAX_TOKENS_PER_CHUNK`
- `MAX_FILE_SIZE_MB`
- `OPENAI_API_KEY`
- `AWS_S3_BUCKET_NAME`
- `AWS_LAMBDA_FUNCTION_NAME` (automatically set by AWS)
