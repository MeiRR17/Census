# CMA Core Services Deployment
=================================

## Overview
This directory contains the core services that run 24/7 in the CMA architecture:

- **CENSUS Database**: Central data store for all telephony information
- **CENSUS API**: REST API for data access and management
- **AXLerate Gateway**: Cisco UC integration service
- **Superset**: BI platform for dashboards and analytics
- **Redis**: Shared cache service
- **Auth Service**: Centralized authentication and API key management

## Services Architecture
```
cma-global-network (172.20.0.0/16)
├── census-db (PostgreSQL:5432)
├── census-api (FastAPI:8001)
├── axlerate-gateway (FastAPI:8000)
├── superset (Web:8088)
├── redis-cache (Redis:6379)
├── auth-service (FastAPI:8002)
└── auth-db (PostgreSQL:5432)
```

## Deployment Instructions

### 1. Environment Setup
Create a `.env` file with the following variables:

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

### 2. Deploy Core Services
```bash
# Navigate to core services directory
cd /opt/cma-core

# Deploy all core services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f census-api
docker-compose logs -f axlerate-gateway
docker-compose logs -f superset
```

### 3. Initialize Database
```bash
# Run database migrations
docker-compose exec census-api alembic upgrade head

# Create initial data (if needed)
docker-compose exec census-api python -c "
from census import init_database
init_database.create_sample_data()
"
```

### 4. Service Health Checks
```bash
# Check all services are healthy
curl http://localhost:8001/health  # CENSUS API
curl http://localhost:8000/health  # AXLerate
curl http://localhost:8088/health  # Superset
curl http://localhost:8002/health  # Auth Service
```

## Service Details

### CENSUS Database
- **Purpose**: Central data store for devices, users, locations, and telephony lines
- **Port**: 5432
- **Data Volume**: `census_data`
- **Backup**: Automated daily backups to `/opt/cma-backups/census/`

### CENSUS API
- **Purpose**: REST API for data access with pagination and filtering
- **Port**: 8001
- **Features**: 
  - Device management
  - User synchronization
  - Real-time metrics
  - API key authentication
- **Documentation**: http://localhost:8001/docs

### AXLerate Gateway
- **Purpose**: Cisco UC integration (CUCM, UCCX, CMS, etc.)
- **Port**: 8000
- **Features**:
  - Real-time device discovery
  - Configuration management
  - Performance monitoring
  - SOAP to REST translation
- **Documentation**: http://localhost:8000/docs

### Superset
- **Purpose**: Business Intelligence and dashboards
- **Port**: 8088
- **Features**:
  - Interactive dashboards
  - SQL charts
  - Data exploration
  - User management
- **Access**: http://localhost:8088
- **Default Credentials**: admin / admin (change in production)

### Auth Service
- **Purpose**: Centralized API key management
- **Port**: 8002
- **Features**:
  - API key generation
  - Rate limiting
  - Permission management
  - Usage analytics
- **Admin Interface**: http://localhost:8002/admin

## Monitoring and Logging

### Health Monitoring
All services expose `/health` endpoints:
- CENSUS API: http://localhost:8001/health
- AXLerate: http://localhost:8000/health
- Superset: http://localhost:8088/health
- Auth Service: http://localhost:8002/health

### Log Aggregation
- **CENSUS API**: `/var/log/census/`
- **AXLerate**: `/var/log/axlerate/`
- **Superset**: `/var/log/superset/`
- **Auth Service**: `/var/log/auth/`

### Metrics Collection
- **System Metrics**: Available via `/metrics` endpoints
- **Database Performance**: PostgreSQL slow query logs
- **API Performance**: Request/response time tracking

## Security Configuration

### Network Security
- All services on internal `cma-global-network`
- Only API Gateway exposed externally
- Firewall rules to restrict access

### Authentication
- **API Keys**: All external access requires valid API key
- **Service-to-Service**: Internal services use service tokens
- **Rate Limiting**: Configurable per application

### Data Protection
- **Encryption**: All data encrypted at rest
- **Backup**: Automated daily backups
- **Access Control**: Role-based permissions

## Scaling and Performance

### Database Scaling
- **Read Replicas**: Additional read-only replicas
- **Connection Pooling**: Optimized connection management
- **Indexing**: Performance indexes on frequently queried fields

### Application Scaling
- **Horizontal Scaling**: Multiple instances behind load balancer
- **Resource Limits**: CPU and memory limits per service
- **Auto-scaling**: Based on CPU/memory usage

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
- **Weekly**: Review logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and update API keys
- **Annually**: Architecture review and optimization planning

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
