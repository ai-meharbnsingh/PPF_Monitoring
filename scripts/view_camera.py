#!/usr/bin/env python3
"""
Hikvision Camera Viewer Script

View live stream from Hikvision IP camera using ffplay.

Usage:
    python view_camera.py                    # View with default settings
    python view_camera.py --ip 192.168.29.173 --password admin123
    python view_camera.py --channel 102      # View sub-stream (lower quality)
    python view_camera.py --transport udp    # Use UDP instead of TCP

Author: PPF Monitoring Team
"""

import argparse
import subprocess
import sys
import os


def check_ffplay():
    """Check if ffplay is installed"""
    try:
        result = subprocess.run(
            ["ffplay", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_rtsp_url(ip, username, password, channel, stream_type="main"):
    """Build RTSP URL for Hikvision camera"""
    # Channel mapping: 101 = main stream, 102 = sub stream
    if stream_type == "sub":
        channel = "102"
    else:
        channel = "101"
    
    if password:
        return f"rtsp://{username}:{password}@{ip}:554/Streaming/Channels/{channel}"
    else:
        return f"rtsp://{username}@{ip}:554/Streaming/Channels/{channel}"


def view_camera(ip, username, password, channel, transport, window_title, fullscreen):
    """Launch ffplay to view camera stream"""
    
    if not check_ffplay():
        print("❌ Error: ffplay not found!")
        print()
        print("Please install ffmpeg:")
        print("  macOS:   brew install ffmpeg")
        print("  Ubuntu:  sudo apt-get install ffmpeg")
        print("  Windows: choco install ffmpeg  or download from ffmpeg.org")
        return 1
    
    # Build RTSP URL
    rtsp_url = get_rtsp_url(ip, username, password, channel, "main" if channel == "101" else "sub")
    
    print("=" * 60)
    print("🎥 Hikvision Camera Viewer")
    print("=" * 60)
    print(f"Camera IP:    {ip}")
    print(f"Username:     {username}")
    print(f"Password:     {'*' * len(password) if password else '(empty)'}")
    print(f"Stream:       {'Main (High Quality)' if channel == '101' else 'Sub (Lower Quality)'}")
    print(f"Transport:    {transport.upper()}")
    print(f"RTSP URL:     {rtsp_url.replace(password, '*' * len(password)) if password else rtsp_url}")
    print("=" * 60)
    print()
    print("Controls:")
    print("  F           - Toggle fullscreen")
    print("  Q / ESC     - Quit")
    print("  Arrow keys  - Seek (if recorded)")
    print("  Space       - Pause (if supported)")
    print()
    print("Starting stream... (Press Q to quit)")
    print()
    
    # Build ffplay command
    cmd = [
        "ffplay",
        "-rtsp_transport", transport,
        "-i", rtsp_url,
        "-window_title", window_title,
        "-vf", "scale=1280:720",  # Default scale to 720p
    ]
    
    if fullscreen:
        cmd.append("-fs")
    
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Stream stopped by user")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="View Hikvision camera stream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # View discovered camera
  %(prog)s --ip 192.168.29.173                # Specific IP
  %(prog)s --password admin123                # With password
  %(prog)s --channel 102                      # Sub-stream (mobile quality)
  %(prog)s --fullscreen                       # Fullscreen mode
  %(prog)s --transport tcp                    # Force TCP transport
        """
    )
    
    parser.add_argument("--ip", default="192.168.29.173",
                        help="Camera IP address (default: 192.168.29.173)")
    parser.add_argument("--username", default="admin",
                        help="Camera username (default: admin)")
    parser.add_argument("--password", default="",
                        help="Camera password (default: empty)")
    parser.add_argument("--channel", choices=["101", "102"], default="101",
                        help="Stream channel: 101=main (HD), 102=sub (SD) (default: 101)")
    parser.add_argument("--transport", choices=["tcp", "udp"], default="tcp",
                        help="RTSP transport protocol (default: tcp)")
    parser.add_argument("--fullscreen", "-f", action="store_true",
                        help="Start in fullscreen mode")
    parser.add_argument("--title", default="Hikvision Camera",
                        help="Window title")
    
    args = parser.parse_args()
    
    return view_camera(
        ip=args.ip,
        username=args.username,
        password=args.password,
        channel=args.channel,
        transport=args.transport,
        window_title=args.title,
        fullscreen=args.fullscreen
    )


if __name__ == "__main__":
    sys.exit(main())
