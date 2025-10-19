#!/usr/bin/env python3
"""
ZKTeco Connection Test Script

This script helps diagnose ZKTeco device connection issues.
Run this from your Django project root directory.

Usage:
    python test_zkteco_connection.py 192.168.68.3
    python test_zkteco_connection.py 192.168.68.3 4370
"""

import sys
import os
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from hrm.zkteco_utils import test_device_connection, diagnose_device_issues

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_zkteco_connection.py <ip_address> [port]")
        print("Example: python test_zkteco_connection.py 192.168.68.3")
        print("Example: python test_zkteco_connection.py 192.168.68.3 4370")
        sys.exit(1)
    
    ip_address = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 4370
    
    print(f"Testing ZKTeco device connection to {ip_address}:{port}")
    print("=" * 60)
    
    # Run basic connection test
    print("\n1. Basic Connection Test:")
    print("-" * 30)
    result = test_device_connection(ip_address, port)
    
    if result['connected']:
        print("✅ Connection successful!")
        if result['device_info']:
            print("Device Information:")
            for key, value in result['device_info'].items():
                print(f"  {key}: {value}")
    else:
        print("❌ Connection failed!")
        if result['error']:
            print(f"Error: {result['error']}")
    
    # Run comprehensive diagnostics
    print("\n2. Comprehensive Diagnostics:")
    print("-" * 30)
    diagnostics = diagnose_device_issues(ip_address, port)
    
    # Network test results
    print("\nNetwork Tests:")
    if diagnostics['network_test'].get('ping', False):
        print("✅ Ping test: PASSED")
    else:
        print("❌ Ping test: FAILED")
        if 'ping_error' in diagnostics['network_test']:
            print(f"   Error: {diagnostics['network_test']['ping_error']}")
    
    if diagnostics['port_test'].get('reachable', False):
        print("✅ Port connectivity: PASSED")
    else:
        print("❌ Port connectivity: FAILED")
        if 'error' in diagnostics['port_test']:
            print(f"   Error: {diagnostics['port_test']['error']}")
    
    # Device test results
    print("\nDevice Protocol Test:")
    device_test = diagnostics['device_test']
    if device_test['connected']:
        print("✅ Device protocol: PASSED")
        if 'protocol_version' in device_test.get('diagnostics', {}):
            print(f"   Protocol version: {device_test['diagnostics']['protocol_version']}")
    else:
        print("❌ Device protocol: FAILED")
        if device_test.get('error'):
            print(f"   Error: {device_test['error']}")
    
    # Recommendations
    if diagnostics['recommendations']:
        print("\nRecommendations:")
        for i, rec in enumerate(diagnostics['recommendations'], 1):
            print(f"{i}. {rec}")
    else:
        print("\n✅ All tests passed! Your device should be working correctly.")
    
    print("\n" + "=" * 60)
    print("Test completed.")

if __name__ == "__main__":
    main()
