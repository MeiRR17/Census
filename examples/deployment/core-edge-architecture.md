# CMA Core/Edge Architecture Deployment
=====================================

## Overview
The CMA system is designed with a Core/Edge architecture for optimal performance and security:

- **Core Services**: CENSUS, AXLerate, Superset (24/7, high availability)
- **Edge Apps**: Telephony Apps, Meeting Apps (edge deployment, isolated)

## Directory Structure
```
/opt/cma-core/                  <-- Core Services (High Availability)
│   ├── docker-compose.yml      <-- CENSUS, AXLerate, Superset
│   ├── Census/                <-- Central Database
│   ├── AXLerate/              <-- AXL Gateway
│   └── Superset/              <-- BI Platform

/opt/cma-apps/                  <-- Edge Applications (Isolated)
│   ├── telephony-app/          <-- Telephony Management App
│   │   └── docker-compose.yml
│   └── meetings-app/           <-- Meetings Management App
│       └── docker-compose.yml
```

## Network Architecture
```
cma-global-network (Core Network)
├── CENSUS Database
├── AXLerate Gateway
├── Superset
└── API Gateway (Nginx)

telephony-network (Edge Network)
├── Telephony App
├── Mock Server
├── Proxy Gateway
└── Redis
```

## Security Model
- **Core**: Internal services, no external access
- **Edge**: External apps with API Gateway protection
- **Communication**: API Gateway with API Key authentication

## Deployment Strategy
1. **Core Deployment**: Deploy first, ensure 24/7 operation
2. **Edge Deployment**: Deploy apps with API Gateway routing
3. **Integration**: Configure apps to communicate via API Gateway
4. **Monitoring**: Set up centralized logging and health checks

## API Gateway Configuration
- **Authentication**: API Key based
- **Rate Limiting**: Configurable per app
- **CORS**: Cross-origin resource sharing
- **Logging**: Centralized request/response logging

## Environment Variables
### Core Services
```bash
# CENSUS Configuration
CENSUS_DB_URL=postgresql://census_user:census_password@census_db:5432/census_db

# AXLerate Configuration
AXLERATE_BASE_URL=http://axlerate:8000
AXLERATE_API_KEY=your-api-key-here

# Superset Configuration
SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py
CENSUS_DATABASE_URI=postgresql://census_user:census_password@census_db:5432/census_db
```

### Edge Applications
```bash
# Telephony App Configuration
AXLERATE_BASE_URL=http://10.X.X.X:8002  # Core server IP
API_KEY=app-specific-api-key

# Meetings App Configuration
AXLERATE_BASE_URL=http://10.X.X.X:8002
API_KEY=app-specific-api-key
```

## Deployment Commands
```bash
# Deploy Core Services
cd /opt/cma-core
docker-compose up -d

# Deploy Edge Applications
cd /opt/cma-apps/telephony-app
docker-compose up -d

cd /opt/cma-apps/meetings-app
docker-compose up -d
```

## Monitoring and Health Checks
- **Core Services**: Health checks via internal network
- **Edge Apps**: Health checks via API Gateway
- **Centralized Logging**: All logs forwarded to central system
- **Alerting**: Automated alerts for service failures

## Scaling Considerations
- **Core Services**: Horizontal scaling with load balancers
- **Edge Apps**: Independent scaling per application
- **Database**: Read replicas for heavy read workloads
- **API Gateway**: Auto-scaling based on traffic

## Backup and Recovery
- **Core Services**: Automated backups with point-in-time recovery
- **Edge Apps**: Configuration backup and quick redeployment
- **Data Replication**: Real-time replication to disaster recovery site
- **Failover**: Automatic failover to backup systems
