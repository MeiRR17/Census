from fastapi import FastAPI, HTTPException, status, Body
from typing import Dict, Any
import logging
from contextlib import asynccontextmanager

from .axl_client import CUCMClient
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global CUCM client instance
cucm_client = None


# Application lifespan manager that initializes the CUCM client on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    global cucm_client
    try:
        logger.info("Initializing CUCM AXL Gateway...")
        cucm_client = CUCMClient()
        logger.info("CUCM AXL Gateway initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize CUCM client: {e}")
        raise
    finally:
        logger.info("CUCM AXL Gateway shutting down...")


# Create FastAPI application with title, description, and lifecycle management
app = FastAPI(
    title="CUCM AXL Gateway",
    description="REST API Gateway for Cisco CUCM AXL operations",
    version="1.0.0",
    lifespan=lifespan
)


# Universal CUCM AXL operation endpoint - dynamic REST-to-SOAP gateway
@app.post("/api/v1/cucm/{operation_name}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_cucm_operation(operation_name: str, payload: Dict[str, Any] = Body(...)):
    if not cucm_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CUCM client not initialized"
        )
    
    try:
        logger.info(f"CUCM operation requested: {operation_name}")
        
        # Execute the universal AXL operation
        result = cucm_client.execute_operation(operation_name, payload)
        
        if result['success']:
            logger.info(f"CUCM operation {operation_name} completed successfully")
            return result['data']
        else:
            # Map AXL errors to appropriate HTTP status codes
            logger.error(f"CUCM operation {operation_name} failed: {result['message']}")
            
            if "not found" in result['message'].lower():
                http_status = status.HTTP_404_NOT_FOUND
            elif "already exists" in result['message'].lower() or "duplicate" in result['message'].lower():
                http_status = status.HTTP_409_CONFLICT
            elif "invalid" in result['message'].lower():
                http_status = status.HTTP_400_BAD_REQUEST
            else:
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            raise HTTPException(
                status_code=http_status,
                detail=result['message']
            )
            
    except HTTPException:
        # Pass through HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute_cucm_operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing CUCM operation"
        )




# List all available CUCM AXL operations for API discovery
@app.get("/api/v1/cucm/operations", status_code=status.HTTP_200_OK)
async def list_cucm_operations():
    if not cucm_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CUCM client not initialized"
        )
    
    try:
        operations = cucm_client.get_operations()
        return {
            "available_operations": operations,
            "total_count": len(operations),
            "usage_example": {
                "endpoint": "/api/v1/cucm/{operation_name}",
                "method": "POST",
                "body": "JSON payload matching the AXL operation parameters"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get CUCM operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available CUCM operations"
        )


# Health check endpoint to verify service availability
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": "CUCM AXL Gateway",
        "version": "1.0.0",
        "cucm_connected": cucm_client is not None
    }


# Root endpoint with basic API information
@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "name": "CUCM AXL Gateway",
        "description": "REST API Gateway for Cisco CUCM AXL operations",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "cucm_operations": "/api/v1/cucm/operations (GET)",
            "execute_operation": "/api/v1/cucm/{operation_name} (POST)",
            "docs": "/docs"
        }
    }
