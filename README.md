# Census - Bridge System for Cisco/Oracle Integration

## 📁 Project Structure

```
Census/
├── main.py                     # Main entry point
├── clients/                    # External system clients
│   ├── __init__.py
│   ├── base_client.py         # Base client class
│   ├── cucm_client.py         # CUCM AXL client
│   ├── cms_client.py          # CMS REST client
│   ├── sbc_client.py          # Oracle SBC client
│   ├── meetingplace_client.py # MeetingPlace SOAP client
│   ├── uccx_client.py         # UCCX REST client
│   ├── expressway_client.py   # Expressway REST client
│   └── tgw_client.py          # TGW client (via CUCM)
├── sync/                       # Synchronization system
│   ├── __init__.py
│   ├── sync_engine.py         # Core sync logic
│   ├── sync_manager.py        # High-level sync management
│   └── middleware.py          # Bidirectional updates
├── utils/                      # Utilities and external libraries
│   ├── __init__.py
│   ├── sbc_rest_client/       # SBC REST client library
│   ├── external_sdks/         # External SDK collections
│   ├── test_sdk.py            # SDK testing utilities
│   ├── test_sdk_imports.py    # Import testing
│   ├── simple_sdk.py          # Simple SDK for edge apps
│   ├── requirements_clean.txt  # Clean dependencies
│   ├── requirements_simple.txt # Simple dependencies
│   ├── Dockerfile-clean      # Clean Docker setup
│   └── Dockerfile-simple     # Simple Docker setup
├── config/                     # Configuration files
│   ├── .env                   # Environment variables
│   ├── .env.example           # Environment template
│   ├── .env.simple            # Simple environment
│   ├── docker-compose-clean.yml
│   ├── docker-compose-simple.yml
│   ├── nginx-clean.conf
│   └── nginx-simple.conf
├── examples/                   # Example implementations
│   ├── Superset/              # Superset example
│   └── deployment/            # Deployment examples
├── legacy/                     # Legacy code (kept for reference)
│   └── Census/                # Old implementation
└── docs/                       # Documentation
    ├── README_CLEAN.md         # Detailed documentation
    └── CENSUS_PROJECT_SUMMARY.md
```

## 🚀 Quick Start

```bash
# 1. Setup environment
cp config/.env.example config/.env
# Edit config/.env with your server details

# 2. Run with Docker
docker-compose -f config/docker-compose-clean.yml up -d

# 3. Or run manually
pip install -r utils/requirements_clean.txt
python main.py
```

## 📖 Documentation

See `docs/README_CLEAN.md` for detailed documentation.

## 🔧 How It Works

### 1. Data Flow
```
Edge Apps ←→ Census API ←→ Database ←→ Sync Engine ←→ External Systems
```

### 2. Bidirectional Updates
- When edge apps update data → Census stores it → Middleware updates external systems
- When external systems change → Sync Engine detects → Database updated → Edge apps can query

### 3. Automatic Synchronization
- Each external system has its own sync interval
- Data is collected, transformed, and stored in the database
- Changes are tracked and propagated automatically

## 📞 Support

For detailed information, see the documentation in `docs/README_CLEAN.md`.
