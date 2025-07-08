"""
Test AWS resource connectivity and existence.
This test verifies that all required AWS resources are available and accessible.
"""

import pytest
import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError as OSConnectionError
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
    
    @pytest.mark.opensearch
    @pytest.mark.integration
    def test_opensearch_connection(self):
        """Test OpenSearch cluster connection and accessibility."""
        host = os.getenv("OPENSEARCH_HOST", "")
        port = int(os.getenv("OPENSEARCH_PORT", "443"))
        username = os.getenv("OPENSEARCH_USERNAME", "")
        password = os.getenv("OPENSEARCH_PASSWORD", "")
        use_ssl = os.getenv("OPENSEARCH_USE_SSL", "true").lower() == "true"
        verify_certs = os.getenv("OPENSEARCH_VERIFY_CERTS", "true").lower() == "true"
        index_name = os.getenv("OPENSEARCH_INDEX_NAME", "pathlight-vectors")
        
        # Check required environment variables
        if not host:
            pytest.fail("OPENSEARCH_HOST environment variable is not set")
        if not username:
            pytest.fail("OPENSEARCH_USERNAME environment variable is not set")
        if not password:
            pytest.fail("OPENSEARCH_PASSWORD environment variable is not set")
        
        try:
            # Parse the host URL properly
            opensearch_host = host
            if opensearch_host.startswith('https://'):
                opensearch_host = opensearch_host[8:]
            elif opensearch_host.startswith('http://'):
                opensearch_host = opensearch_host[7:]
            
            # Remove trailing slash if present
            if opensearch_host.endswith('/'):
                opensearch_host = opensearch_host[:-1]
            
            # Create OpenSearch client
            client = OpenSearch(
                hosts=[{
                    'host': opensearch_host,
                    'port': port
                }],
                http_auth=(username, password),
                use_ssl=use_ssl,
                verify_certs=verify_certs,
                timeout=30,
                max_retries=3
            )
            
            # Test connection
            info = client.info()
            logger.info(f"✅ OpenSearch connection successful")
            logger.info(f"Cluster Name: {info.get('cluster_name', 'Unknown')}")
            logger.info(f"Version: {info.get('version', {}).get('number', 'Unknown')}")
            
            # Test if index exists
            try:
                if client.indices.exists(index=index_name):
                    logger.info(f"✅ OpenSearch index '{index_name}' exists")
                    
                    # Get index info
                    index_info = client.indices.get(index=index_name)
                    mapping = index_info[index_name].get('mappings', {})
                    logger.info(f"Index mapping properties: {list(mapping.get('properties', {}).keys())}")
                else:
                    logger.warning(f"⚠️  OpenSearch index '{index_name}' does not exist")
                    
            except Exception as e:
                logger.warning(f"Could not check OpenSearch index: {e}")
            
            # Test if we can perform a basic search
            try:
                search_response = client.search(
                    index=index_name,
                    body={"query": {"match_all": {}}, "size": 0}
                )
                doc_count = search_response['hits']['total']['value']
                logger.info(f"✅ OpenSearch search test successful. Document count: {doc_count}")
            except Exception as e:
                logger.warning(f"Could not perform OpenSearch search test: {e}")
                
        except OSConnectionError as e:
            pytest.fail(f"Failed to connect to OpenSearch: {e}")
        except Exception as e:
            pytest.fail(f"OpenSearch connection test failed: {e}")
    
    @pytest.mark.smoke
    def test_environment_variables(self):
        """Test that all required environment variables are set."""
        required_vars = [
            "OPENAI_API_KEY",
            "S3_BUCKET_NAME", 
            "OPENSEARCH_HOST",
            "OPENSEARCH_USERNAME",
            "OPENSEARCH_PASSWORD",
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
            "OPENSEARCH_HOST": os.getenv("OPENSEARCH_HOST"),
            "OPENSEARCH_PORT": os.getenv("OPENSEARCH_PORT"),
            "OPENSEARCH_INDEX_NAME": os.getenv("OPENSEARCH_INDEX_NAME"),
            "OPENAI_API_KEY_SET": bool(os.getenv("OPENAI_API_KEY")),
            "ACCESS_KEY_ID_SET": bool(os.getenv("ACCESS_KEY_ID")),
            "SECRET_ACCESS_KEY_SET": bool(os.getenv("SECRET_ACCESS_KEY"))
        }
        logger.info(f"Configuration: {config_info}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
