# Census - Bridge System for Cisco/Oracle Integration

Clean deployment-ready version for edge applications.

## 🚀 Quick Start

```bash
# 1. Setup environment
cp config/.env.example config/.env
# Edit config/.env with your server details

# 2. Install dependencies
pip install -r utils/requirements_clean.txt

# 3. Run the application
python main.py
```

## 📁 Project Structure

```
Census/
├── main.py                     # Main application entry point
├── clients/                    # External system clients
├── sync/                       # Synchronization system
├── utils/                      # Utilities and SDK
│   ├── simple_sdk.py          # SDK for edge applications
│   └── requirements_clean.txt # Dependencies
└── config/                     # Configuration files
```

## 📖 API Endpoints

- **Health Check**: `/health`
- **Devices**: `/api/devices` (GET, POST)
- **Meetings**: `/api/meetings` (GET, POST)
- **Users**: `/api/users` (GET, POST)
- **Sync**: `/api/sync` (POST), `/api/sync/status` (GET)
- **Middleware**: `/api/middleware/update` (POST), `/api/middleware/create` (POST)

## 🔧 Edge Application Integration

Use the `utils/simple_sdk.py` to connect your edge applications to Census.

```python
from utils.simple_sdk import CensusSDK

# Initialize SDK
sdk = CensusSDK(base_url="http://localhost:8000")

# Get devices
devices = sdk.get_devices()

# Create a meeting
meeting = sdk.create_meeting({
    "meeting_id": "meeting-123",
    "name": "Team Meeting",
    "source": "edge_app"
})
```
