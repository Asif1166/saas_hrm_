from zk import ZK

conn = ZK('192.168.68.3', port=4370, timeout=10)

try:
    print('Connecting...')
    zk = conn.connect()
    print('Connected!')
    
    # Get device info
    print(f'Firmware Version: {zk.get_firmware_version()}')
    print(f'Device Name: {zk.get_device_name()}')
    
    # Get users
    users = zk.get_users()
    print(f'Total Users: {len(users)}')
    
    # Get attendance
    attendance = zk.get_attendance()
    print(f'Total Records: {len(attendance)}')
    
    for record in attendance[:5]:  # Show first 5 records
        print(f'  {record.user_id} - {record.timestamp}')
    
    zk.disconnect()
    
except Exception as e:
    print(f'Error: {e}')
    print('\nTrying UDP mode...')
    
    # Try with UDP
    try:
        conn = ZK('192.168.68.3', port=4370, timeout=10, force_udp=True)
        zk = conn.connect()
        print('Connected with UDP!')
        zk.disconnect()
    except Exception as e2:
        print(f'UDP also failed: {e2}')