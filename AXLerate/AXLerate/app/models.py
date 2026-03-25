# Generic utility models and functions for universal AXL operations

from typing import Dict, Any
from pydantic import BaseModel
import re


class AxlRequestPayload(BaseModel):
    # Generic payload model for any AXL operation
    
    data: Dict[str, Any]


def format_mac_address(mac: str) -> str:
    # Utility function for future device onboarding operations
    # Formats MAC addresses to CUCM standard: uppercase, no separators, SEP prefix
    # Accepts formats like: 00:11:22:33:44:55, 00-11-22-33-44-55, 001122334455, SEP001122334455
    
    # Remove any existing separators and convert to uppercase
    clean_mac = re.sub(r'[:\-]', '', mac.upper())
    
    # Validate MAC address format (12 hexadecimal characters)
    if not re.match(r'^[0-9A-F]{12}$', clean_mac):
        raise ValueError(
            'Invalid MAC address format. Must be 12 hexadecimal characters '
            '(with or without colons/hyphens as separators)'
        )
    
    # Add SEP prefix if not already present
    phone_name = f"SEP{clean_mac}"
    
    return phone_name
