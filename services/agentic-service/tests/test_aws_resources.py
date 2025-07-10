"""
Test AWS resource connectivity and existence.
This test verifies that all required AWS resources are available and accessible.
"""

import pytest
import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TestAWSResources:
    """Test suite for AWS resource connectivity and existence."""
    
    @pytest.fixture(scope="class")
    def aws_session(self):
        """Create AWS session for testing."""
        try:
            if os.getenv("ACCESS_KEY_ID") and os.getenv("SECRET_ACCESS_KEY"):
                session = boto3.Session(
                    aws_access_key_id=os.getenv("ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY"),
                    region_name=os.getenv("REGION", "ap-northeast-1")
                )
            else:
                session = boto3.Session(region_name=os.getenv("REGION", "ap-northeast-1"))
            return session
        except Exception as e:
            pytest.fail(f"Failed to create AWS session: {e}")
    
    @pytest.mark.aws
    @pytest.mark.smoke
    def test_aws_credentials(self, aws_session):
        """Test AWS credentials are valid."""
        try:
            sts = aws_session.client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"AWS Identity: {identity.get('Arn', 'Unknown')}")
            assert 'Account' in identity
            assert 'Arn' in identity
        except NoCredentialsError:
            pytest.fail("AWS credentials are not configured")
        except ClientError as e:
            pytest.fail(f"AWS credentials are invalid: {e}")
    
    @pytest.mark.aws
    @pytest.mark.integration
    def test_s3_bucket_exists(self, aws_session):
        """Test S3 bucket exists and is accessible."""
        bucket_name = os.getenv("S3_BUCKET_NAME", "pathlight-document")
        
        if not bucket_name:
            pytest.fail("S3_BUCKET_NAME environment variable is not set")
        
        try:
            s3 = aws_session.client('s3')
            s3.head_bucket(Bucket=bucket_name)
            logger.info(f"✅ S3 bucket '{bucket_name}' exists and is accessible")
            
            # Test if we can list objects (permission check)
            try:
                response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                logger.info(f"✅ Can list objects in S3 bucket '{bucket_name}'")
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDenied':
                    pytest.fail(f"Access denied to list objects in S3 bucket '{bucket_name}'")
                else:
                    logger.warning(f"Could not list objects in S3 bucket: {e}")
                    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                pytest.fail(f"S3 bucket '{bucket_name}' does not exist")
            elif error_code == 'AccessDenied':
                pytest.fail(f"Access denied to S3 bucket '{bucket_name}'")
            else:
                pytest.fail(f"Error accessing S3 bucket '{bucket_name}': {e}")
    
    @pytest.mark.aws
    @pytest.mark.integration
    def test_lambda_function_exists(self, aws_session):
        """Test Lambda function exists and is accessible."""
        function_name = os.getenv("LAMBDA_FUNCTION_NAME", "pathlight-agentic-service")
        
        try:
            lambda_client = aws_session.client('lambda')
            response = lambda_client.get_function(FunctionName=function_name)
            
            logger.info(f"✅ Lambda function '{function_name}' exists")
            logger.info(f"Runtime: {response['Configuration'].get('Runtime', 'Unknown')}")
            logger.info(f"State: {response['Configuration'].get('State', 'Unknown')}")
            
            # Check if function is in ACTIVE state
            state = response['Configuration'].get('State')
            if state != 'Active':
                logger.warning(f"Lambda function '{function_name}' is not in Active state: {state}")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                pytest.fail(f"Lambda function '{function_name}' does not exist")
            elif error_code == 'AccessDenied':
                pytest.fail(f"Access denied to Lambda function '{function_name}'")
            else:
                pytest.fail(f"Error accessing Lambda function '{function_name}': {e}")
    
    @pytest.mark.aws
    @pytest.mark.integration
    def test_ecr_repository_exists(self, aws_session):
        """Test ECR repository exists and is accessible."""
        repository_name = os.getenv("ECR_REPOSITORY_NAME", "pathlight/agentic_service")
        
        try:
            ecr = aws_session.client('ecr')
            response = ecr.describe_repositories(repositoryNames=[repository_name])
            
            repo = response['repositories'][0]
            logger.info(f"✅ ECR repository '{repository_name}' exists")
            logger.info(f"URI: {repo.get('repositoryUri', 'Unknown')}")
            logger.info(f"Created: {repo.get('createdAt', 'Unknown')}")
            
            # Check if we can list images
            try:
                images = ecr.list_images(repositoryName=repository_name, maxResults=5)
                image_count = len(images.get('imageIds', []))
                logger.info(f"✅ Found {image_count} images in ECR repository")
            except ClientError as e:
                logger.warning(f"Could not list images in ECR repository: {e}")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'RepositoryNotFoundException':
                pytest.fail(f"ECR repository '{repository_name}' does not exist")
            elif error_code == 'AccessDenied':
                pytest.fail(f"Access denied to ECR repository '{repository_name}'")
            else:
                pytest.fail(f"Error accessing ECR repository '{repository_name}': {e}")
    
    @pytest.mark.smoke
    def test_environment_variables(self):
        """Test that all required environment variables are set."""
        required_vars = [
            "OPENAI_API_KEY",
            "S3_BUCKET_NAME", 
            "REGION"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            pytest.fail(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        logger.info("✅ All required environment variables are set")
        
        # Log configuration (without sensitive data)
        config_info = {
            "REGION": os.getenv("REGION"),
            "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME"),
            "OPENAI_API_KEY_SET": bool(os.getenv("OPENAI_API_KEY")),
            "ACCESS_KEY_ID_SET": bool(os.getenv("ACCESS_KEY_ID")),
            "SECRET_ACCESS_KEY_SET": bool(os.getenv("SECRET_ACCESS_KEY"))
        }
        logger.info(f"Configuration: {config_info}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
