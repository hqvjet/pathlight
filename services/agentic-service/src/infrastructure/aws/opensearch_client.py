"""
🔍 OpenSearch Client Manager

Elegant OpenSearch operations with environment-aware configuration.
Smart enough to know when it should work and when to gracefully skip.
"""

import asyncio
import time
from opensearchpy import OpenSearch, OpenSearchException
from requests.exceptions import Timeout, ConnectionError
from typing import Optional, Dict, Any

from core.logging import setup_logger, log_exception
from core.exceptions import OpenSearchConfigurationError, OpenSearchOperationError
from core.environment import get_environment_type
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



logger = setup_logger(__name__)


class OpenSearchClient:
    """Professional OpenSearch client with environment-aware behavior."""
    
    def __init__(
        self, 
        host: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = True,
        verify_certs: bool = True,
        timeout: int = 60,
    enabled: bool = True,
    skip_local: bool = True,
    force_local: bool = False
    ):
        """
        Initialize OpenSearch client with environment-aware behavior.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port
            username: Username for authentication
            password: Password for authentication
            use_ssl: Whether to use SSL
            verify_certs: Whether to verify certificates
            timeout: Connection timeout
            enabled: Whether OpenSearch is enabled
            skip_local: Skip initializing OpenSearch when environment is local
            force_local: Force OpenSearch in local environment
        """
        self.environment = get_environment_type()
        self.enabled = enabled
        self.client = self._initialize_client_conditional(
            host, port, username, password, use_ssl, verify_certs, timeout, skip_local, force_local
        )

    def _initialize_client_conditional(
        self, 
        host: str, 
        port: int, 
        username: str, 
        password: str, 
        use_ssl: bool, 
        verify_certs: bool, 
        timeout: int,
        skip_local: bool,
        force_local: bool
    ) -> Optional[OpenSearch]:
        """Initialize OpenSearch client based on environment conditions."""
        try:
            # Skip OpenSearch initialization in local environment if not forced
            if self.environment == 'local' and skip_local and not force_local:
                logger.info("Local mode: SKIP_OPENSEARCH_LOCAL=true -> skipping OpenSearch initialization")
                logger.info("Set FORCE_OPENSEARCH_LOCAL=true to override or SKIP_OPENSEARCH_LOCAL=false to enable")
                return None
            
            # Check if OpenSearch is explicitly disabled
            if not self.enabled:
                logger.info("OpenSearch is disabled via configuration")
                return None
            
            # Check if running in test environment
            if self.environment == 'testing':
                logger.info("Running in test environment - skipping OpenSearch initialization")
                return None
            
            # In local environment, disable SSL and certificate verification by default
            if self.environment == 'local':
                if use_ssl or verify_certs:
                    logger.info("Local mode: overriding OpenSearch SSL settings (use_ssl=False, verify_certs=False)")
                use_ssl = False
                verify_certs = False

            return self._initialize_client(host, port, username, password, use_ssl, verify_certs, timeout)
            
        except Exception as e:
            logger.warning(f"OpenSearch initialization failed, continuing without it: {e}")
            return None

    def _initialize_client(
        self, 
        host: str, 
        port: int, 
        username: str, 
        password: str, 
        use_ssl: bool, 
        verify_certs: bool, 
        timeout: int
    ) -> OpenSearch:
        """Initialize OpenSearch client with proper error handling."""
        try:
            logger.info(f"Initializing OpenSearch client with host: {host}")
            
            # Validate required configuration
            if not all([host, port, username, password]):
                missing = [name for name, value in [
                    ("host", host), ("port", port), ("username", username), ("password", password)
                ] if not value]
                raise OpenSearchConfigurationError(f"Missing OpenSearch configuration: {', '.join(missing)}")
            
            scheme = 'https'
            opensearch_client = OpenSearch(
                hosts=[{'host': host, 'port': int(port), 'scheme': scheme}],
                http_auth=(username, password),
                use_ssl=use_ssl,
                verify_certs=verify_certs,
                connection_class=None,
                timeout=timeout,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test the connection with timeout for local environments
            connection_timeout = 5 if self.environment == 'local' else 30
            return self._test_connection(opensearch_client, connection_timeout)
                
        except OpenSearchConfigurationError as e:
            log_exception(logger, "OpenSearch configuration error", e)
            if self.environment == 'lambda':
                # In Lambda, this is a critical error
                raise OpenSearchConfigurationError(f"OpenSearch configuration error in Lambda: {str(e)}")
            else:
                # In local/dev, just warn and continue
                logger.warning("Continuing without OpenSearch in development environment")
                return None
        except Exception as e:
            log_exception(logger, "Unexpected error initializing OpenSearch client", e)
            if self.environment == 'lambda':
                raise OpenSearchConfigurationError(f"Failed to initialize OpenSearch in Lambda: {str(e)}")
            return None

    def _test_connection(self, client: OpenSearch, timeout: int = 30) -> OpenSearch:
        """Test OpenSearch connection with configurable timeout."""
        try:
            logger.info(f"Testing OpenSearch connection with {timeout}s timeout...")
            
            # Simply test the connection using the provided client
            info = client.info()
            logger.info(f"OpenSearch connection successful. Cluster: {info.get('cluster_name', 'Unknown')}")
            return client
            
        except OpenSearchException as e:
            log_exception(logger, "OpenSearch connection test failed", e)
            raise OpenSearchConfigurationError(f"Failed to connect to OpenSearch: {str(e)}")
        except (ConnectionError, Timeout) as e:
            log_exception(logger, f"Network error connecting to OpenSearch (timeout: {timeout}s)", e)
            if self.environment == 'local':
                raise OpenSearchConfigurationError(
                    f"OpenSearch unreachable in local environment. "
                    f"This is expected if OpenSearch is in VPC. "
                    f"Set OPENSEARCH_ENABLED=false or FORCE_OPENSEARCH_LOCAL=false for local development."
                )
            else:
                raise OpenSearchConfigurationError("OpenSearch service is unavailable. Please try again later.")

    def is_available(self) -> bool:
        """Check if OpenSearch client is available."""
        return self.client is not None

    def info(self) -> Dict[str, Any]:
        """Expose basic cluster info similar to opensearchpy client."""
        if not self.is_available():
            raise OpenSearchConfigurationError("OpenSearch client not available")
        return self.client.info()

    def search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Search documents in OpenSearch with retry logic."""
        if not self.is_available():
            raise OpenSearchOperationError("OpenSearch client not available")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.client.search(index=index, body=body)
            except (OpenSearchException, ConnectionError, Timeout) as e:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(f"OpenSearch search attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                log_exception(logger, f"Failed to search after {max_retries} attempts", e)
                raise OpenSearchOperationError(f"Search failed after {max_retries} attempts: {str(e)}")
            except Exception as e:
                log_exception(logger, f"Failed to search OpenSearch", e)
                raise OpenSearchOperationError(f"Search failed: {str(e)}")

    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: str) -> Dict:
        """
        Index a document to OpenSearch with retry logic.
        
        Args:
            index_name: Index name
            document: Document data
            doc_id: Document ID
            
        Returns:
            OpenSearch response
            
        Raises:
            OpenSearchOperationError: If indexing fails
        """
        if not self.is_available():
            raise OpenSearchOperationError("OpenSearch client not available")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.client.index(
                    index=index_name,
                    body=document,
                    id=doc_id,
                    refresh=True,
                    timeout=60
                )
            except (OpenSearchException, ConnectionError, Timeout) as e:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(f"OpenSearch indexing attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                # Last attempt failed
                log_exception(logger, f"Failed to index document {doc_id} after {max_retries} attempts", e)
                raise OpenSearchOperationError(f"Indexing failed after {max_retries} attempts: {str(e)}")
            except Exception as e:
                # Unexpected error - don't retry
                log_exception(logger, f"Failed to index document {doc_id}", e)
                raise OpenSearchOperationError(f"Indexing failed: {str(e)}")
    def refresh_index(self, index_name: str) -> Dict:
        """Force refresh an index to make all recent changes searchable immediately.
        
        Args:
            index_name: Index to refresh
            
        Returns:
            OpenSearch response
        """
        if not self.is_available():
            logger.warning("OpenSearch client not available - skipping refresh")
            return {}
        
        try:
            logger.info(f"Force refreshing index: {index_name}")
            response = self.client.indices.refresh(index=index_name)
            logger.info(f"Index {index_name} refreshed successfully")
            return response
        except Exception as e:
            log_exception(logger, f"Failed to refresh index {index_name}", e)
            # Don't raise - refresh failure is not critical
            return {}
    def index_material_data(self, index_name: str, material_data: Dict[str, Any], material_id: str) -> None:
        """
        Index material data to OpenSearch if available.
        
        Args:
            index_name: Index name
            material_data: Material data to index
            material_id: Material ID
            
        Raises:
            OpenSearchOperationError: If indexing fails in production
        """
        # Check if OpenSearch is available
        if not self.is_available():
            logger.warning(f"OpenSearch client not available in {self.environment} environment, skipping indexing")
            if self.environment == 'lambda':
                # In Lambda, this might be a critical issue
                error = OpenSearchConfigurationError("OpenSearch client not initialized in production environment")
                log_exception(logger, "OpenSearch client not initialized in Lambda environment", error)
                raise error
            return
        
        try:
            logger.info(f"Indexing material data in OpenSearch with ID: {material_id}")
            
            if not index_name:
                raise OpenSearchConfigurationError("Index name not configured")
            
            response = self.index_document(index_name, material_data, material_id)
            logger.info(f"Successfully indexed material data: {response.get('_id', 'Unknown ID')}")
            
        except Exception as e:
            log_exception(logger, "Failed to index data to OpenSearch", e)
            if self.environment == 'lambda':
                # In production, indexing failure might be critical
                raise OpenSearchOperationError(f"OpenSearch indexing failed in production: {str(e)}")
            else:
                # In development, just log the error and continue
                logger.warning(f"OpenSearch indexing failed in {self.environment} environment, continuing...")
