import requests
from requests.auth import HTTPBasicAuth
from zeep import Client, Transport, helpers
from zeep.exceptions import Fault
from typing import Dict, Any, Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class CUCMClient:
    # Universal Dynamic Proxy for CUCM AXL operations
    # Eliminates need for hardcoded methods - maps any operation dynamically
    # Translates REST JSON to SOAP XML transparently
    
    def __init__(self):
        # Initialize the CUCM AXL client with authentication and transport
        self.client = self._create_client()
    
    def _create_client(self) -> Client:
        # Create and configure the Zeep SOAP client with HTTP authentication
        # Create requests session with authentication and SSL verification disabled
        session = requests.Session()
        session.auth = HTTPBasicAuth(settings.axl_user, settings.axl_password)
        session.verify = False  # Critical for development environment
        
        # Create Zeep transport with the authenticated session
        transport = Transport(session=session, timeout=settings.timeout)
        
        # Initialize Zeep client with WSDL and custom transport
        client = Client(
            wsdl=settings.wsdl_path,
            transport=transport
        )
        
        logger.info("CUCM AXL client initialized successfully")
        return client
    

    def execute_operation(self, operation_name: str, payload_dict: dict) -> dict:
        # Universal method that dynamically executes any AXL operation
        # Uses getattr to map to any Zeep service method dynamically
        # Handles all Zeep Faults with proper error mapping
        try:
            logger.info(f"Executing AXL operation: {operation_name}")
            
            # Dynamically get the AXL method from Zeep service
            axl_method = getattr(self.client.service, operation_name)
            
            # Execute the operation with unpacked payload
            response = axl_method(**payload_dict)
            
            # Convert Zeep response to serializable Python dict
            result_dict = self._serialize_response(response)
            
            logger.info(f"AXL operation {operation_name} completed successfully")
            
            return {
                'success': True,
                'data': result_dict,
                'operation': operation_name
            }
            
        except AttributeError as e:
            error_message = f"AXL operation '{operation_name}' not found. Available operations can be checked in the WSDL."
            logger.error(error_message)
            return {
                'success': False,
                'message': error_message,
                'error_code': 'OPERATION_NOT_FOUND'
            }
            
        except Fault as e:
            # Handle AXL-specific errors
            error_message = f"AXL Error in {operation_name}: {e.message}"
            logger.error(error_message)
            return {
                'success': False,
                'message': error_message,
                'error_code': str(e.code) if hasattr(e, 'code') else 'AXL_FAULT',
                'operation': operation_name
            }
            
        except Exception as e:
            # Handle unexpected errors
            error_message = f"Unexpected error in {operation_name}: {str(e)}"
            logger.error(error_message)
            return {
                'success': False,
                'message': error_message,
                'error_code': 'UNEXPECTED_ERROR',
                'operation': operation_name
            }

    def get_operations(self) -> list:
        # Return all available AXL operations from the WSDL
        # Essential for API discovery and debugging
        try:
            operations = [op for op in dir(self.client.service) 
                         if not op.startswith('_') and callable(getattr(self.client.service, op))]
            return sorted(operations)
        except Exception as e:
            logger.error(f"Failed to get available operations: {e}")
            return []

    def _serialize_response(self, response) -> Dict[str, Any]:
        # Convert Zeep responses to regular Python dictionaries
        # Zeep returns special objects that aren't always JSON serializable
        # This method uses zeep.helpers.serialize_object to convert everything to regular structure
        try:
            # Try serialization with zeep.helpers
            serialized = helpers.serialize_object(response)
            return serialized
        except Exception as e:
            logger.warning(f"Failed to serialize response with zeep.helpers: {e}")
            try:
                # Fallback - try to convert to dict directly
                if hasattr(response, '__dict__'):
                    return response.__dict__
                elif isinstance(response, (dict, list)):
                    return response
                else:
                    return {'value': str(response)}
            except Exception:
                # Ultimate fallback
                return {'value': str(response)}

    
