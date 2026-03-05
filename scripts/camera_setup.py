#!/usr/bin/env python3
"""
Camera Setup & Viewer Helper

Helps configure and view Hikvision cameras.

Usage:
    python camera_setup.py scan                    # Scan network for cameras
    python camera_setup.py view --ip 192.168.1.64  # View camera at IP
    python camera_setup.py setup                   # Interactive setup

Author: PPF Monitoring Team
"""

import argparse
import asyncio
import subprocess
import sys
import os


async def scan_for_cameras():
    """Scan network for Hikvision cameras"""
    print("=" * 60)
    print("🔍 Scanning for Hikvision Cameras")
    print("=" * 60)
    print()
    
    # Import discovery module
    sys.path.insert(0, os.path.dirname(__file__))
    from discover_hikvision_cameras import HikvisionScanner
    
    scanner = HikvisionScanner(timeout=1.5)
    
    # Scan current subnet
    cameras = await scanner.scan_subnet('192.168.29.0/24')
    
    if cameras:
        print(f"\n✅ Found {len(cameras)} camera(s):")
        for cam in cameras:
            print(f"  📷 {cam.ip_address} - {cam.name}")
            print(f"     RTSP: {cam.rtsp_urls.get('main', 'N/A')}")
    else:
        print("\n❌ No Hikvision cameras found on 192.168.29.0/24")
        print()
        print("Possible reasons:")
        print("  - Camera is powered off")
        print("  - Camera is on factory default subnet (192.168.1.x)")
        print("  - Camera is not connected to network")
        print()
        print("Try factory default scan:")
        print("  python camera_setup.py scan-factory")
    
    return cameras


def view_camera(ip, username, password, channel):
    """Launch ffplay to view camera"""
    
    # Check ffplay
    try:
        subprocess.run(["ffplay", "-version"], capture_output=True, timeout=3)
    except:
        print("❌ ffplay not found. Install ffmpeg:")
        print("  brew install ffmpeg")
        return 1
    
    # Build URL
    ch = "101" if channel == "main" else "102"
    if password:
        url = f"rtsp://{username}:{password}@{ip}:554/Streaming/Channels/{ch}"
    else:
        url = f"rtsp://{username}@{ip}:554/Streaming/Channels/{ch}"
    
    print("=" * 60)
    print("🎥 Starting Camera Stream")
    print("=" * 60)
    print(f"IP:       {ip}")
    print(f"User:     {username}")
    print(f"Stream:   {channel}")
    print(f"URL:      {url.replace(password, '****') if password else url}")
    print("=" * 60)
    print()
    print("Controls: Q=Quit, F=Fullscreen")
    print()
    
    cmd = [
        "ffplay",
        "-rtsp_transport", "tcp",
        "-i", url,
        "-window_title", f"Hikvision Camera {ip}",
        "-vf", "scale=1280:720"
    ]
    
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Stopped")
        return 0


def interactive_setup():
    """Interactive camera setup"""
    print("=" * 60)
    print("📷 Hikvision Camera Setup")
    print("=" * 60)
    print()
    
    # Step 1: Find camera
    print("Step 1: Finding camera...")
    result = subprocess.run(
        ["python3", os.path.join(os.path.dirname(__file__), "discover_hikvision_cameras.py"), "--auto-scan"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    
    # Step 2: Get IP
    ip = input("Enter camera IP (e.g., 192.168.1.64): ").strip()
    if not ip:
        print("❌ No IP provided")
        return 1
    
    # Step 3: Test connection
    print(f"\nStep 2: Testing connection to {ip}...")
    result = subprocess.run(["ping", "-c", "1", "-W", "2", ip], 
                          capture_output=True)
    if result.returncode != 0:
        print(f"❌ Cannot ping {ip}")
        return 1
    print(f"✅ {ip} is online")
    
    # Step 4: Get credentials
    print("\nStep 3: Camera credentials")
    username = input("Username [admin]: ").strip() or "admin"
    password = input("Password (press Enter if empty): ").strip()
    
    # Step 5: Test stream
    print("\nStep 4: Testing stream...")
    ch = input("Stream (1=main HD, 2=sub SD) [1]: ").strip() or "1"
    channel = "main" if ch == "1" else "sub"
    
    return view_camera(ip, username, password, channel)


def main():
    parser = argparse.ArgumentParser(
        description="Camera Setup & Viewer Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan                     # Scan network for cameras
  %(prog)s view                     # View camera (interactive)
  %(prog)s view --ip 192.168.1.64   # View specific camera
  %(prog)s setup                    # Interactive setup wizard
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for cameras")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View camera stream")
    view_parser.add_argument("--ip", default="192.168.29.173", help="Camera IP")
    view_parser.add_argument("--username", default="admin", help="Username")
    view_parser.add_argument("--password", default="", help="Password")
    view_parser.add_argument("--channel", choices=["main", "sub"], default="main", help="Stream quality")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Interactive setup")
    
    args = parser.parse_args()
    
    if args.command == "scan":
        cameras = asyncio.run(scan_for_cameras())
        return 0 if cameras else 1
    
    elif args.command == "view":
        return view_camera(args.ip, args.username, args.password, args.channel)
    
    elif args.command == "setup":
        return interactive_setup()
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
