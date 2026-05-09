"""
TGW Client - Telephony Gateway
Client for TGW access through CUCM services
"""
from typing import Dict, Any, List, Optional
from .cucm_client import CUCMClient
import logging

logger = logging.getLogger(__name__)

class TGWClient(CUCMClient):
    """Client for Telephony Gateway accessed through CUCM"""
    
    def __init__(self, host: str, username: str, password: str, **kwargs):
        """
        Initialize TGW client (extends CUCM client)
        
        Args:
            host: CUCM server hostname/IP (TGW accessed via CUCM)
            username: AXL API username
            password: AXL API password
        """
        super().__init__(host, username, password, **kwargs)
        self.tgw_enabled = False
    
    def authenticate(self) -> bool:
        """Authenticate with CUCM and check TGW services"""
        try:
            # First authenticate with CUCM
            if not super().authenticate():
                return False
            
            # Check if TGW services are available
            # This would be implemented based on actual TGW service discovery
            self.tgw_enabled = True
            logger.info("TGW services detected and enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with TGW: {e}")
            return False
    
    def get_tgw_status(self) -> Dict[str, Any]:
        """Get TGW-specific status"""
        try:
            if not self.tgw_enabled:
                return {
                    "status": "disabled",
                    "host": self.host,
                    "message": "TGW services not available"
                }
            
            # Get TGW-specific information
            # This would query TGW-specific tables or services in CUCM
            result = self.service.executeSQLQuery("""
                SELECT COUNT(*) as gateway_count 
                FROM processnode 
                WHERE tkprocessnode = 'Cisco Telephony Gateway'
            """)
            
            gateway_count = int(result[0]['gateway_count'])
            
            return {
                "status": "connected" if self.test_connection() else "disconnected",
                "host": self.host,
                "gateway_count": gateway_count,
                "tgw_enabled": self.tgw_enabled
            }
            
        except Exception as e:
            logger.error(f"Failed to get TGW status: {e}")
            return {
                "status": "error",
                "host": self.host,
                "error": str(e)
            }
    
    def get_tgw_gateways(self) -> List[Dict[str, Any]]:
        """Get all TGW gateways"""
        try:
            if not self.tgw_enabled:
                logger.warning("TGW services not enabled")
                return []
            
            if not self._authenticated:
                self.authenticate()
            
            # Query TGW gateways from CUCM
            sql = """
                SELECT pn.name, pn.description, pn.ipaddress,
                       pn.tkgatewaytype, pn.tkgatewayprotocol
                FROM processnode pn
                WHERE pn.tkprocessnode = 'Cisco Telephony Gateway'
                ORDER BY pn.name
            """
            
            result = self.service.executeSQLQuery(sql)
            
            gateways = []
            for row in result:
                gateways.append({
                    "name": row.get("name"),
                    "description": row.get("description"),
                    "ip_address": row.get("ipaddress"),
                    "gateway_type": row.get("tkgatewaytype"),
                    "protocol": row.get("tkgatewayprotocol")
                })
            
            return gateways
            
        except Exception as e:
            logger.error(f"Failed to get TGW gateways: {e}")
            raise
    
    def get_tgw_routes(self) -> List[Dict[str, Any]]:
        """Get TGW routing information"""
        try:
            if not self.tgw_enabled:
                logger.warning("TGW services not enabled")
                return []
            
            if not self._authenticated:
                self.authenticate()
            
            # Query TGW routes from CUCM
            sql = """
                SELECT r.name, r.description, r.pattern,
                       r.routepartition, r.gwselection
                FROM routingpattern r
                WHERE r.routetype = 'TGW'
                ORDER BY r.name
            """
            
            result = self.service.executeSQLQuery(sql)
            
            routes = []
            for row in result:
                routes.append({
                    "name": row.get("name"),
                    "description": row.get("description"),
                    "pattern": row.get("pattern"),
                    "route_partition": row.get("routepartition"),
                    "gateway_selection": row.get("gwselection")
                })
            
            return routes
            
        except Exception as e:
            logger.error(f"Failed to get TGW routes: {e}")
            raise
    
    def add_tgw_gateway(self, gateway_data: Dict[str, Any]) -> bool:
        """Add a new TGW gateway"""
        try:
            if not self.tgw_enabled:
                logger.error("TGW services not enabled")
                return False
            
            if not self._authenticated:
                self.authenticate()
            
            # Add TGW gateway using CUCM AXL
            result = self.service.addProcessNode(
                name=gateway_data["name"],
                description=gateway_data.get("description", ""),
                tkprocessnode="Cisco Telephony Gateway",
                ipaddress=gateway_data.get("ip_address"),
                tkgatewaytype=gateway_data.get("gateway_type"),
                tkgatewayprotocol=gateway_data.get("protocol", "SIP")
            )
            
            logger.info(f"Added TGW gateway {gateway_data['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add TGW gateway: {e}")
            return False
    
    def update_tgw_gateway(self, gateway_name: str, gateway_data: Dict[str, Any]) -> bool:
        """Update an existing TGW gateway"""
        try:
            if not self.tgw_enabled:
                logger.error("TGW services not enabled")
                return False
            
            if not self._authenticated:
                self.authenticate()
            
            # Update TGW gateway using CUCM AXL
            result = self.service.updateProcessNode(
                name=gateway_name,
                **gateway_data
            )
            
            logger.info(f"Updated TGW gateway {gateway_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update TGW gateway: {e}")
            return False
    
    def delete_tgw_gateway(self, gateway_name: str) -> bool:
        """Delete a TGW gateway"""
        try:
            if not self.tgw_enabled:
                logger.error("TGW services not enabled")
                return False
            
            if not self._authenticated:
                self.authenticate()
            
            result = self.service.removeProcessNode(name=gateway_name)
            
            logger.info(f"Deleted TGW gateway {gateway_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete TGW gateway: {e}")
            return False
