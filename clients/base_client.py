"""
Base Client class for all Census clients
"""
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseClient(ABC):
    """Base client for all external system connections"""
    
    def __init__(self, host: str, username: str, password: str, 
                 verify_ssl: bool = False, timeout: int = 30):
        """
        Initialize base client
        
        Args:
            host: Server hostname/IP
            username: Username for authentication
            password: Password for authentication
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Create session
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Authentication will be handled by subclasses
        self._authenticated = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the server"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the server"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get server status information"""
        pass
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None, 
                     params: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> requests.Response:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            requests.Response object
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.host}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise Exception(f"Request to {self.host} failed: {e}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make GET request"""
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make POST request"""
        return self._make_request("POST", endpoint, data=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make PUT request"""
        return self._make_request("PUT", endpoint, data=data)
    
    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request"""
        return self._make_request("DELETE", endpoint)
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self._authenticated
