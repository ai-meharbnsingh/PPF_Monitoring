#!/usr/bin/env python3
"""
WiFi Configuration Portal for Raspberry Pi
Allows users to scan and connect to WiFi networks via web interface
"""

import subprocess
import json
import re
import os
from flask import Flask, render_template, jsonify, request, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
PORT = 80  # Standard HTTP port (requires sudo) or use 8080
HOST = '0.0.0.0'  # Listen on all interfaces


def run_cmd(cmd, timeout=30):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def check_nmcli():
    """Check if NetworkManager is available"""
    return run_cmd("which nmcli")[0] == 0


def get_wifi_interface():
    """Get the WiFi interface name"""
    returncode, stdout, _ = run_cmd("iw dev | grep Interface | awk '{print $2}'")
    if returncode == 0 and stdout.strip():
        return stdout.strip().split('\n')[0]
    # Fallback methods
    for iface in ['wlan0', 'wlan1', 'wlp2s0']:
        if run_cmd(f"ip link show {iface}")[0] == 0:
            return iface
    return None


@app.route('/')
def index():
    """Main page"""
    return render_template('wifi_portal.html')


@app.route('/api/status')
def get_status():
    """Get current connection status"""
    wifi_iface = get_wifi_interface()
    
    # Get current connection info
    returncode, stdout, _ = run_cmd("nmcli connection show --active | grep -i wifi")
    
    current_ssid = None
    current_ip = None
    is_connected = False
    
    if returncode == 0:
        is_connected = True
        # Get SSID
        _, ssid_out, _ = run_cmd("nmcli -t -f NAME connection show --active | head -1")
        current_ssid = ssid_out.strip()
        
        # Get IP
        _, ip_out, _ = run_cmd("hostname -I | awk '{print $1}'")
        current_ip = ip_out.strip()
    
    return jsonify({
        'connected': is_connected,
        'ssid': current_ssid,
        'ip': current_ip,
        'interface': wifi_iface
    })


@app.route('/api/scan')
def scan_networks():
    """Scan for available WiFi networks"""
    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return jsonify({'error': 'No WiFi interface found'}), 400
    
    # Trigger a scan first
    run_cmd(f"sudo iw dev {wifi_iface} scan >/dev/null 2>&1", timeout=10)
    
    # Get list of networks using nmcli
    networks = []
    returncode, stdout, stderr = run_cmd(
        "nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list 2>/dev/null | head -20"
    )
    
    if returncode != 0:
        # Fallback to iw
        returncode, stdout, _ = run_cmd(
            f"sudo iw dev {wifi_iface} scan 2>/dev/null | grep -E 'SSID|signal' | head -40"
        )
        if returncode == 0:
            # Parse iw output
            lines = stdout.strip().split('\n')
            seen = set()
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    signal_match = re.search(r'signal:\s*(-?\d+)', lines[i])
                    ssid_match = re.search(r'SSID:\s*(.+)', lines[i+1])
                    if ssid_match:
                        ssid = ssid_match.group(1).strip()
                        signal = int(signal_match.group(1)) if signal_match else -70
                        if ssid and ssid not in seen:
                            seen.add(ssid)
                            networks.append({
                                'ssid': ssid,
                                'signal': signal,
                                'security': 'Unknown'
                            })
    else:
        # Parse nmcli output
        seen = set()
        for line in stdout.strip().split('\n'):
            parts = line.split(':')
            if len(parts) >= 3:
                ssid = parts[0]
                signal = parts[1] if parts[1] else '0'
                security = parts[2] if parts[2] else 'None'
                
                if ssid and ssid not in seen:
                    seen.add(ssid)
                    try:
                        signal_int = int(signal)
                    except:
                        signal_int = 50
                    networks.append({
                        'ssid': ssid,
                        'signal': signal_int,
                        'security': 'WPA2' if security and security != 'none' else 'Open'
                    })
    
    # Sort by signal strength
    networks.sort(key=lambda x: x['signal'], reverse=True)
    
    return jsonify({'networks': networks})


@app.route('/api/connect', methods=['POST'])
def connect_wifi():
    """Connect to a WiFi network"""
    data = request.json
    ssid = data.get('ssid', '').strip()
    password = data.get('password', '')
    
    if not ssid:
        return jsonify({'success': False, 'error': 'SSID is required'}), 400
    
    # First, delete any existing connection with this SSID
    run_cmd(f"sudo nmcli connection delete '{ssid}' 2>/dev/null")
    
    # Connect using nmcli
    if password:
        cmd = f"sudo nmcli device wifi connect '{ssid}' password '{password}'"
    else:
        cmd = f"sudo nmcli device wifi connect '{ssid}'"
    
    returncode, stdout, stderr = run_cmd(cmd, timeout=30)
    
    if returncode == 0:
        return jsonify({
            'success': True, 
            'message': f'Successfully connected to {ssid}',
            'ssid': ssid
        })
    else:
        error_msg = stderr if stderr else stdout
        return jsonify({
            'success': False, 
            'error': f'Failed to connect: {error_msg}'
        }), 400


@app.route('/api/disconnect', methods=['POST'])
def disconnect_wifi():
    """Disconnect from current WiFi"""
    wifi_iface = get_wifi_interface()
    if wifi_iface:
        run_cmd(f"sudo nmcli device disconnect {wifi_iface}")
        return jsonify({'success': True, 'message': 'Disconnected'})
    return jsonify({'success': False, 'error': 'No interface'}), 400


@app.route('/api/reboot', methods=['POST'])
def reboot_pi():
    """Reboot the Raspberry Pi"""
    run_cmd("sudo reboot &")
    return jsonify({'success': True, 'message': 'Rebooting...'})


if __name__ == '__main__':
    print("=" * 60)
    print("WiFi Configuration Portal")
    print("=" * 60)
    print(f"Access the portal at: http://<raspberry-pi-ip>:{PORT}")
    print("=" * 60)
    
    # Check if running as root for port 80
    if PORT == 80 and os.geteuid() != 0:
        print("\nWarning: Port 80 requires root privileges.")
        print("Run with: sudo python3 wifi_server.py")
        print("Or change PORT to 8080 in the script")
        PORT = 8080
        print(f"\nUsing port {PORT} instead...")
    
    app.run(host=HOST, port=PORT, debug=False)
