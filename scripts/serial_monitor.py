#!/usr/bin/env python3
"""
Serial Monitor for ESP32 PPF Device
Usage: python3 scripts/serial_monitor.py
Press Ctrl+C to exit
"""

import serial
import sys

def main():
    PORT = '/dev/cu.usbserial-0001'  # Device 1
    BAUD = 115200
    
    print('=' * 60)
    print('PPF ESP32 Serial Monitor')
    print('=' * 60)
    print(f'Port: {PORT}')
    print(f'Baud: {BAUD}')
    print('')
    print('Press Ctrl+C to exit')
    print('-' * 60)
    
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print('Connected! Reading device output...\n')
        
        while True:
            data = ser.readline()
            if data:
                try:
                    line = data.decode('utf-8', errors='replace').strip()
                    if line:
                        print(line)
                except:
                    pass
                    
    except KeyboardInterrupt:
        print('\n' + '-' * 60)
        print('Exiting...')
    except Exception as e:
        print(f'Error: {e}')
        print(f'\nMake sure device is connected to: {PORT}')
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == '__main__':
    main()
