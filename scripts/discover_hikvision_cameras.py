#!/usr/bin/env python3
"""
Hikvision Camera Discovery Script

Scans the local network for Hikvision IP cameras using multiple methods:
1. ONVIF WS-Discovery (standard for IP cameras)
2. UPnP/SSDP multicast discovery
3. IP range scanning with Hikvision-specific probes

Usage:
    python discover_hikvision_cameras.py
    python discover_hikvision_cameras.py --subnet 192.168.1.0/24
    python discover_hikvision_cameras.py --ip-range 192.168.1.1-192.168.1.254

Author: PPF Monitoring Team
"""

import argparse
import asyncio
import json
import socket
import struct
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

try:
    import httpx
except ImportError:
    print("Installing required package: httpx")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


@dataclass
class DiscoveredCamera:
    """Represents a discovered Hikvision camera"""
    ip_address: str
    port: int
    device_id: str
    name: str
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None
    discovery_method: str = "unknown"
    is_online: bool = False
    rtsp_urls: dict = None
    http_urls: dict = None
    
    def __post_init__(self):
        if self.rtsp_urls is None:
            self.rtsp_urls = {}
        if self.http_urls is None:
            self.http_urls = {}
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def get_rtsp_url(self, username: str = "admin", password: str = "", channel: int = 1) -> str:
        """Generate RTSP URL for Hikvision camera"""
        auth = f"{username}:{password}@" if password else f"{username}@"
        return f"rtsp://{auth}{self.ip_address}:{self.port}/Streaming/Channels/{channel}01"


class ONVIFDiscovery:
    """ONVIF WS-Discovery implementation for finding IP cameras"""
    
    WS_DISCOVERY_MULTICAST = "239.255.255.250"
    WS_DISCOVERY_PORT = 3702
    
    WS_DISCOVERY_PROBE = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
               xmlns:tns="http://schemas.xmlsoap.org/ws/2005/04/discovery">
    <soap:Header>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
        <wsa:MessageID>urn:uuid:probe-msg-id</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    </soap:Header>
    <soap:Body>
        <tns:Probe>
            <tns:Types>dn:NetworkVideoTransmitter</tns:Types>
        </tns:Probe>
    </soap:Body>
</soap:Envelope>"""
    
    async def discover(self, timeout: float = 3.0) -> List[DiscoveredCamera]:
        """Discover cameras using ONVIF WS-Discovery"""
        cameras = []
        
        try:
            # Create UDP socket for multicast
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.setblocking(False)
            
            # Bind to any available port
            sock.bind(("0.0.0.0", 0))
            
            # Send probe to multicast address
            probe_msg = self.WS_DISCOVERY_PROBE.replace("probe-msg-id", self._generate_uuid())
            sock.sendto(probe_msg.encode(), (self.WS_DISCOVERY_MULTICAST, self.WS_DISCOVERY_PORT))
            
            # Collect responses
            loop = asyncio.get_event_loop()
            end_time = asyncio.get_event_loop().time() + timeout
            
            found_ips = set()
            
            while asyncio.get_event_loop().time() < end_time:
                try:
                    ready = await asyncio.wait_for(
                        loop.sock_recv(sock, 4096),
                        timeout=0.5
                    )
                    
                    if ready:
                        response = ready.decode('utf-8', errors='ignore')
                        camera = self._parse_probe_response(response)
                        
                        if camera and camera.ip_address not in found_ips:
                            found_ips.add(camera.ip_address)
                            camera.discovery_method = "onvif"
                            cameras.append(camera)
                            
                except asyncio.TimeoutError:
                    continue
                    
            sock.close()
            
        except Exception as e:
            print(f"ONVIF discovery error: {e}")
            
        return cameras
    
    def _generate_uuid(self) -> str:
        """Generate a UUID for WS-Discovery message"""
        import uuid
        return str(uuid.uuid4())
    
    def _parse_probe_response(self, response: str) -> Optional[DiscoveredCamera]:
        """Parse ONVIF probe response"""
        try:
            # Extract IP address from XAddrs
            import re
            
            # Look for IP address in the response
            ip_match = re.search(r'http://(\d+\.\d+\.\d+\.\d+)', response)
            if not ip_match:
                return None
                
            ip_address = ip_match.group(1)
            
            # Try to extract device info from XML
            device_id = f"onvif-{ip_address.replace('.', '-')}"
            name = "ONVIF Camera"
            manufacturer = None
            model = None
            
            # Parse XML for more details
            try:
                root = ET.fromstring(response)
                
                # Extract friendly name
                for elem in root.iter():
                    if 'FriendlyName' in elem.tag or 'Scopes' in elem.tag:
                        text = elem.text or ""
                        if 'Hikvision' in text or 'HIKVISION' in text:
                            manufacturer = "Hikvision"
                        if 'onvif' in text.lower():
                            # Extract name from scopes
                            parts = text.split()
                            for part in parts:
                                if 'name' in part.lower():
                                    name = part.split('/')[-1] or name
                                    break
            except ET.ParseError:
                pass
            
            # Check if it looks like a Hikvision camera
            if not manufacturer:
                if 'hikvision' in response.lower() or 'hik' in response.lower():
                    manufacturer = "Hikvision"
            
            return DiscoveredCamera(
                ip_address=ip_address,
                port=80,
                device_id=device_id,
                name=name,
                manufacturer=manufacturer,
                model=model,
                is_online=True
            )
            
        except Exception as e:
            print(f"Error parsing probe response: {e}")
            return None


class SSDPDiscovery:
    """UPnP/SSDP discovery for network devices"""
    
    SSDP_MULTICAST = "239.255.255.250"
    SSDP_PORT = 1900
    
    SSDP_MSEARCH = """M-SEARCH * HTTP/1.1
Host: 239.255.255.250:1900
Man: "ssdp:discover"
MX: 3
ST: urn:schemas-upnp-org:device:MediaServer:1

"""
    
    async def discover(self, timeout: float = 3.0) -> List[DiscoveredCamera]:
        """Discover devices using SSDP"""
        cameras = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)
            sock.bind(("0.0.0.0", 0))
            
            # Send M-SEARCH
            sock.sendto(self.SSDP_MSEARCH.encode(), (self.SSDP_MULTICAST, self.SSDP_PORT))
            
            # Collect responses
            loop = asyncio.get_event_loop()
            found_ips = set()
            
            while timeout > 0:
                start = asyncio.get_event_loop().time()
                try:
                    ready = await asyncio.wait_for(
                        loop.sock_recv(sock, 4096),
                        timeout=min(0.5, timeout)
                    )
                    
                    if ready:
                        response = ready.decode('utf-8', errors='ignore')
                        camera = self._parse_ssdp_response(response)
                        
                        if camera and camera.ip_address not in found_ips:
                            # Check if it might be a camera
                            if self._is_camera_response(response):
                                found_ips.add(camera.ip_address)
                                camera.discovery_method = "ssdp"
                                cameras.append(camera)
                                
                except asyncio.TimeoutError:
                    pass
                    
                timeout -= (asyncio.get_event_loop().time() - start)
                
            sock.close()
            
        except Exception as e:
            print(f"SSDP discovery error: {e}")
            
        return cameras
    
    def _parse_ssdp_response(self, response: str) -> Optional[DiscoveredCamera]:
        """Parse SSDP response"""
        import re
        
        # Extract IP from Location header
        location_match = re.search(r'LOCATION:\s*http://(\d+\.\d+\.\d+\.\d+)', response, re.IGNORECASE)
        if not location_match:
            return None
            
        ip_address = location_match.group(1)
        device_id = f"ssdp-{ip_address.replace('.', '-')}"
        
        return DiscoveredCamera(
            ip_address=ip_address,
            port=80,
            device_id=device_id,
            name="UPnP Device",
            is_online=True
        )
    
    def _is_camera_response(self, response: str) -> bool:
        """Check if SSDP response is from a camera"""
        camera_keywords = ['camera', 'cam', 'hikvision', 'dahua', 'axis', 'onvif', 'nvt']
        response_lower = response.lower()
        return any(kw in response_lower for kw in camera_keywords)


class HikvisionScanner:
    """Active scanner for Hikvision cameras"""
    
    HIKVISION_PORTS = [80, 81, 82, 8000, 8080, 443]
    HIKVISION_PATHS = [
        "/ISAPI/System/deviceInfo",
        "/SDK/webLogin",
        "/doc/page/login.asp",
        "/",
    ]
    
    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(50)  # Limit concurrent connections
    
    async def scan_subnet(self, subnet: str) -> List[DiscoveredCamera]:
        """Scan a subnet for Hikvision cameras"""
        import ipaddress
        
        try:
            network = ipaddress.ip_network(subnet, strict=False)
            hosts = list(network.hosts())
            
            print(f"Scanning {len(hosts)} hosts in {subnet}...")
            
            tasks = []
            for host in hosts:
                tasks.append(self._check_host(str(host)))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            cameras = []
            for result in results:
                if isinstance(result, DiscoveredCamera):
                    cameras.append(result)
                    
            return cameras
            
        except ValueError as e:
            print(f"Invalid subnet: {e}")
            return []
    
    async def scan_ip_range(self, start_ip: str, end_ip: str) -> List[DiscoveredCamera]:
        """Scan an IP range for Hikvision cameras"""
        import ipaddress
        
        try:
            start = ipaddress.ip_address(start_ip)
            end = ipaddress.ip_address(end_ip)
            
            hosts = []
            current = start
            while current <= end:
                hosts.append(str(current))
                current += 1
            
            print(f"Scanning {len(hosts)} hosts from {start_ip} to {end_ip}...")
            
            tasks = [self._check_host(host) for host in hosts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            cameras = []
            for result in results:
                if isinstance(result, DiscoveredCamera):
                    cameras.append(result)
                    
            return cameras
            
        except ValueError as e:
            print(f"Invalid IP range: {e}")
            return []
    
    async def _check_host(self, ip: str) -> Optional[DiscoveredCamera]:
        """Check if a host is a Hikvision camera"""
        async with self.semaphore:
            for port in self.HIKVISION_PORTS:
                camera = await self._probe_host(ip, port)
                if camera:
                    return camera
            return None
    
    async def _probe_host(self, ip: str, port: int) -> Optional[DiscoveredCamera]:
        """Probe a specific host:port for Hikvision camera"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # Try common Hikvision paths
                for path in self.HIKVISION_PATHS:
                    try:
                        url = f"http://{ip}:{port}{path}"
                        response = await client.get(url)
                        
                        if self._is_hikvision_response(response):
                            return await self._extract_camera_info(ip, port, response, client)
                            
                    except httpx.ConnectError:
                        continue
                    except httpx.TimeoutException:
                        continue
                        
        except Exception:
            pass
            
        return None
    
    def _is_hikvision_response(self, response: httpx.Response) -> bool:
        """Check if response is from a Hikvision device"""
        content = response.text.lower()
        headers = dict(response.headers)
        
        hikvision_indicators = [
            'hikvision',
            'hik-web',
            'net-dvr',
            'net-hdvr',
            'ds-',
            'isapi',
            'hik_us',
            '<vendorname>hikvision</vendorname>',
        ]
        
        # Check response body
        if any(indicator in content for indicator in hikvision_indicators):
            return True
            
        # Check server header
        server = headers.get('server', '').lower()
        if 'hikvision' in server or 'dvrdvs' in server:
            return True
            
        # Check WWW-Authenticate header (for 401 responses)
        auth = headers.get('www-authenticate', '').lower()
        if 'hikvision' in auth or 'basic realm' in auth:
            return True
            
        return False
    
    async def _extract_camera_info(
        self, 
        ip: str, 
        port: int, 
        response: httpx.Response,
        client: httpx.AsyncClient
    ) -> DiscoveredCamera:
        """Extract camera information from Hikvision device"""
        device_id = f"hikvision-{ip.replace('.', '-')}-{port}"
        name = f"Hikvision Camera ({ip})"
        manufacturer = "Hikvision"
        model = None
        firmware = None
        mac_address = None
        
        # Try to get detailed info from ISAPI
        try:
            isapi_url = f"http://{ip}:{port}/ISAPI/System/deviceInfo"
            isapi_response = await client.get(isapi_url)
            
            if isapi_response.status_code == 200:
                content = isapi_response.text
                
                # Parse XML response
                try:
                    root = ET.fromstring(content)
                    
                    for elem in root.iter():
                        tag = elem.tag.lower()
                        if 'devicename' in tag or 'device name' in tag:
                            name = elem.text or name
                        elif 'model' in tag and 'modeldescription' not in tag:
                            model = elem.text
                        elif 'firmwareversion' in tag or 'firmware' in tag:
                            firmware = elem.text
                        elif 'macaddress' in tag or 'mac' in tag:
                            mac_address = elem.text
                            
                except ET.ParseError:
                    # Try regex parsing for non-XML responses
                    import re
                    model_match = re.search(r'<model>([^<]+)</model>', content, re.IGNORECASE)
                    if model_match:
                        model = model_match.group(1)
                        
        except Exception:
            pass
        
        # Generate RTSP URLs
        rtsp_urls = {
            "main": f"rtsp://{ip}:554/Streaming/Channels/101",
            "sub": f"rtsp://{ip}:554/Streaming/Channels/102"
        }
        
        http_urls = {
            "web": f"http://{ip}:{port}",
            "snapshot": f"http://{ip}:{port}/ISAPI/Streaming/channels/101/picture",
        }
        
        return DiscoveredCamera(
            ip_address=ip,
            port=554,  # RTSP port
            device_id=device_id,
            name=name,
            manufacturer=manufacturer,
            model=model,
            firmware_version=firmware,
            mac_address=mac_address,
            discovery_method="scan",
            is_online=True,
            rtsp_urls=rtsp_urls,
            http_urls=http_urls
        )


class CameraDiscovery:
    """Main camera discovery coordinator"""
    
    def __init__(self):
        self.onvif = ONVIFDiscovery()
        self.ssdp = SSDPDiscovery()
        self.scanner = HikvisionScanner()
    
    async def discover_all(self, subnet: Optional[str] = None) -> List[DiscoveredCamera]:
        """Run all discovery methods"""
        cameras = []
        found_ips = set()
        
        print("=" * 60)
        print("Hikvision Camera Discovery")
        print("=" * 60)
        
        # Method 1: ONVIF WS-Discovery
        print("\n[1/3] Running ONVIF WS-Discovery...")
        try:
            onvif_cameras = await self.onvif.discover(timeout=3.0)
            for cam in onvif_cameras:
                if cam.ip_address not in found_ips:
                    found_ips.add(cam.ip_address)
                    cameras.append(cam)
                    print(f"  ✓ Found: {cam.ip_address} ({cam.name})")
            print(f"  Found {len(onvif_cameras)} camera(s) via ONVIF")
        except Exception as e:
            print(f"  ✗ ONVIF discovery failed: {e}")
        
        # Method 2: SSDP
        print("\n[2/3] Running UPnP/SSDP discovery...")
        try:
            ssdp_cameras = await self.ssdp.discover(timeout=3.0)
            for cam in ssdp_cameras:
                if cam.ip_address not in found_ips:
                    found_ips.add(cam.ip_address)
                    cameras.append(cam)
                    print(f"  ✓ Found: {cam.ip_address} ({cam.name})")
            print(f"  Found {len(ssdp_cameras)} device(s) via SSDP")
        except Exception as e:
            print(f"  ✗ SSDP discovery failed: {e}")
        
        # Method 3: Network scan (if subnet provided)
        if subnet:
            print(f"\n[3/3] Scanning subnet {subnet}...")
            try:
                scanned_cameras = await self.scanner.scan_subnet(subnet)
                for cam in scanned_cameras:
                    if cam.ip_address not in found_ips:
                        found_ips.add(cam.ip_address)
                        cameras.append(cam)
                        print(f"  ✓ Found: {cam.ip_address} ({cam.name})")
                print(f"  Found {len(scanned_cameras)} camera(s) via network scan")
            except Exception as e:
                print(f"  ✗ Network scan failed: {e}")
        else:
            print("\n[3/3] Skipping network scan (no subnet provided)")
            print("      Use --subnet to enable full network scanning")
        
        return cameras
    
    def get_local_subnet(self) -> Optional[str]:
        """Auto-detect local subnet"""
        try:
            # Get local IP address
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0)
            try:
                # Connect to a public DNS server to get local IP
                sock.connect(('8.8.8.8', 1))
                local_ip = sock.getsockname()[0]
            finally:
                sock.close()
            
            # Convert to /24 subnet
            ip_parts = local_ip.split('.')
            subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
            return subnet
            
        except Exception:
            return None


def format_output(cameras: List[DiscoveredCamera], output_format: str = "table") -> str:
    """Format camera list for output"""
    if output_format == "json":
        return json.dumps([c.to_dict() for c in cameras], indent=2)
    
    elif output_format == "csv":
        lines = ["IP Address,Port,Device ID,Name,Manufacturer,Model,MAC Address,Discovery Method"]
        for cam in cameras:
            lines.append(f"{cam.ip_address},{cam.port},{cam.device_id},{cam.name},{cam.manufacturer or ''},{cam.model or ''},{cam.mac_address or ''},{cam.discovery_method}")
        return "\n".join(lines)
    
    else:  # table
        if not cameras:
            return "No cameras found."
        
        lines = []
        lines.append("\n" + "=" * 100)
        lines.append(f"{'IP Address':<18} {'Port':<6} {'Manufacturer':<12} {'Model':<20} {'Discovery':<10} {'Name'}")
        lines.append("-" * 100)
        
        for cam in cameras:
            model = (cam.model or "Unknown")[:18]
            lines.append(f"{cam.ip_address:<18} {cam.port:<6} {cam.manufacturer or 'Unknown':<12} {model:<20} {cam.discovery_method:<10} {cam.name}")
        
        lines.append("=" * 100)
        lines.append(f"\nTotal cameras found: {len(cameras)}")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Discover Hikvision cameras on the local network",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Quick discovery using ONVIF/SSDP
  %(prog)s --subnet 192.168.1.0/24   # Full network scan
  %(prog)s --auto-scan               # Auto-detect subnet and scan
  %(prog)s --json                    # Output as JSON
  %(prog)s --register 1              # Register found cameras to workshop ID 1
        """
    )
    
    parser.add_argument("--subnet", help="Subnet to scan (e.g., 192.168.1.0/24)")
    parser.add_argument("--ip-range", help="IP range to scan (e.g., 192.168.1.1-192.168.1.254)")
    parser.add_argument("--auto-scan", action="store_true", help="Auto-detect local subnet and scan")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    parser.add_argument("--register", type=int, metavar="WORKSHOP_ID", help="Register cameras to workshop (requires backend API)")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API URL")
    parser.add_argument("--token", help="API authentication token")
    
    args = parser.parse_args()
    
    discovery = CameraDiscovery()
    
    # Determine subnet
    subnet = args.subnet
    if args.auto_scan and not subnet:
        subnet = discovery.get_local_subnet()
        if subnet:
            print(f"Auto-detected subnet: {subnet}")
        else:
            print("Could not auto-detect subnet")
    
    # Run discovery
    async def run():
        if args.ip_range:
            start, end = args.ip_range.split('-')
            cameras = await discovery.scanner.scan_ip_range(start.strip(), end.strip())
        else:
            cameras = await discovery.discover_all(subnet)
        
        return cameras
    
    cameras = asyncio.run(run())
    
    # Output results
    output_format = "json" if args.json else ("csv" if args.csv else "table")
    print(format_output(cameras, output_format))
    
    # Register cameras if requested
    if args.register and cameras:
        print(f"\n\nRegistering {len(cameras)} camera(s) to workshop {args.register}...")
        # This would integrate with your backend API
        print("(Registration not implemented in standalone script)")
        print(f"Use the backend API to register: POST {args.api_url}/api/v1/cameras/register")
    
    # Print RTSP URLs
    if cameras and output_format == "table":
        print("\n\nRTSP Stream URLs (default admin/password):")
        print("-" * 80)
        for cam in cameras:
            rtsp = cam.get_rtsp_url()
            print(f"{cam.ip_address}: {rtsp}")
        print("\nNote: Replace 'admin' and empty password with actual credentials")


if __name__ == "__main__":
    main()
