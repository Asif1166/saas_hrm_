from django.core.management.base import BaseCommand
from hrm.models import AttendanceDevice
from hrm.zkteco_utils import AttendanceSyncManager
import datetime


class Command(BaseCommand):
    help = 'Sync attendance data from ZKTeco devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='Specific device ID to sync'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to sync (default: 7)'
        )
        parser.add_argument(
            '--upload-users',
            action='store_true',
            help='Upload users to device'
        )

    def handle(self, *args, **options):
        device_id = options.get('device_id')
        days = options.get('days')
        upload_users = options.get('upload_users')

        if device_id:
            devices = AttendanceDevice.objects.filter(id=device_id)
        else:
            devices = AttendanceDevice.objects.filter(is_active=True)

        for device in devices:
            self.stdout.write(f"\nSyncing device: {device.name} ({device.ip_address})")
            
            sync_manager = AttendanceSyncManager(device)
            
            # Sync device info
            if sync_manager.sync_device_info():
                self.stdout.write(self.style.SUCCESS('✓ Device info synced'))
            else:
                self.stdout.write(self.style.ERROR('✗ Failed to sync device info'))
                continue
            
            # Upload users if requested
            if upload_users:
                uploaded = sync_manager.upload_users()
                self.stdout.write(self.style.SUCCESS(f'✓ Uploaded {uploaded} users'))
            
            # Sync users
            users_synced = sync_manager.sync_users()
            self.stdout.write(self.style.SUCCESS(f'✓ Synced {users_synced} users'))
            
            # Sync attendance
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=days)
            
            attendance_synced = sync_manager.sync_attendance(start_date, end_date)
            self.stdout.write(self.style.SUCCESS(f'✓ Synced {attendance_synced} attendance records'))

        self.stdout.write(self.style.SUCCESS('\n✓ Sync completed!'))