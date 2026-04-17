"""
Phone Scraper - Asynchronous CDP data extraction from Cisco IP Phones.
Scrapes CDP (Cisco Discovery Protocol) information from phone web interfaces.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup, Tag


logger = logging.getLogger(__name__)


class CDPInfo:
    """Data class for CDP information."""
    
    def __init__(self, ip_address: str, switch_name: Optional[str] = None, 
                 switch_port: Optional[str] = None):
        self.ip_address = ip_address
        self.switch_name = switch_name
        self.switch_port = switch_port
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            "ip_address": self.ip_address,
            "switch_name": self.switch_name,
            "switch_port": self.switch_port
        }
    
    def is_valid(self) -> bool:
        """Check if CDP info is valid (has switch name)."""
        return bool(self.switch_name)


class PhoneScraper:
    """
    Asynchronous web scraper for extracting CDP data from Cisco IP Phones.
    """
    
    def __init__(self, timeout_seconds: int = 3, max_concurrent: int = 200):
        """
        Initialize the phone scraper.
        
        Args:
            timeout_seconds: Timeout for each HTTP request
            max_concurrent: Maximum concurrent connections
        """
        self.timeout_seconds = timeout_seconds
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _extract_cdp_from_table(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract CDP information from HTML table.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Tuple of (switch_name, switch_port) or (None, None) if not found
        """
        switch_name = None
        switch_port = None
        
        # Look for all table rows
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label_text = cells[0].get_text(strip=True).lower()
                value_text = cells[1].get_text(strip=True)
                
                # Extract switch name
                if any(keyword in label_text for keyword in [
                    'cdp neighbor device id', 
                    'neighbor device id',
                    'cdp device id',
                    'neighbor device'
                ]):
                    switch_name = value_text
                    logger.debug(f"Found switch name: {switch_name}")
                
                # Extract switch port
                elif any(keyword in label_text for keyword in [
                    'cdp neighbor port',
                    'neighbor port',
                    'cdp port',
                    'neighbor interface'
                ]):
                    switch_port = value_text
                    logger.debug(f"Found switch port: {switch_port}")
        
        return switch_name, switch_port
    
    async def _fetch_page_content(self, session: aiohttp.ClientSession, 
                                 url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML content from a URL.
        
        Args:
            session: aiohttp ClientSession
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)) as response:
                if response.status == 200:
                    content = await response.text()
                    return BeautifulSoup(content, 'html.parser')
                else:
                    logger.debug(f"HTTP {response.status} for {url}")
                    return None
        except asyncio.TimeoutError:
            logger.debug(f"Timeout for {url}")
            return None
        except aiohttp.ClientError as e:
            logger.debug(f"Client error for {url}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error for {url}: {e}")
            return None
    
    async def fetch_cdp_info(self, session: aiohttp.ClientSession, 
                           ip_address: str) -> Optional[Dict]:
        """
        Fetch CDP information from a single phone.
        
        Args:
            session: aiohttp ClientSession
            ip_address: IP address of the phone
            
        Returns:
            Dictionary with CDP info or None if failed
        """
        async with self.semaphore:  # Limit concurrent connections
            # Primary URL to try
            primary_url = f"http://{ip_address}/CGI/Java/Serviceability?adapter=device.statistics.port.network"
            fallback_url = f"http://{ip_address}/CGI/Java/Setup/Network"
            
            # Try primary URL first
            logger.debug(f"Fetching CDP info from {ip_address} (primary)")
            soup = await self._fetch_page_content(session, primary_url)
            
            # If primary fails, try fallback
            if not soup:
                logger.debug(f"Primary URL failed for {ip_address}, trying fallback")
                soup = await self._fetch_page_content(session, fallback_url)
            
            if not soup:
                logger.debug(f"No content retrieved from {ip_address}")
                return None
            
            # Extract CDP information
            switch_name, switch_port = await self._extract_cdp_from_table(soup)
            
            if switch_name:
                cdp_info = CDPInfo(ip_address, switch_name, switch_port)
                logger.info(f"CDP info extracted from {ip_address}: {switch_name} ({switch_port})")
                return cdp_info.to_dict()
            else:
                logger.debug(f"No CDP info found in {ip_address}")
                return None
    
    async def scan_phones_network(self, ip_list: List[str]) -> List[Dict]:
        """
        Scan multiple phones for CDP information concurrently.
        
        Args:
            ip_list: List of IP addresses to scan
            
        Returns:
            List of valid CDP information dictionaries
        """
        logger.info(f"Starting CDP scan for {len(ip_list)} phones (max concurrent: {self.max_concurrent})")
        
        # Create aiohttp session with SSL verification disabled
        connector = aiohttp.TCPConnector(verify_ssl=False, limit=self.max_concurrent + 10)
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        
        valid_results = []
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create tasks for all IPs
            tasks = [
                self.fetch_cdp_info(session, ip) 
                for ip in ip_list
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                ip = ip_list[i]
                
                if isinstance(result, Exception):
                    logger.debug(f"Exception scanning {ip}: {result}")
                elif result:
                    valid_results.append(result)
                else:
                    logger.debug(f"No CDP data from {ip}")
        
        logger.info(f"CDP scan completed: {len(valid_results)}/{len(ip_list)} phones returned data")
        return valid_results
    
    async def scan_single_phone(self, ip_address: str) -> Optional[Dict]:
        """
        Scan a single phone for CDP information.
        
        Args:
            ip_address: IP address of the phone
            
        Returns:
            CDP information dictionary or None if failed
        """
        connector = aiohttp.TCPConnector(verify_ssl=False)
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            return await self.fetch_cdp_info(session, ip_address)


# Convenience functions for direct usage
async def fetch_cdp_info(session: aiohttp.ClientSession, ip_address: str, 
                        timeout_seconds: int = 3) -> Optional[Dict]:
    """
    Convenience function to fetch CDP info from a single phone.
    
    Args:
        session: aiohttp ClientSession
        ip_address: IP address of the phone
        timeout_seconds: Request timeout
        
    Returns:
        Dictionary with CDP info or None if failed
    """
    scraper = PhoneScraper(timeout_seconds=timeout_seconds)
    return await scraper.fetch_cdp_info(session, ip_address)


async def scan_phones_network(ip_list: List[str], max_concurrent: int = 200) -> List[Dict]:
    """
    Convenience function to scan multiple phones for CDP information.
    
    Args:
        ip_list: List of IP addresses to scan
        max_concurrent: Maximum concurrent connections
        
    Returns:
        List of valid CDP information dictionaries
    """
    scraper = PhoneScraper(max_concurrent=max_concurrent)
    return await scraper.scan_phones_network(ip_list)


# Example usage
if __name__ == "__main__":
    import sys
    
    async def main():
        # Example IP addresses
        test_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        
        if len(sys.argv) > 1:
            # Use command line arguments if provided
            test_ips = sys.argv[1:]
        
        # Scan phones
        results = await scan_phones_network(test_ips)
        
        # Print results
        print(f"\nScanned {len(test_ips)} phones, found CDP info for {len(results)}:")
        for result in results:
            print(f"  {result['ip_address']} -> {result['switch_name']} ({result['switch_port']})")
    
    # Run the example
    asyncio.run(main())
