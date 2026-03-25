# CUCM AXL Gateway

A FastAPI microservice that serves as an API Gateway (Anti-Corruption Layer) for Cisco CUCM AXL operations. This service translates modern REST API requests into legacy SOAP calls for Cisco Unified Communications Manager version 14.

## Architecture

This microservice implements the Anti-Corruption Layer pattern to isolate modern applications from the complexity of legacy CUCM AXL SOAP operations.

### Key Components

- **FastAPI**: Modern, fast web framework for building APIs
- **Zeep**: Python SOAP client for AXL communication
- **Pydantic**: Data validation and settings management
- **Requests**: HTTP session management with authentication

## Project Structure

```
LM/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Environment variables and settings
│   ├── models.py            # Pydantic models for data validation
│   ├── axl_client.py        # CUCM AXL SOAP client
│   └── main.py              # FastAPI application and endpoints
├── AXLAPI.wsdl              # CUCM AXL WSDL file (version 14)
├── .env                     # Environment variables (template)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```bash
# CUCM Server Settings
CUCM_IP=192.168.1.100
AXL_USER=administrator
AXL_PASSWORD=your_password_here
WSDL_PATH=c:\Users\User\Desktop\M_Projects\LM\AXLAPI.wsdl
```

## Usage

### Start the Service

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Create Phone
```http
POST /api/v1/phones
Content-Type: application/json

{
    "mac_address": "00:11:22:33:44:55",
    "description": "Executive Office Phone",
    "device_pool": "Standard Device Pool",
    "template_name": "Cisco 8841"
}
```

#### Health Check
```http
GET /health
```

#### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Features

### MAC Address Validation
- Automatic formatting to uppercase
- Removes colons and hyphens
- Adds 'SEP' prefix automatically
- Validates 12-character hexadecimal format

### Error Handling
- AXL-specific error mapping
- HTTP status code translation
- Detailed error messages
- Comprehensive logging

### Security
- HTTP Basic Authentication
- SSL verification bypass (development)
- Session management with requests

## Development Notes

### MAC Address Format Examples
- Input: `00:11:22:33:44:55` → Output: `SEP001122334455`
- Input: `00-11-22-33-44-55` → Output: `SEP001122334455`
- Input: `001122334455` → Output: `SEP001122334455`
- Input: `SEP001122334455` → Output: `SEP001122334455`

### Error Response Format
```json
{
    "detail": "AXL Error: Phone with name SEP001122334455 already exists"
}
```

## Production Considerations

1. **SSL Verification**: Enable `verify=True` in production
2. **Environment Variables**: Use secure secret management
3. **Logging**: Configure structured logging for monitoring
4. **Rate Limiting**: Implement API rate limiting
5. **Authentication**: Add API key or OAuth2 authentication

## Dependencies

- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- pydantic==2.5.0
- pydantic-settings==2.1.0
- zeep==4.2.1
- requests==2.31.0
- python-multipart==0.0.6
