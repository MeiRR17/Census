# CMA Deployment Guide
======================

## Architecture Overview
The CMA system is designed with a Core/Edge architecture for optimal performance and security:

### Core Services (24/7 High Availability)
- **CENSUS Database**: Central data store for all telephony information
- **CENSUS API**: REST API for data access and management  
- **AXLerate Gateway**: Cisco UC integration service
- **Superset**: Business Intelligence platform
- **Redis**: Shared cache service
- **Auth Service**: Centralized authentication and API key management

### Edge Applications (Isolated Deployment)
- **Telephony Management App**: Device and line management
- **Meetings Management App**: Meeting room and scheduling management
- **API Gateway**: Nginx-based gateway with authentication

## Directory Structure
```
CMA/
├── deployment/
│   ├── core-edge-architecture.md    # Architecture documentation
│   ├── api-gateway/                  # API Gateway configuration
│   │   ├── nginx.conf
│   │   ├── docker-compose.yml
│   │   └── auth-service.py
│   ├── core-services/                # Core services deployment
│   │   ├── docker-compose.yml
│   │   └── README.md
│   └── edge-apps/                   # Edge applications
│       ├── telephony-app/
│       │   ├── docker-compose.yml
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── app.py
│       └── meetings-app/
│           ├── docker-compose.yml
│           ├── Dockerfile
│           ├── requirements.txt
│           └── app.py
├── Census/                              # CENSUS system
├── AXLerate/                           # AXL Gateway
└── Superset/                           # BI Platform
```

## Deployment Strategy

### Phase 1: Core Services Deployment
Deploy core services first to ensure 24/7 operation:

```bash
# Navigate to core services
cd /opt/cma-core

# Deploy all core services
docker-compose up -d

# Verify all services are healthy
for service in census-db census-api axlerate superset redis auth-service; do
    echo "Checking $service..."
    curl -f http://localhost:${service_ports[$service]}/health
done
```

### Phase 2: API Gateway Deployment
Deploy the API Gateway for secure external access:

```bash
# Navigate to API Gateway
cd /opt/cma-core/deployment/api-gateway

# Deploy API Gateway
docker-compose up -d

# Verify gateway is healthy
curl -f http://localhost:8001/health
```

### Phase 3: Edge Applications Deployment
Deploy edge applications with API Gateway integration:

```bash
# Deploy Telephony Management App
cd /opt/cma-apps/telephony-app
docker-compose up -d

# Deploy Meetings Management App  
cd /opt/cma-apps/meetings-app
docker-compose up -d

# Verify applications are healthy
curl -f http://localhost:8080/health  # Telephony App
curl -f http://localhost:8090/health  # Meetings App
```

## Environment Configuration

### Core Services Environment
Create `/opt/cma-core/.env`:

```bash
# Database Credentials
CENSUS_PASSWORD=your_secure_census_password
AUTH_PASSWORD=your_secure_auth_password
REDIS_PASSWORD=your_secure_redis_password

# Cisco UC Credentials
CUCM_HOST=cucm.company.com
CUCM_USERNAME=admin
CUCM_PASSWORD=your_cucm_password
UCCX_HOST=uccx.company.com
UCCX_USERNAME=admin
UCCX_PASSWORD=your_uccx_password

# API Keys
CENSUS_API_KEY=your_census_api_key
AUTH_API_KEY=your_auth_service_key
SUPERSET_SECRET_KEY=your_super_secret_key
```

### Edge Applications Environment
Create `/opt/cma-apps/.env`:

```bash
# API Gateway Configuration
API_GATEWAY_URL=http://api-gateway:8001

# Application API Keys
TELEPHONY_APP_KEY=telephony-app-key-123
MEETINGS_APP_KEY=meetings-app-key-456

# Core Service URLs
AXLERATE_BASE_URL=http://10.X.X.X:8002  # Core server IP
CALENDAR_API_URL=https://calendar.company.com/api
CALENDAR_API_KEY=your_calendar_key
```

## Network Configuration

### Core Network (cma-global-network)
- **Subnet**: 172.20.0.0/16
- **Purpose**: Internal service communication
- **Services**: All core services
- **Isolation**: No external access

### Edge Network (telephony-network)
- **Subnet**: 172.20.0.0/16
- **Purpose**: Edge application communication
- **Services**: Edge apps and API Gateway
- **External Access**: Through API Gateway only

## Security Configuration

### API Gateway Security
- **Authentication**: API Key based for all external requests
- **Rate Limiting**: Configurable per application
- **CORS**: Cross-origin resource sharing
- **SSL/TLS**: HTTPS termination (production)
- **Headers**: Security headers (HSTS, XSS Protection, etc.)

### Service-to-Service Authentication
- **Internal Services**: Service tokens for inter-service communication
- **API Keys**: Application-specific keys for external access
- **Permission System**: Role-based access control
- **Audit Logging**: All requests logged with timestamps

## Monitoring and Observability

### Health Checks
All services expose `/health` endpoints:
- **Core Services**: http://localhost:[port]/health
- **Edge Apps**: http://localhost:[port]/health
- **API Gateway**: http://localhost:8001/health

### Centralized Logging
- **Format**: Structured JSON logging
- **Aggregation**: All logs forwarded to central system
- **Rotation**: Automated log rotation
- **Alerting**: Email/Slack notifications for critical issues

### Metrics Collection
- **System Metrics**: CPU, memory, disk, network
- **Application Metrics**: Request/response times, error rates
- **Database Metrics**: Query performance, connection counts
- **Business Metrics**: Device counts, user activity, meeting usage

## API Usage Examples

### Telephony Management App
```bash
# Get all devices
curl -H "X-API-Key: telephony-app-key-123" \
     http://localhost:8080/devices

# Create new device
curl -X POST -H "X-API-Key: telephony-app-key-123" \
     -H "Content-Type: application/json" \
     -d '{"device_name": "Phone-001", "mac_address": "SEP123456789012", "device_type": "Cisco 8841"}' \
     http://localhost:8080/devices
```

### Meetings Management App
```bash
# Get all meeting rooms
curl -H "X-API-Key: meetings-app-key-456" \
     http://localhost:8090/rooms

# Create new meeting
curl -X POST -H "X-API-Key: meetings-app-key-456" \
     -H "Content-Type: application/json" \
     -d '{"title": "Team Meeting", "start_time": "2024-01-15T10:00:00Z", "room_name": "Conference-Room-A"}' \
     http://localhost:8090/meetings
```

## Backup and Recovery

### Automated Backups
```bash
# Database backups
docker-compose exec census-db pg_dump -U census_user census_db > /opt/cma-backups/census/backup_$(date +%Y%m%d_%H%M%S).sql

# Configuration backups
tar -czf /opt/cma-backups/config_$(date +%Y%m%d_%H%M%S).tar.gz /opt/cma-core/
```

### Disaster Recovery
- **Point-in-Time Recovery**: Database PITR capability
- **Service Redeployment**: Quick service restoration
- **Data Validation**: Post-restoration data integrity checks

## Scaling Considerations

### Horizontal Scaling
- **Core Services**: Multiple instances behind load balancers
- **Edge Apps**: Independent scaling per application
- **Database**: Read replicas for heavy read workloads
- **API Gateway**: Auto-scaling based on traffic

### Performance Optimization
- **Database**: Connection pooling, query optimization
- **Caching**: Redis for frequently accessed data
- **CDN**: Static asset delivery (production)
- **Load Balancing**: Round-robin or least connections

## Troubleshooting

### Common Issues
1. **Service won't start**: Check environment variables and port conflicts
2. **Database connection failed**: Verify database is healthy and credentials are correct
3. **API timeouts**: Check network connectivity and service health
4. **High memory usage**: Monitor resource usage and adjust limits

### Debug Commands
```bash
# Check service logs
docker-compose logs -f [service-name]

# Enter service container
docker-compose exec [service-name] /bin/bash

# Check resource usage
docker stats

# Test database connectivity
docker-compose exec census-db psql -U census_user -d census_db -c "SELECT 1;"
```

## Maintenance

### Regular Tasks
- **Daily**: Review logs and performance metrics
- **Weekly**: Update dependencies and security patches
- **Monthly**: Review and update API keys
- **Quarterly**: Performance tuning and optimization
- **Annually**: Architecture review and capacity planning

### Update Process
```bash
# Pull latest images
docker-compose pull

# Recreate services with zero downtime
docker-compose up -d --force-recreate

# Verify all services are healthy
for service in census-api axlerate superset auth-service; do
    curl -f http://localhost:${service_ports[$service]}/health
done
```

## Production Deployment Checklist

### Pre-Deployment
- [ ] Security audit completed
- [ ] Performance testing completed
- [ ] Backup strategy validated
- [ ] Monitoring configured
- [ ] Documentation updated

### Post-Deployment
- [ ] All services healthy
- [ ] Health checks passing
- [ ] Monitoring data flowing
- [ ] First user test successful
- [ ] Backup schedule confirmed

## Support and Contact

### Documentation
- **Architecture**: `/deployment/core-edge-architecture.md`
- **API Documentation**: Available at service `/docs` endpoints
- **Configuration**: Environment variable documentation in service READMEs

### Emergency Contacts
- **Technical Support**: [Contact Information]
- **On-Call Engineer**: [Contact Information]
- **System Administrator**: [Contact Information]

---

**This deployment guide provides a comprehensive framework for deploying and managing the CMA system in production environments.**
