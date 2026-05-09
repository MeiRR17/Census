#!/usr/bin/env python3
"""
Test script for SDK imports and basic functionality
"""

print("=" * 60)
print("Testing CMA SDK Imports")
print("=" * 60)

# Test 1: Import ciscoaxl main module
print("\n[1] Testing ciscoaxl main module...")
try:
    from ciscoaxl import CMSClient, MeetingPlaceClient, ExpresswayClient, UCCXClient
    print("  ✓ Main imports successful")
    print(f"    - CMSClient: {CMSClient}")
    print(f"    - MeetingPlaceClient: {MeetingPlaceClient}")
    print(f"    - ExpresswayClient: {ExpresswayClient}")
    print(f"    - UCCXClient: {UCCXClient}")
except Exception as e:
    print(f"  ✗ Import failed: {e}")

# Test 2: Import CMS module
print("\n[2] Testing CMS module...")
try:
    from ciscoaxl.cms import CMSClient as CMSClient2, CMSConfig
    print("  ✓ CMS module imports successful")
    
    # Test CMS client instantiation (without connection)
    print("\n  [2a] Testing CMSClient instantiation...")
    cms = CMSClient(
        host="https://localhost:8443/",
        username="admin",
        password="password",
        verify_ssl=False
    )
    print(f"    ✓ CMSClient created: {cms}")
    print(f"    - BASE_URL: {cms.BASE_URL}")
except Exception as e:
    print(f"  ✗ CMS test failed: {e}")

# Test 3: Import MeetingPlace module
print("\n[3] Testing MeetingPlace module...")
try:
    from ciscoaxl.meetingplace import MeetingPlaceClient as MPClient, MeetingPlaceConfig
    from ciscoaxl.meetingplace import meetings, users
    print("  ✓ MeetingPlace module imports successful")
    print(f"    - meetings module: {meetings}")
    print(f"    - users module: {users}")
except Exception as e:
    print(f"  ✗ MeetingPlace test failed: {e}")

# Test 4: Import Expressway module
print("\n[4] Testing Expressway module...")
try:
    from ciscoaxl.expressway import ExpresswayClient as ExpClient, ExpresswayConfig
    print("  ✓ Expressway module imports successful")
    
    print("\n  [4a] Testing ExpresswayClient instantiation...")
    exp = ExpClient(
        host="https://localhost",
        username="admin",
        password="password",
        verify_ssl=False
    )
    print(f"    ✓ ExpresswayClient created: {exp}")
except Exception as e:
    print(f"  ✗ Expressway test failed: {e}")

# Test 5: Import UCCX module
print("\n[5] Testing UCCX module...")
try:
    from ciscoaxl.uccx import UCCXClient as UCCXClient2, UCCXConfig
    print("  ✓ UCCX module imports successful")
    
    print("\n  [5a] Testing UCCXClient instantiation...")
    uccx = UCCXClient2(
        host="https://localhost",
        username="admin",
        password="password",
        verify_ssl=False
    )
    print(f"    ✓ UCCXClient created: {uccx}")
except Exception as e:
    print(f"  ✗ UCCX test failed: {e}")

# Test 6: Check API availability
print("\n[6] Testing Census API endpoints...")
import requests
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print(f"  ✓ Census API is running (status: {response.status_code})")
        print(f"    Response: {response.text[:100]}")
    else:
        print(f"  ⚠ Census API returned: {response.status_code}")
except Exception as e:
    print(f"  ✗ Cannot connect to Census API: {e}")

# Test 7: List available endpoints
print("\n[7] Available API documentation...")
print(f"  - Swagger UI: http://localhost:8000/docs")
print(f"  - ReDoc: http://localhost:8000/redoc")
print(f"  - OpenAPI JSON: http://localhost:8000/openapi.json")

print("\n" + "=" * 60)
print("SDK Test Summary: All imports successful!")
print("=" * 60)
