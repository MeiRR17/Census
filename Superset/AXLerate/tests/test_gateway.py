#!/usr/bin/env python3
"""
AXLerate Gateway Integration Tests
================================

Comprehensive tests for the AXLerate API Gateway.
Tests all three Iron Rules implementation.
"""

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_axl_client
from census_integration import get_census_db

class TestIronRules:
    """Test the three Iron Rules implementation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.api_key = "axlerate-api-key"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    async def test_iron_rule_1_sdk_calls(self):
        """Test Iron Rule 1: App calls SDK function"""
        # This tests that the gateway properly calls SDK functions
        # and doesn't try to route commands itself
        
        # Mock the SDK client
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.add_phone.return_value = {
                'success': True,
                'data': {'uuid': 'test-uuid'}
            }
            
            # Test API call
            response = self.client.post(
                "/api/v1/phones",
                json={
                    "name": "TEST1234567890AB",
                    "description": "Test Phone",
                    "product": "Cisco 8841",
                    "device_pool": "Default",
                    "location": "Test_Location"
                },
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            
            # Verify SDK was called
            mock_axl.add_phone.assert_called_once()
    
    async def test_iron_rule_2_rest_to_soap(self):
        """Test Iron Rule 2: Gateway translates REST to SOAP"""
        # This tests that the gateway properly translates REST/JSON
        # requests to SOAP/XML calls to CUCM
        
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.add_phone.return_value = {
                'success': True,
                'data': {'return': 'success'}
            }
            
            # Send REST request
            response = self.client.post(
                "/api/v1/phones",
                json={
                    "name": "TEST1234567890AB",
                    "description": "Test Phone",
                    "product": "Cisco 8841"
                },
                headers=self.headers
            )
            
            # Verify the translation happened
            mock_axl.add_phone.assert_called_once()
            call_args = mock_axl.add_phone.call_args[0][0]
            
            # Should contain SOAP-compatible parameters
            assert 'name' in call_args
            assert call_args['name'] == "TEST1234567890AB"
    
    async def test_iron_rule_3_write_through(self):
        """Test Iron Rule 3: Write-through to CENSUS DB"""
        # This tests that successful operations are written
        # to CENSUS DB immediately after CUCM confirmation
        
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            with pytest.mock.patch('main.get_census_db') as mock_census:
                mock_axl = mock_client.return_value
                mock_census_db = mock_census.return_value
                
                # Mock successful CUCM operation
                mock_axl.add_phone.return_value = {
                    'success': True,
                    'data': {'uuid': 'test-uuid'}
                }
                
                # Make API call
                response = self.client.post(
                    "/api/v1/phones",
                    json={
                        "name": "TEST1234567890AB",
                        "description": "Test Phone"
                    },
                    headers=self.headers
                )
                
                assert response.status_code == 200
                
                # Verify write-through was called
                mock_census_db.write_device_operation.assert_called_once_with(
                    "add_phone",
                    {"mac_address": "TEST1234567890AB", "status": "active"},
                    "api_user"
                )

class TestAPIEndpoints:
    """Test individual API endpoints"""
    
    def setup_method(self):
        self.client = TestClient(app)
        self.api_key = "axlerate-api-key"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert 'success' in data
        assert 'gateway' in data['data']
    
    def test_authentication_required(self):
        """Test that authentication is required"""
        response = self.client.post(
            "/api/v1/phones",
            json={"name": "TEST"}
        )
        assert response.status_code == 401
    
    def test_add_phone_endpoint(self):
        """Test add phone endpoint"""
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.add_phone.return_value = {'success': True}
            
            response = self.client.post(
                "/api/v1/phones",
                json={
                    "name": "TEST1234567890AB",
                    "description": "Test Phone",
                    "product": "Cisco 8841",
                    "device_pool": "Default",
                    "location": "Test_Location"
                },
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
    
    def test_get_phones_endpoint(self):
        """Test get phones endpoint"""
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.get_phones.return_value = {
                'success': True,
                'data': [{'name': 'TEST1'}, {'name': 'TEST2'}]
            }
            
            response = self.client.get("/api/v1/phones", headers=self.headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert len(data['data']) == 2
    
    def test_get_specific_phone_endpoint(self):
        """Test get specific phone endpoint"""
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.get_phone.return_value = {
                'success': True,
                'data': {'name': 'TEST1234567890AB'}
            }
            
            response = self.client.get(
                "/api/v1/phones/TEST1234567890AB",
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert data['data']['name'] == 'TEST1234567890AB'
    
    def test_update_phone_endpoint(self):
        """Test update phone endpoint"""
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.update_phone.return_value = {'success': True}
            
            response = self.client.put(
                "/api/v1/phones/TEST1234567890AB",
                json={
                    "description": "Updated Description",
                    "device_pool": "Updated_Pool"
                },
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
    
    def test_delete_phone_endpoint(self):
        """Test delete phone endpoint"""
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.delete_phone.return_value = {'success': True}
            
            response = self.client.delete(
                "/api/v1/phones/TEST1234567890AB",
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def setup_method(self):
        self.client = TestClient(app)
        self.api_key = "axlerate-api-key"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def test_cucm_connection_error(self):
        """Test handling of CUCM connection errors"""
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_client.side_effect = Exception("CUCM connection failed")
            
            response = self.client.post(
                "/api/v1/phones",
                json={"name": "TEST"},
                headers=self.headers
            )
            
            assert response.status_code == 503
            data = response.json()
            assert data['success'] == False
            assert 'Cannot connect to CUCM server' in data['error']
    
    def test_sdk_operation_failure(self):
        """Test handling of SDK operation failures"""
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            mock_axl = mock_client.return_value
            mock_axl.add_phone.return_value = {
                'success': False,
                'error': 'Phone already exists'
            }
            
            response = self.client.post(
                "/api/v1/phones",
                json={"name": "TEST"},
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == False
            assert data['error'] == 'Phone already exists'
    
    def test_validation_errors(self):
        """Test input validation errors"""
        # Test missing required fields
        response = self.client.post(
            "/api/v1/phones",
            json={"description": "Test"},  # Missing name and product
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error

class TestIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_phone_workflow(self):
        """Test complete phone provisioning workflow"""
        # This test simulates a real-world scenario:
        # 1. Add user
        # 2. Add phone
        # 3. Add line
        # 4. Associate line to phone
        # 5. Verify write-through to CENSUS
        
        with pytest.mock.patch('main.get_axl_client') as mock_client:
            with pytest.mock.patch('main.get_census_db') as mock_census:
                mock_axl = mock_client.return_value
                mock_census_db = mock_census.return_value
                
                # Mock all SDK operations to succeed
                mock_axl.add_user.return_value = {'success': True}
                mock_axl.add_phone.return_value = {'success': True}
                mock_axl.add_line.return_value = {'success': True}
                mock_axl.associate_line_to_phone.return_value = {'success': True}
                
                client = TestClient(app)
                headers = {"Authorization": "Bearer axlerate-api-key"}
                
                # Step 1: Add user
                user_response = client.post(
                    "/api/v1/users",
                    json={
                        "userid": "testuser",
                        "firstname": "Test",
                        "lastname": "User"
                    },
                    headers=headers
                )
                assert user_response.status_code == 200
                
                # Step 2: Add phone
                phone_response = client.post(
                    "/api/v1/phones",
                    json={
                        "name": "TEST1234567890AB",
                        "description": "Test User Phone",
                        "product": "Cisco 8841"
                    },
                    headers=headers
                )
                assert phone_response.status_code == 200
                
                # Step 3: Add line
                line_response = client.post(
                    "/api/v1/lines",
                    json={
                        "pattern": "1001",
                        "description": "Test User Line"
                    },
                    headers=headers
                )
                assert line_response.status_code == 200
                
                # Verify write-through calls
                assert mock_census_db.write_user_operation.call_count == 1
                assert mock_census_db.write_device_operation.call_count == 1
                assert mock_census_db.write_line_operation.call_count == 1

if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v"])
