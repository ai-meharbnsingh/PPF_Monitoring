#!/usr/bin/env python3
"""
WiFi Configuration Portal for Raspberry Pi - Version 2
Handles IP changes and shows new IP after connection
"""

import subprocess
import json
import re
import os
import time
import threading
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
PORT = 8080
HOST = '0.0.0.0'

# Global state for tracking connection progress
connection_state = {
    'in_progress': False,
    'target_ssid': None,
    'start_time': None,
    'old_ip': None,
    'status': 'idle',  # idle, connecting, connected, failed
    'message': '',
    'new_ip': None
}

# Hostname for mDNS access
HOSTNAME = 'piwifi'


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


def get_wifi_interface():
    """Get the WiFi interface name"""
    returncode, stdout, _ = run_cmd("iw dev | grep Interface | awk '{print $2}'")
    if returncode == 0 and stdout.strip():
        return stdout.strip().split('\n')[0]
    for iface in ['wlan0', 'wlan1', 'wlp2s0']:
        if run_cmd(f"ip link show {iface}")[0] == 0:
            return iface
    return None


def get_current_ip():
    """Get current IP address of WiFi interface"""
    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return None
    
    # Try multiple methods
    returncode, stdout, _ = run_cmd(f"ip addr show {wifi_iface} | grep 'inet ' | awk '{{print $2}}' | cut -d'/' -f1")
    if returncode == 0 and stdout.strip():
        return stdout.strip().split('\n')[0]
    
    # Fallback
    returncode, stdout, _ = run_cmd("hostname -I | awk '{print $1}'")
    if returncode == 0:
        return stdout.strip()
    return None


def get_hostname_ip():
    """Get mDNS hostname"""
    return f"{HOSTNAME}.local"


def check_connection_status():
    """Check if connected to WiFi and get details"""
    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return {'connected': False, 'ssid': None, 'ip': None}
    
    # Check if we have an IP
    ip = get_current_ip()
    
    # Check if connected via nmcli
    returncode, stdout, _ = run_cmd("nmcli connection show --active | grep -i wifi")
    
    if returncode == 0 and ip:
        # Get SSID
        _, ssid_out, _ = run_cmd("nmcli -t -f NAME connection show --active | head -1")
        ssid = ssid_out.strip()
        
        return {
            'connected': True,
            'ssid': ssid,
            'ip': ip,
            'interface': wifi_iface,
            'hostname': get_hostname_ip()
        }
    
    return {
        'connected': False,
        'ssid': None,
        'ip': ip,
        'interface': wifi_iface,
        'hostname': get_hostname_ip()
    }


@app.route('/')
def index():
    """Main page"""
    return render_template('wifi_portal_v2.html', hostname=HOSTNAME)


@app.route('/api/status')
def get_status():
    """Get current connection status including connection progress"""
    status = check_connection_status()
    
    # Include connection state
    global connection_state
    response = {
        **status,
        'connection_progress': {
            'in_progress': connection_state['in_progress'],
            'target_ssid': connection_state['target_ssid'],
            'status': connection_state['status'],
            'message': connection_state['message'],
            'new_ip': connection_state['new_ip'],
            'old_ip': connection_state['old_ip']
        },
        'hostname': get_hostname_ip()
    }
    
    return jsonify(response)


@app.route('/api/scan')
def scan_networks():
    """Scan for available WiFi networks"""
    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        return jsonify({'error': 'No WiFi interface found'}), 400
    
    # Trigger a scan
    run_cmd(f"sudo iw dev {wifi_iface} scan >/dev/null 2>&1", timeout=10)
    
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
    
    networks.sort(key=lambda x: x['signal'], reverse=True)
    return jsonify({'networks': networks})


def connection_worker(ssid, password, old_ip):
    """Background worker to handle connection and detect new IP"""
    global connection_state
    
    connection_state['in_progress'] = True
    connection_state['target_ssid'] = ssid
    connection_state['status'] = 'connecting'
    connection_state['message'] = f'Connecting to {ssid}...'
    connection_state['old_ip'] = old_ip
    connection_state['new_ip'] = None
    
    # Delete existing connection
    run_cmd(f"sudo nmcli connection delete '{ssid}' 2>/dev/null")
    time.sleep(1)
    
    # Attempt connection
    if password:
        cmd = f"sudo nmcli device wifi connect '{ssid}' password '{password}'"
    else:
        cmd = f"sudo nmcli device wifi connect '{ssid}'"
    
    returncode, stdout, stderr = run_cmd(cmd, timeout=30)
    
    if returncode == 0:
        connection_state['status'] = 'connected'
        connection_state['message'] = 'Connection successful! Getting new IP...'
        
        # Wait for DHCP to assign IP (up to 30 seconds)
        for i in range(30):
            time.sleep(1)
            new_ip = get_current_ip()
            
            # Check if IP changed
            if new_ip and new_ip != old_ip:
                connection_state['new_ip'] = new_ip
                connection_state['message'] = f'Connected! New IP: {new_ip}'
                break
            elif new_ip and i > 5:
                # IP might be same if reconnecting to same network
                connection_state['new_ip'] = new_ip
                connection_state['message'] = f'Connected! IP: {new_ip}'
                break
        else:
            # Timeout - try to get any IP
            new_ip = get_current_ip()
            connection_state['new_ip'] = new_ip
            connection_state['message'] = f'Connected! IP: {new_ip}'
    else:
        connection_state['status'] = 'failed'
        error_msg = stderr if stderr else stdout
        connection_state['message'] = f'Failed: {error_msg}'
    
    connection_state['in_progress'] = False


@app.route('/api/connect', methods=['POST'])
def connect_wifi():
    """Connect to a WiFi network - starts background worker"""
    global connection_state
    
    data = request.json
    ssid = data.get('ssid', '').strip()
    password = data.get('password', '')
    
    if not ssid:
        return jsonify({'success': False, 'error': 'SSID is required'}), 400
    
    # Get current IP before changing
    old_ip = get_current_ip()
    
    # Reset connection state
    connection_state = {
        'in_progress': True,
        'target_ssid': ssid,
        'start_time': time.time(),
        'old_ip': old_ip,
        'status': 'connecting',
        'message': f'Starting connection to {ssid}...',
        'new_ip': None
    }
    
    # Start connection in background thread
    thread = threading.Thread(
        target=connection_worker,
        args=(ssid, password, old_ip)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Connection started',
        'old_ip': old_ip,
        'note': 'Connection in progress. Check /api/status for updates.'
    })


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
    print("WiFi Configuration Portal v2")
    print("=" * 60)
    print(f"Hostname: {get_hostname_ip()}")
    print(f"Current IP: {get_current_ip()}")
    print(f"Access: http://{get_current_ip()}:{PORT}")
    print(f"        http://{get_hostname_ip()}:{PORT}")
    print("=" * 60)
    
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
