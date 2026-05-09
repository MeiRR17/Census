# Census Clean - Organized Bridge System

## 🎯 Overview

Census Clean is a completely reorganized and simplified bridge system that connects edge applications with Cisco and Oracle servers. It provides bidirectional synchronization, middleware updates, and a clean API for all operations.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Edge Apps     │◄──►│   Census API    │◄──►│ External Systems│
│   (Superset)    │    │   (FastAPI)     │    │ (CUCM, CMS, SBC)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Database)    │
                       └─────────────────┘
```

## 📁 Project Structure

```
Census/
├── clients/                    # All external system clients
│   ├── __init__.py            # Client exports
│   ├── base_client.py         # Base client class
│   ├── cucm_client.py         # CUCM AXL client
│   ├── cms_client.py          # CMS REST client
│   ├── sbc_client.py          # Oracle SBC client
│   ├── meetingplace_client.py # MeetingPlace SOAP client
│   ├── uccx_client.py         # UCCX REST client
│   ├── expressway_client.py   # Expressway REST client
│   └── tgw_client.py          # TGW client (via CUCM)
├── sync/                       # Synchronization system
│   ├── __init__.py            # Sync exports
│   ├── sync_engine.py         # Core sync logic
│   ├── sync_manager.py        # High-level sync management
│   └── middleware.py          # Bidirectional updates
├── main_clean.py              # Main FastAPI application
├── requirements_clean.txt     # Dependencies
├── Dockerfile-clean          # Docker configuration
├── docker-compose-clean.yml  # Docker Compose setup
├── nginx-clean.conf          # Nginx reverse proxy
└── README_CLEAN.md           # This file
```

## 🔌 Supported Systems

### Cisco Systems
- **CUCM** - Cisco Unified Communications Manager (AXL API)
- **CMS** - Cisco Meeting Server (REST API)
- **MeetingPlace** - Cisco MeetingPlace (SOAP API)
- **UCCX** - Cisco Unified Contact Center Express (REST API)
- **Expressway** - Cisco Expressway/VCS (REST API)
- **TGW** - Telephony Gateway (via CUCM)

### Oracle Systems
- **SBC** - Oracle Communications Session Border Controller (REST API)

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.simple .env

# Edit with your server configurations
nano .env
```

### 2. Docker Deployment

```bash
# Build and start all services
docker-compose -f docker-compose-clean.yml up -d

# Check status
docker-compose -f docker-compose-clean.yml ps

# View logs
docker-compose -f docker-compose-clean.yml logs -f census
```

### 3. Manual Installation

```bash
# Install dependencies
pip install -r requirements_clean.txt

# Set up database
createdb census_db

# Run the application
uvicorn main_clean:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Health & Status
- `GET /health` - System health check
- `GET /api/sync/status` - Synchronization status

### Data Management
- `GET /api/devices` - Get all devices
- `POST /api/devices` - Create/update device
- `GET /api/users` - Get all users  
- `POST /api/users` - Create/update user
- `GET /api/meetings` - Get all meetings
- `POST /api/meetings` - Create/update meeting

### Synchronization
- `POST /api/sync` - Trigger full sync
- `POST /api/sync?system=cucm` - Sync specific system

### Middleware
- `POST /api/middleware/update` - Handle bidirectional updates
- `POST /api/middleware/create` - Create entity in external systems

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/census_db

# CUCM
CUCM_HOST=https://cucm-server:8443
CUCM_USERNAME=axl_user
CUCM_PASSWORD=axl_password

# CMS
CMS_HOST=https://cms-server
CMS_USERNAME=admin
CMS_PASSWORD=admin_password

# SBC
SBC_HOST=https://sbc-server
SBC_USERNAME=admin
SBC_PASSWORD=admin_password

# ... (other systems)
```

## 🔄 Synchronization Flow

### 1. Data Collection
```
External Systems → Sync Engine → Database
```

### 2. Bidirectional Updates
```
Edge App → Census API → Middleware → External Systems
```

### 3. Automatic Sync
- **CUCM**: Every 5 minutes
- **CMS**: Every 2 minutes  
- **MeetingPlace**: Every 10 minutes
- **UCCX**: Every 5 minutes
- **Expressway**: Every 5 minutes
- **SBC**: Every 10 minutes
- **TGW**: Every 5 minutes

## 🛡️ Security Features

- **Rate Limiting**: API endpoints protected
- **SSL/TLS**: Encrypted communications
- **Authentication**: Basic auth for external systems
- **CORS**: Configurable cross-origin policies

## 📊 Monitoring

### Health Checks
- Database connectivity
- External system status
- API response times

### Logging
- Structured logging with levels
- Request/response logging
- Error tracking

## 🔍 Usage Examples

### SDK Usage

```python
from simple_sdk import CensusSDK

# Initialize SDK
sdk = CensusSDK("http://localhost:8000")

# Get all devices
devices = sdk.get_devices()

# Create new meeting
meeting = sdk.create_meeting_room(
    meeting_id="CONF001",
    name="Test Conference",
    passcode="123456"
)

# Trigger sync
result = sdk.trigger_sync()
```

### Direct API Usage

```bash
# Get health status
curl http://localhost/health

# Get all CUCM devices
curl http://localhost/api/devices?source=cucm

# Create new device
curl -X POST http://localhost/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SEP001122334455",
    "ip_address": "192.168.1.100",
    "device_type": "Phone",
    "source": "cucm"
  }'

# Trigger sync
curl -X POST http://localhost/api/sync
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL in .env
   - Verify PostgreSQL is running
   - Check network connectivity

2. **External System Authentication Failed**
   - Verify credentials in .env
   - Check network connectivity to servers
   - Verify SSL certificates

3. **Sync Not Working**
   - Check system status: `GET /api/sync/status`
   - Verify external system connectivity
   - Check logs for errors

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
uvicorn main_clean:app --host 0.0.0.0 --port 8000 --log-level debug
```

## 📈 Performance

### Optimization Features
- **Connection Pooling**: Database connections reused
- **Rate Limiting**: Prevent API abuse
- **Caching**: External system status cached
- **Async Operations**: Non-blocking I/O

### Scaling
- **Horizontal Scaling**: Multiple API instances
- **Load Balancing**: Nginx distributes traffic
- **Database Scaling**: PostgreSQL read replicas

## 🔮 Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket notifications
- **Advanced Analytics**: Usage statistics
- **Multi-tenant**: Organization isolation
- **Web UI**: Management dashboard

### Integration Roadmap
- **Additional Systems**: More Cisco/Oracle products
- **Cloud Services**: AWS/Azure integration
- **Monitoring**: Prometheus/Grafana
- **Alerting**: Proactive notifications

## 📞 Support

### Documentation
- **API Docs**: `/docs` endpoint
- **Code Comments**: Inline documentation
- **Examples**: Usage samples

### Getting Help
1. Check logs for error messages
2. Verify configuration in .env
3. Test external system connectivity
4. Review API documentation

---

**Version**: 2.0.0  
**Last Updated**: 2026-05-10  
**Status**: Production Ready
