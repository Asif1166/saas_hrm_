"""
ZKTeco Device Integration for Django using PyZK Library

This module provides a complete integration solution for ZKTeco attendance devices.
Tested and working with F18 device (Ver 6.60).

Requirements:
    pip install pyzk
"""

from zk import ZK, const
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.conf import settings
import logging
import datetime

logger = logging.getLogger(__name__)


class ZKTecoDevice:
    """
    ZKTeco device communication using PyZK library
    """

    def __init__(self, ip_address: str, port: int = 4370, timeout: int = 10, password: int = 0):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.password = password
        self.conn = None
        self.zk = None
        self.is_connected = False

    def connect(self) -> bool:
        """Connect to the ZKTeco device"""
        try:
            logger.info(f"Connecting to ZKTeco device at {self.ip_address}:{self.port}")
            
            self.conn = ZK(
                self.ip_address, 
                port=self.port, 
                timeout=self.timeout,
                password=self.password,
                force_udp=False,
                ommit_ping=False
            )
            
            self.zk = self.conn.connect()
            self.is_connected = True
            
            logger.info(f"Successfully connected to {self.ip_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to device {self.ip_address}: {str(e)}")
            
            # Try with UDP as fallback
            try:
                logger.info("Retrying with UDP protocol...")
                self.conn = ZK(
                    self.ip_address,
                    port=self.port,
                    timeout=self.timeout,
                    password=self.password,
                    force_udp=True,
                    ommit_ping=True
                )
                self.zk = self.conn.connect()
                self.is_connected = True
                logger.info(f"Connected to {self.ip_address} via UDP")
                return True
            except Exception as e2:
                logger.error(f"UDP connection also failed: {str(e2)}")
                return False

    def disconnect(self):
        """Disconnect from the device"""
        if self.zk:
            try:
                self.zk.disconnect()
                logger.info("Disconnected from device")
            except Exception as e:
                logger.warning(f"Error during disconnect: {str(e)}")
            finally:
                self.zk = None
                self.conn = None
                self.is_connected = False

    def get_device_info(self) -> Dict:
        """Get device information"""
        if not self.is_connected:
            return {}

        info = {}
        try:
            info['firmware_version'] = self.zk.get_firmware_version()
            info['serialnumber'] = self.zk.get_serialnumber()
            info['platform'] = self.zk.get_platform()
            info['device_name'] = self.zk.get_device_name()
            info['mac'] = self.zk.get_mac()
            
            try:
                info['face_version'] = self.zk.get_face_version()
            except:
                pass
                
            try:
                info['fp_version'] = self.zk.get_fp_version()
            except:
                pass
                
            logger.info(f"Device info retrieved: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get device info: {str(e)}")
            return info

    def get_users(self) -> List[Dict]:
        """Get all users from the device"""
        if not self.is_connected:
            return []

        try:
            users = self.zk.get_users()
            
            user_list = []
            for user in users:
                user_list.append({
                    'uid': user.uid,
                    'user_id': user.user_id,
                    'name': user.name,
                    'privilege': user.privilege,
                    'password': user.password if hasattr(user, 'password') else '',
                    'group_id': user.group_id if hasattr(user, 'group_id') else '',
                    'card': user.card if hasattr(user, 'card') else 0,
                })
            
            logger.info(f"Retrieved {len(user_list)} users from device")
            return user_list
            
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    def get_attendance(self, start_date: datetime.date = None, end_date: datetime.date = None) -> List[Dict]:
        """
        Get attendance records from the device
        
        Note: PyZK gets ALL attendance records. Filter by date in your application.
        """
        if not self.is_connected:
            return []

        try:
            attendance_records = self.zk.get_attendance()
            
            attendance_list = []
            for record in attendance_records:
                # Apply date filter if specified
                if start_date and record.timestamp.date() < start_date:
                    continue
                if end_date and record.timestamp.date() > end_date:
                    continue
                
                attendance_list.append({
                    'user_id': record.user_id,
                    'timestamp': record.timestamp,
                    'status': record.status,  # Verify type
                    'punch': record.punch,    # In/Out direction
                    'uid': record.uid if hasattr(record, 'uid') else None,
                })
            
            logger.info(f"Retrieved {len(attendance_list)} attendance records")
            return attendance_list
            
        except Exception as e:
            logger.error(f"Failed to get attendance: {str(e)}")
            return []

    def set_user(self, uid: int, name: str, privilege: int = 0, 
                 password: str = '', group_id: str = '', user_id: str = '', 
                 card: int = 0) -> bool:
        """Add or update a user on the device"""
        if not self.is_connected:
            return False

        try:
            self.zk.set_user(
                uid=uid,
                name=name,
                privilege=privilege,
                password=password,
                group_id=group_id,
                user_id=user_id,
                card=card
            )
            logger.info(f"User {name} (UID: {uid}) added/updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set user: {str(e)}")
            return False

    def delete_user(self, uid: int) -> bool:
        """Delete a user from the device"""
        if not self.is_connected:
            return False

        try:
            self.zk.delete_user(uid=uid)
            logger.info(f"User UID {uid} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user: {str(e)}")
            return False

    def clear_attendance(self) -> bool:
        """Clear all attendance records from the device"""
        if not self.is_connected:
            return False

        try:
            self.zk.clear_attendance()
            logger.info("Attendance records cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear attendance: {str(e)}")
            return False

    def enable_device(self) -> bool:
        """Enable device (for normal operation)"""
        if not self.is_connected:
            return False

        try:
            self.zk.enable_device()
            return True
        except Exception as e:
            logger.error(f"Failed to enable device: {str(e)}")
            return False

    def disable_device(self) -> bool:
        """Disable device (for maintenance/data operations)"""
        if not self.is_connected:
            return False

        try:
            self.zk.disable_device()
            return True
        except Exception as e:
            logger.error(f"Failed to disable device: {str(e)}")
            return False

    def restart_device(self) -> bool:
        """Restart the device"""
        if not self.is_connected:
            return False

        try:
            self.zk.restart()
            logger.info("Device restart command sent")
            return True
        except Exception as e:
            logger.error(f"Failed to restart device: {str(e)}")
            return False

    def poweroff_device(self) -> bool:
        """Power off the device"""
        if not self.is_connected:
            return False

        try:
            self.zk.poweroff()
            logger.info("Device poweroff command sent")
            return True
        except Exception as e:
            logger.error(f"Failed to poweroff device: {str(e)}")
            return False

    def test_voice(self, index: int = 0) -> bool:
        """Test device voice/sound"""
        if not self.is_connected:
            return False

        try:
            self.zk.test_voice(index=index)
            return True
        except Exception as e:
            logger.error(f"Failed to test voice: {str(e)}")
            return False


class AttendanceSyncManager:
    """
    Manager class for syncing attendance data with ZKTeco devices
    """

    def __init__(self, device):
        """
        device: Your Django AttendanceDevice model instance
        """
        self.device = device
        self.zk_device = ZKTecoDevice(
            ip_address=device.ip_address,
            port=device.port if hasattr(device, 'port') else 4370,
            timeout=device.timeout if hasattr(device, 'timeout') else 10,
            password=device.password if hasattr(device, 'password') else 0
        )

    def sync_device_info(self) -> bool:
        """Sync device information to database"""
        try:
            if not self.zk_device.connect():
                self.device.is_online = False
                self.device.save()
                return False

            device_info = self.zk_device.get_device_info()
            
            if device_info:
                self.device.serial_number = device_info.get('serialnumber', '')
                self.device.model = device_info.get('device_name', '')
                self.device.firmware_version = device_info.get('firmware_version', '')
                self.device.mac_address = device_info.get('mac', '')
                self.device.platform = device_info.get('platform', '')
                self.device.is_online = True
                self.device.last_sync = timezone.now()
                self.device.save()
                
                logger.info(f"Device info synced for {self.device.name}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to sync device info: {str(e)}")
            self.device.is_online = False
            self.device.save()
            return False
        finally:
            self.zk_device.disconnect()

    def sync_users(self, auto_create: bool = True) -> Dict[str, int]:
        """
        Sync users from device to database
        
        Args:
            auto_create: If True, automatically create employees for unmatched device users
            
        Returns:
            Dictionary with sync statistics: {'synced': int, 'created': int, 'failed': int}
        """
        try:
            if not self.zk_device.connect():
                return {'synced': 0, 'created': 0, 'failed': 0}

            device_users = self.zk_device.get_users()
            synced_count = 0
            created_count = 0
            failed_count = 0

            from .models import Employee
            from django.contrib.auth import get_user_model
            User = get_user_model()

            for device_user in device_users:
                try:
                    employee = None
                    
                    # Strategy 1: Find by device_enrollment_id
                    employee = Employee.objects.filter(
                        organization=self.device.organization,
                        device_enrollment_id=str(device_user['user_id'])
                    ).first()
                    
                    # Strategy 2: Find by employee_id matching device user_id
                    if not employee:
                        employee = Employee.objects.filter(
                            organization=self.device.organization,
                            employee_id=str(device_user['user_id'])
                        ).first()
                    
                    # Strategy 3: Try to match by name
                    if not employee and device_user['name'].strip():
                        name_parts = device_user['name'].strip().split()
                        if name_parts:
                            employee = Employee.objects.filter(
                                organization=self.device.organization,
                                first_name__iexact=name_parts[0],
                                is_active=True
                            ).first()

                    if employee:
                        # Update existing employee with device IDs
                        employee.device_user_id = str(device_user['uid'])
                        employee.device_enrollment_id = str(device_user['user_id'])
                        employee.save()
                        synced_count += 1
                        logger.info(f"✓ Synced user: {device_user['name']} -> {employee.full_name}")
                    
                    elif auto_create:
                        # Create new employee from device user
                        try:
                            # Parse name
                            name_parts = device_user['name'].strip().split()
                            first_name = name_parts[0] if name_parts else device_user['name'][:50]
                            last_name = ' '.join(name_parts[1:])[:50] if len(name_parts) > 1 else ''
                            
                            # Generate unique username
                            base_username = first_name.lower().replace(' ', '')
                            username = base_username
                            counter = 1
                            while User.objects.filter(username=username).exists():
                                username = f"{base_username}{counter}"
                                counter += 1
                            
                            # Generate unique employee_id for organization
                            employee_id = str(device_user['user_id'])
                            original_employee_id = employee_id
                            counter = 1
                            while Employee.objects.filter(
                                organization=self.device.organization,
                                employee_id=employee_id
                            ).exists():
                                employee_id = f"{original_employee_id}_{counter}"
                                counter += 1
                            
                            # Create user account with password
                            password = f"{username}123"  # username + 123
                            user = User.objects.create_user(
                                username=username,
                                password=password,
                                first_name=first_name,
                                last_name=last_name,
                                email=f"{username}@{self.device.organization.name.lower().replace(' ', '')}.local"
                            )
                            
                            # Create employee
                            from datetime import date
                            employee = Employee.objects.create(
                                organization=self.device.organization,
                                user=user,
                                employee_id=employee_id,
                                first_name=first_name,
                                last_name=last_name,
                                hire_date=date.today(),
                                employment_status='active',
                                is_active=True,
                                device_user_id=str(device_user['uid']),
                                device_enrollment_id=str(device_user['user_id']),
                            )
                            
                            created_count += 1
                            logger.info(f"✓ Created employee: {employee.full_name} (ID: {employee_id}, Username: {username}, Password: {password})")
                        
                        except Exception as e:
                            failed_count += 1
                            logger.error(f"✗ Failed to create employee for '{device_user['name']}': {str(e)}")
                    else:
                        logger.warning(f"⚠ No match for device user: {device_user['name']} (ID: {device_user['user_id']}, UID: {device_user['uid']})")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"✗ Error syncing user {device_user.get('name', 'unknown')}: {str(e)}")
                    continue

            logger.info(f"User sync completed: {synced_count} matched, {created_count} created, {failed_count} failed out of {len(device_users)} total")
            
            return {
                'synced': synced_count,
                'created': created_count,
                'failed': failed_count
            }

        except Exception as e:
            logger.error(f"Failed to sync users: {str(e)}")
            return {'synced': 0, 'created': 0, 'failed': 0}
        finally:
            self.zk_device.disconnect()

    def sync_attendance(self, start_date: datetime.date = None, end_date: datetime.date = None) -> int:
        """
        Sync attendance records from device
        Returns number of records synced
        """
        try:
            if not self.zk_device.connect():
                return 0

            if not start_date:
                start_date = datetime.date.today() - datetime.timedelta(days=7)
            if not end_date:
                end_date = datetime.date.today()

            attendance_logs = self.zk_device.get_attendance(start_date, end_date)
            synced_count = 0

            from .models import Employee, AttendanceRecord

            for log in attendance_logs:
                try:
                    # Find employee by device user_id
                    employee = Employee.objects.filter(
                        organization=self.device.organization,
                        device_enrollment_id=str(log['user_id'])
                    ).first()

                    if not employee:
                        # Try by device_user_id (UID)
                        if log.get('uid'):
                            employee = Employee.objects.filter(
                                organization=self.device.organization,
                                device_user_id=str(log['uid'])
                            ).first()

                    if not employee:
                        logger.warning(f"No employee found for device user_id: {log['user_id']}")
                        continue

                    # Get or create attendance record for the day
                    attendance_date = log['timestamp'].date()
                    
                    attendance_record, created = AttendanceRecord.objects.get_or_create(
                        organization=self.device.organization,
                        employee=employee,
                        date=attendance_date,
                        defaults={
                            'device': self.device,
                            'status': 'present',
                            'sync_timestamp': timezone.now(),
                        }
                    )

                    # Determine if this is check-in or check-out
                    # Punch: 0 = Check In, 1 = Check Out, 2 = Break Out, 3 = Break In, etc.
                    punch_time = log['timestamp'].time()
                    

                            # ✅ Append all punch times to notes field
                    current_notes = attendance_record.notes or ""
                    all_times = [t.strip() for t in current_notes.split(",") if t.strip()]
                    time_str = punch_time.strftime("%H:%M:%S")
                    if time_str not in all_times:
                        all_times.append(time_str)
                        attendance_record.notes = ",".join(sorted(all_times))


                    if log['punch'] in [0, 2, 4]:  # Check-in types
                        if not attendance_record.check_in_time or punch_time < attendance_record.check_in_time:
                            attendance_record.check_in_time = punch_time
                            logger.info(f"Updated check-in for {employee.full_name} at {punch_time}")
                    
                    elif log['punch'] in [1, 3, 5]:  # Check-out types
                        if not attendance_record.check_out_time or punch_time > attendance_record.check_out_time:
                            attendance_record.check_out_time = punch_time
                            logger.info(f"Updated check-out for {employee.full_name} at {punch_time}")

                    attendance_record.save()

                    # Calculate working hours
                    if hasattr(attendance_record, 'calculate_hours'):
                        attendance_record.calculate_hours()

                    if created:
                        synced_count += 1

                except Exception as e:
                    logger.error(f"Error processing attendance log: {str(e)}")
                    continue

            # Update device sync timestamp
            self.device.last_sync = timezone.now()
            self.device.save()

            logger.info(f"Synced {synced_count} attendance records")
            return synced_count

        except Exception as e:
            logger.error(f"Failed to sync attendance: {str(e)}")
            return 0
        finally:
            self.zk_device.disconnect()

    def upload_users(self) -> int:
        """
        Upload users from database to device
        Returns number of users uploaded
        """
        try:
            if not self.zk_device.connect():
                return 0

            from .models import Employee

            employees = Employee.objects.filter(
                organization=self.device.organization,
                is_active=True
            )

            uploaded_count = 0

            for employee in employees:
                try:
                    # Generate UID if not exists
                    if not employee.device_user_id:
                        employee.device_user_id = str(employee.id)
                    
                    if not employee.device_enrollment_id:
                        employee.device_enrollment_id = str(employee.employee_id or employee.id)

                    # Upload user to device
                    success = self.zk_device.set_user(
                        uid=int(employee.device_user_id),
                        name=employee.full_name[:23],  # Max 24 chars for some devices
                        privilege=0,  # 0=User, 14=Admin
                        password='',
                        group_id='',
                        user_id=str(employee.device_enrollment_id),
                        card=0
                    )

                    if success:
                        uploaded_count += 1
                        employee.save()
                        logger.info(f"Uploaded user: {employee.full_name}")

                except Exception as e:
                    logger.error(f"Error uploading user {employee.full_name}: {str(e)}")
                    continue

            logger.info(f"Uploaded {uploaded_count} users to device")
            return uploaded_count

        except Exception as e:
            logger.error(f"Failed to upload users: {str(e)}")
            return 0
        finally:
            self.zk_device.disconnect()


# def test_device_connection(ip_address: str, port: int = 4370) -> Dict:
#     """
#     Test connection to ZKTeco device
#     """
#     result = {
#         'connected': False,
#         'device_info': {},
#         'error': None,
#         'user_count': 0,
#         'attendance_count': 0
#     }

#     device = ZKTecoDevice(ip_address, port)

#     try:
#         print(f"\nTesting connection to {ip_address}:{port}...")
        
#         if device.connect():
#             print("✓ Connected successfully!\n")
#             result['connected'] = True

#             # Get device info
#             print("Getting device information...")
#             info = device.get_device_info()
#             result['device_info'] = info
            
#             for key, value in info.items():
#                 print(f"  {key}: {value}")

#             # Get user count
#             print("\nGetting users...")
#             users = device.get_users()
#             result['user_count'] = len(users)
#             print(f"  Total users: {len(users)}")
            
#             if users:
#                 print("\n  Sample users:")
#                 for user in users[:3]:
#                     print(f"    - {user['name']} (ID: {user['user_id']}, UID: {user['uid']})")

#             # Get attendance count
#             print("\nGetting attendance records...")
#             attendance = device.get_attendance()
#             result['attendance_count'] = len(attendance)
#             print(f"  Total records: {len(attendance)}")
            
#             if attendance:
#                 print("\n  Sample records:")
#                 for record in attendance[:3]:
#                     print(f"    - User {record['user_id']}: {record['timestamp']} (Punch: {record['punch']})")

#             print("\n✓ Test completed successfully!")

#         else:
#             print("✗ Connection failed")
#             result['error'] = "Unable to connect to device"

#     except Exception as e:
#         print(f"✗ Error: {str(e)}")
#         result['error'] = str(e)
#     finally:
#         device.disconnect()

#     return result


# if __name__ == "__main__":
#     # Quick test
#     test_device_connection("192.168.68.3", 4370)