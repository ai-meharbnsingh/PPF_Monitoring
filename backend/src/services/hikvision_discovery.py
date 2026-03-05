"""
Module: hikvision_discovery.py
Purpose:
    Hikvision camera network discovery service.
    Extends camera discovery with ONVIF, SSDP, and active network scanning.

Author: PPF Monitoring Team
Created: 2026-03-05
"""

import asyncio
import socket
import uuid
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HikvisionCameraInfo:
    """Information about a discovered Hikvision camera"""
    ip_address: str
    port: int
    device_id: str
    name: str
    model: Optional[str] = None
    manufacturer: str = "Hikvision"
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None
    discovery_method: str = "unknown"
    is_online: bool = False
    rtsp_urls: Dict[str, str] = None
    http_urls: Dict[str, str] = None
    capabilities: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.rtsp_urls is None:
            self.rtsp_urls = {}
        if self.http_urls is None:
            self.http_urls = {}
        if self.capabilities is None:
            self.capabilities = {}
    
    def to_discovery_dict(self) -> Dict[str, Any]:
        """Convert to format compatible with CameraDiscoveryRequest"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "description": f"Discovered {self.manufacturer} camera via {self.discovery_method}",
            "camera_type": "hikvision",
            "model": self.model,
            "manufacturer": self.manufacturer,
            "ip_address": self.ip_address,
            "port": self.port,
            "mac_address": self.mac_address,
            "stream_urls": {
                "rtsp": {"main": self.rtsp_urls.get("main", f"rtsp://{self.ip_address}:554/Streaming/Channels/101")},
                "hls": self.http_urls.get("hls"),
                "webrtc": self.http_urls.get("webrtc"),
            },
            "protocols": ["rtsp", "http"],
            "has_ptz": self.capabilities.get("has_ptz", False),
            "has_audio": self.capabilities.get("has_audio", False),
            "is_online": self.is_online,
            "firmware_version": self.firmware_version,
            "discovered_via": self.discovery_method,
        }


class ONVIFWSdiscovery:
    """
    ONVIF WS-Discovery implementation.
    This is the standard discovery protocol for IP cameras.
    """
    
    MULTICAST_ADDR = "239.255.255.250"
    WS_DISCOVERY_PORT = 3702
    
    PROBE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
               xmlns:tns="http://schemas.xmlsoap.org/ws/2005/04/discovery"
               xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
    <soap:Header>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
        <wsa:MessageID>urn:uuid:{message_id}</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    </soap:Header>
    <soap:Body>
        <tns:Probe>
            <tns:Types>dn:NetworkVideoTransmitter</tns:Types>
        </tns:Probe>
    </soap:Body>
</soap:Envelope>"""
    
    async def discover(self, timeout: float = 3.0) -> List[HikvisionCameraInfo]:
        """
        Discover cameras using ONVIF WS-Discovery multicast.
        
        Args:
            timeout: How long to wait for responses (seconds)
            
        Returns:
            List of discovered camera information
        """
        cameras = []
        found_addrs = set()
        
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.setblocking(False)
            sock.bind(("0.0.0.0", 0))
            
            # Send probe
            message_id = str(uuid.uuid4())
            probe_msg = self.PROBE_TEMPLATE.format(message_id=message_id)
            sock.sendto(
                probe_msg.encode('utf-8'),
                (self.MULTICAST_ADDR, self.WS_DISCOVERY_PORT)
            )
            
            logger.info("ONVIF WS-Discovery probe sent")
            
            # Collect responses
            loop = asyncio.get_event_loop()
            end_time = loop.time() + timeout
            
            while loop.time() < end_time:
                try:
                    remaining = end_time - loop.time()
                    ready = await asyncio.wait_for(
                        loop.sock_recv(sock, 4096),
                        timeout=max(0.1, min(0.5, remaining))
                    )
                    
                    if ready:
                        response = ready.decode('utf-8', errors='ignore')
                        camera = self._parse_response(response)
                        
                        if camera and camera.ip_address not in found_addrs:
                            found_addrs.add(camera.ip_address)
                            cameras.append(camera)
                            logger.info(f"ONVIF discovered: {camera.ip_address} ({camera.name})")
                            
                except asyncio.TimeoutError:
                    continue
                    
            sock.close()
            
        except Exception as e:
            logger.error(f"ONVIF discovery error: {e}")
            
        logger.info(f"ONVIF discovery complete: {len(cameras)} camera(s) found")
        return cameras
    
    def _parse_response(self, response: str) -> Optional[HikvisionCameraInfo]:
        """Parse ONVIF probe response"""
        import re
        
        try:
            # Extract IP from XAddrs
            ip_match = re.search(r'http://(\d+\.\d+\.\d+\.\d+)', response)
            if not ip_match:
                return None
                
            ip_address = ip_match.group(1)
            
            # Default values
            device_id = f"hikvision-onvif-{ip_address.replace('.', '-')}"
            name = "ONVIF Camera"
            manufacturer = None
            model = None
            
            # Parse XML for details
            try:
                root = ET.fromstring(response)
                
                # Look for device info in different namespaces
                for elem in root.iter():
                    tag = elem.tag.lower()
                    text = elem.text or ""
                    
                    # Check for Hikvision in any text content
                    if 'hikvision' in text.lower():
                        manufacturer = "Hikvision"
                    
                    # Extract scopes which contain device info
                    if 'scopes' in tag:
                        scopes = text.split()
                        for scope in scopes:
                            if '/name/' in scope.lower():
                                name = scope.split('/')[-1] or name
                            elif '/hardware/' in scope.lower():
                                model = scope.split('/')[-1] or model
                                
            except ET.ParseError:
                # Fallback to regex
                if 'hikvision' in response.lower():
                    manufacturer = "Hikvision"
                    
            # Only return if it looks like a Hikvision camera or we can't tell
            if manufacturer == "Hikvision" or 'onvif' in response.lower():
                return HikvisionCameraInfo(
                    ip_address=ip_address,
                    port=80,
                    device_id=device_id,
                    name=name,
                    manufacturer=manufacturer or "Unknown",
                    model=model,
                    discovery_method="onvif",
                    is_online=True,
                    rtsp_urls={
                        "main": f"rtsp://{ip_address}:554/Streaming/Channels/101",
                        "sub": f"rtsp://{ip_address}:554/Streaming/Channels/102"
                    },
                    http_urls={
                        "web": f"http://{ip_address}",
                    }
                )
                
        except Exception as e:
            logger.debug(f"Error parsing ONVIF response: {e}")
            
        return None


class HikvisionNetworkScanner:
    """
    Active network scanner for Hikvision cameras.
    Probes IP ranges to find cameras by checking Hikvision-specific endpoints.
    """
    
    # Common ports used by Hikvision cameras
    HIKVISION_PORTS = [80, 81, 82, 8000, 8080]
    
    # Endpoints that indicate Hikvision devices
    HIKVISION_ENDPOINTS = [
        "/ISAPI/System/deviceInfo",
        "/SDK/webLogin",
        "/doc/page/login.asp",
        "/PSIA/System/deviceInfo",
    ]
    
    # Indicators in responses that confirm Hikvision
    HIKVISION_INDICATORS = [
        'hikvision',
        'hik-web',
        'net-dvr',
        'net-hdvr',
        '<vendorname>hikvision</vendorname>',
        'www-authenticate: basic realm="ds-',
        'server: dvrdvs',
    ]
    
    def __init__(self, timeout: float = 2.0, max_concurrent: int = 50):
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.client: Optional[httpx.AsyncClient] = None
    
    async def scan_subnet(self, subnet: str) -> List[HikvisionCameraInfo]:
        """
        Scan a subnet for Hikvision cameras.
        
        Args:
            subnet: CIDR notation subnet (e.g., "192.168.1.0/24")
            
        Returns:
            List of discovered cameras
        """
        import ipaddress
        
        try:
            network = ipaddress.ip_network(subnet, strict=False)
            hosts = list(network.hosts())
            
            logger.info(f"Scanning {len(hosts)} hosts in {subnet}")
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                self.client = client
                
                # Create tasks for all hosts
                tasks = [self._check_host(str(host)) for host in hosts]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
            # Filter out exceptions and None results
            cameras = []
            for result in results:
                if isinstance(result, HikvisionCameraInfo):
                    cameras.append(result)
                elif isinstance(result, Exception):
                    logger.debug(f"Host check error: {result}")
                    
            logger.info(f"Subnet scan complete: {len(cameras)} camera(s) found")
            return cameras
            
        except ValueError as e:
            logger.error(f"Invalid subnet {subnet}: {e}")
            return []
        finally:
            self.client = None
    
    async def scan_ip_range(
        self, 
        start_ip: str, 
        end_ip: str
    ) -> List[HikvisionCameraInfo]:
        """Scan a range of IP addresses"""
        import ipaddress
        
        try:
            start = ipaddress.ip_address(start_ip)
            end = ipaddress.ip_address(end_ip)
            
            hosts = []
            current = start
            while current <= end:
                hosts.append(str(current))
                current += 1
            
            logger.info(f"Scanning IP range {start_ip} to {end_ip} ({len(hosts)} hosts)")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                self.client = client
                tasks = [self._check_host(host) for host in hosts]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
            cameras = [r for r in results if isinstance(r, HikvisionCameraInfo)]
            logger.info(f"Range scan complete: {len(cameras)} camera(s) found")
            return cameras
            
        except ValueError as e:
            logger.error(f"Invalid IP range: {e}")
            return []
        finally:
            self.client = None
    
    async def _check_host(self, ip: str) -> Optional[HikvisionCameraInfo]:
        """Check if a host is a Hikvision camera"""
        async with self.semaphore:
            for port in self.HIKVISION_PORTS:
                camera = await self._probe_port(ip, port)
                if camera:
                    return camera
            return None
    
    async def _probe_port(self, ip: str, port: int) -> Optional[HikvisionCameraInfo]:
        """Probe a specific IP:port for Hikvision camera"""
        if not self.client:
            return None
            
        for endpoint in self.HIKVISION_ENDPOINTS:
            try:
                url = f"http://{ip}:{port}{endpoint}"
                response = await self.client.get(url)
                
                if self._is_hikvision_response(response):
                    return await self._extract_camera_info(ip, port, response)
                    
            except httpx.ConnectError:
                continue
            except httpx.TimeoutException:
                continue
            except Exception as e:
                logger.debug(f"Probe error for {ip}:{port}: {e}")
                continue
                
        return None
    
    def _is_hikvision_response(self, response: httpx.Response) -> bool:
        """Check if HTTP response is from a Hikvision device"""
        content = response.text.lower()
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}
        
        # Check content body
        for indicator in self.HIKVISION_INDICATORS:
            if indicator in content:
                return True
        
        # Check headers
        server = headers.get('server', '')
        if 'hikvision' in server or 'dvrdvs' in server:
            return True
            
        auth = headers.get('www-authenticate', '')
        if 'hikvision' in auth or 'basic realm="ds-' in auth:
            return True
            
        return False
    
    async def _extract_camera_info(
        self, 
        ip: str, 
        port: int, 
        response: httpx.Response
    ) -> HikvisionCameraInfo:
        """Extract detailed info from Hikvision camera"""
        device_id = f"hikvision-{ip.replace('.', '-')}-{port}"
        name = f"Hikvision Camera ({ip})"
        model = None
        firmware = None
        mac_address = None
        capabilities = {"has_ptz": False, "has_audio": False}
        
        # Try ISAPI for detailed info
        if self.client:
            try:
                isapi_url = f"http://{ip}:{port}/ISAPI/System/deviceInfo"
                isapi_resp = await self.client.get(isapi_url)
                
                if isapi_resp.status_code == 200:
                    model, firmware, mac_address = self._parse_device_info(isapi_resp.text)
                    
                # Try to get device name
                name_url = f"http://{ip}:{port}/ISAPI/System/Network/interfaces"
                name_resp = await self.client.get(name_url)
                if name_resp.status_code == 200:
                    # Parse for hostname
                    import re
                    host_match = re.search(r'<id>(\d+)</id>.*?<ipAddress>([^<]+)</ipAddress>', name_resp.text, re.DOTALL)
                    if host_match:
                        pass  # Could use this for validation
                        
            except Exception as e:
                logger.debug(f"Error extracting info from {ip}: {e}")
        
        # Build URLs
        rtsp_urls = {
            "main": f"rtsp://{ip}:554/Streaming/Channels/101",
            "sub": f"rtsp://{ip}:554/Streaming/Channels/102"
        }
        
        http_urls = {
            "web": f"http://{ip}:{port}",
            "snapshot": f"http://{ip}:{port}/ISAPI/Streaming/channels/101/picture",
        }
        
        return HikvisionCameraInfo(
            ip_address=ip,
            port=554,  # RTSP port
            device_id=device_id,
            name=name,
            model=model,
            manufacturer="Hikvision",
            firmware_version=firmware,
            mac_address=mac_address,
            discovery_method="scan",
            is_online=True,
            rtsp_urls=rtsp_urls,
            http_urls=http_urls,
            capabilities=capabilities
        )
    
    def _parse_device_info(self, xml_content: str) -> tuple:
        """Parse ISAPI deviceInfo XML response"""
        model = None
        firmware = None
        mac = None
        
        try:
            root = ET.fromstring(xml_content)
            
            for elem in root.iter():
                tag = elem.tag.lower()
                text = elem.text
                
                if text:
                    if 'model' in tag and 'description' not in tag:
                        model = text
                    elif 'firmwareversion' in tag or ('firmware' in tag and 'ver' in tag):
                        firmware = text
                    elif 'macaddress' in tag or ('mac' in tag and 'addr' in tag):
                        mac = text.upper()
                        
        except ET.ParseError:
            # Try regex fallback
            import re
            model_match = re.search(r'<model>([^<]+)</model>', xml_content, re.IGNORECASE)
            if model_match:
                model = model_match.group(1)
                
        return model, firmware, mac


class HikvisionDiscoveryService:
    """
    Main service for discovering Hikvision cameras on the network.
    Combines multiple discovery methods for maximum coverage.
    """
    
    def __init__(self):
        self.onvif = ONVIFWSdiscovery()
        self.scanner = HikvisionNetworkScanner()
    
    async def discover_cameras(
        self,
        subnet: Optional[str] = None,
        use_onvif: bool = True,
        use_scan: bool = True,
    ) -> List[HikvisionCameraInfo]:
        """
        Discover Hikvision cameras using all available methods.
        
        Args:
            subnet: Optional subnet to scan (e.g., "192.168.1.0/24")
            use_onvif: Whether to use ONVIF WS-Discovery
            use_scan: Whether to use active network scanning
            
        Returns:
            List of discovered cameras
        """
        cameras = []
        found_ips = set()
        
        logger.info("Starting Hikvision camera discovery")
        
        # Method 1: ONVIF WS-Discovery
        if use_onvif:
            try:
                onvif_cameras = await self.onvif.discover(timeout=3.0)
                for cam in onvif_cameras:
                    if cam.ip_address not in found_ips:
                        found_ips.add(cam.ip_address)
                        cameras.append(cam)
                        logger.info(f"ONVIF found: {cam.ip_address}")
            except Exception as e:
                logger.error(f"ONVIF discovery failed: {e}")
        
        # Method 2: Network scan
        if use_scan and subnet:
            try:
                scanned_cameras = await self.scanner.scan_subnet(subnet)
                for cam in scanned_cameras:
                    if cam.ip_address not in found_ips:
                        found_ips.add(cam.ip_address)
                        cameras.append(cam)
                        logger.info(f"Scan found: {cam.ip_address}")
            except Exception as e:
                logger.error(f"Network scan failed: {e}")
        
        logger.info(f"Discovery complete: {len(cameras)} camera(s) found")
        return cameras
    
    def get_local_subnet(self) -> Optional[str]:
        """Auto-detect the local subnet"""
        try:
            # Get local IP by connecting to a public DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0)
            try:
                sock.connect(('8.8.8.8', 1))
                local_ip = sock.getsockname()[0]
            finally:
                sock.close()
            
            # Convert to /24 subnet
            parts = local_ip.split('.')
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            
        except Exception as e:
            logger.warning(f"Could not auto-detect subnet: {e}")
            return None


# Singleton instance
discovery_service = HikvisionDiscoveryService()


async def discover_hikvision_cameras(
    subnet: Optional[str] = None,
    auto_detect_subnet: bool = False,
) -> List[Dict[str, Any]]:
    """
    Convenience function to discover Hikvision cameras.
    
    Args:
        subnet: CIDR subnet to scan (e.g., "192.168.1.0/24")
        auto_detect_subnet: If True, auto-detect local subnet
        
    Returns:
        List of camera info dicts ready for API registration
    """
    service = HikvisionDiscoveryService()
    
    # Auto-detect subnet if requested
    if auto_detect_subnet and not subnet:
        subnet = service.get_local_subnet()
        if subnet:
            logger.info(f"Auto-detected subnet: {subnet}")
    
    # Run discovery
    cameras = await service.discover_cameras(
        subnet=subnet,
        use_onvif=True,
        use_scan=bool(subnet)
    )
    
    # Convert to API-compatible format
    return [cam.to_discovery_dict() for cam in cameras]
