import os
import platform
import socket
from datetime import datetime

class LogNormalizer:
    def __init__(self):
        self.hostname = socket.gethostname()

    def normalize_process_log(self, log):
        """Chuẩn hóa log process theo định dạng database"""
        return {
            'Time': log.get('Time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Hostname': log.get('Hostname') or self.hostname,
            'ProcessID': log.get('ProcessID') or 0,
            'ParentProcessID': log.get('ParentProcessID') or 0,
            'ProcessName': log.get('ProcessName') or '',
            'CommandLine': log.get('CommandLine') or '',
            'ExecutablePath': log.get('ExecutablePath') or '',
            'UserName': log.get('UserName') or '',
            'CPUUsage': float(log.get('CPUUsage') or 0.0),
            'MemoryUsage': int(log.get('MemoryUsage') or 0),
            'Hash': log.get('Hash') or ''
        }

    def normalize_file_log(self, log):
        """Chuẩn hóa log file theo định dạng database"""
        return {
            'Time': log.get('Time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Hostname': log.get('Hostname') or self.hostname,
            'FileName': log.get('FileName') or '',
            'FilePath': log.get('FilePath') or '',
            'FileSize': int(log.get('FileSize') or 0),
            'FileHash': log.get('FileHash') or '',
            'EventType': log.get('EventType') or 'Unknown',
            'ProcessID': log.get('ProcessID') or 0,
            'ProcessName': log.get('ProcessName') or ''
        }

    def normalize_network_log(self, log):
        """Chuẩn hóa log network theo định dạng database"""
        return {
            'Time': log.get('Time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Hostname': log.get('Hostname') or self.hostname,
            'ProcessID': log.get('ProcessID') or 0,
            'ProcessName': log.get('ProcessName') or '',
            'Protocol': log.get('Protocol') or 'Unknown',
            'LocalAddress': log.get('LocalAddress') or '',
            'LocalPort': int(log.get('LocalPort') or 0),
            'RemoteAddress': log.get('RemoteAddress') or '',
            'RemotePort': int(log.get('RemotePort') or 0),
            'Direction': log.get('Direction') or 'Unknown'
        }

    @staticmethod
    def normalize_process_log(log_data, os_type):
        """Normalize process log data for both Windows and Linux"""
        base_log = {
            'Time': log_data.get('Time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Hostname': log_data.get('Hostname') or socket.gethostname(),
            'ProcessID': log_data.get('ProcessID') or log_data.get('PID') or 0,
            'ParentProcessID': log_data.get('ParentProcessID') or log_data.get('PPID') or 0,
            'ProcessName': log_data.get('ProcessName') or log_data.get('name') or '',
            'CommandLine': log_data.get('CommandLine') or log_data.get('cmdline') or '',
            'ExecutablePath': log_data.get('ExecutablePath') or log_data.get('exe') or '',
            'UserName': log_data.get('UserName') or log_data.get('username') or '',
            'CPUUsage': log_data.get('CPUUsage') or 0.0,
            'MemoryUsage': log_data.get('MemoryUsage') or 0,
            'Hash': log_data.get('Hash') or log_data.get('SHA256') or '',
            'OSType': os_type
        }

        # Add OS-specific fields
        if os_type == 'Windows':
            base_log.update({
                'SignatureStatus': log_data.get('SignatureStatus', 'unknown'),
                'CompanyName': log_data.get('CompanyName', 'unknown')
            })
        else:  # Linux
            base_log.update({
                'GroupName': log_data.get('GroupName', 'unknown'),
                'State': log_data.get('State', 'unknown'),
                'Threads': log_data.get('Threads', 0),
                'Priority': log_data.get('Priority', 0),
                'Nice': log_data.get('Nice', 0)
            })

        return base_log

    @staticmethod
    def normalize_file_log(log_data, os_type):
        """Normalize file log data for both Windows and Linux"""
        base_log = {
            'Time': log_data.get('Time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Hostname': log_data.get('Hostname') or socket.gethostname(),
            'FileName': log_data.get('FileName') or os.path.basename(log_data.get('FilePath', '')),
            'FilePath': log_data.get('FilePath') or '',
            'FileSize': log_data.get('FileSize') or 0,
            'FileHash': log_data.get('FileHash') or log_data.get('Hash') or '',
            'EventType': log_data.get('EventType') or 'file_event',
            'ProcessID': log_data.get('ProcessID') or log_data.get('PID') or 0,
            'ProcessName': log_data.get('ProcessName') or '',
            'UserName': log_data.get('UserName') or '',
            'OSType': os_type
        }

        # Add OS-specific fields
        if os_type == 'Linux':
            base_log.update({
                'Owner': log_data.get('Owner', 'unknown'),
                'Group': log_data.get('Group', 'unknown'),
                'Permissions': log_data.get('Permissions', {}),
                'LastModified': log_data.get('LastModified', ''),
                'LastAccessed': log_data.get('LastAccessed', ''),
                'Created': log_data.get('Created', ''),
                'Inode': log_data.get('Inode', 0),
                'Device': log_data.get('Device', 0),
                'HardLinks': log_data.get('HardLinks', 0)
            })

        return base_log

    @staticmethod
    def normalize_network_log(log_data, os_type):
        """Normalize network log data for both Windows and Linux"""
        base_log = {
            'Time': log_data.get('Time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Hostname': log_data.get('Hostname') or socket.gethostname(),
            'ProcessID': log_data.get('ProcessID') or log_data.get('PID') or 0,
            'ProcessName': log_data.get('ProcessName') or '',
            'Protocol': log_data.get('Protocol') or '',
            'LocalAddress': log_data.get('LocalAddress') or log_data.get('LocalIP') or '',
            'LocalPort': log_data.get('LocalPort') or 0,
            'RemoteAddress': log_data.get('RemoteAddress') or log_data.get('RemoteIP') or '',
            'RemotePort': log_data.get('RemotePort') or 0,
            'Direction': log_data.get('Direction') or '',
            'OSType': os_type
        }

        # Add OS-specific fields
        if os_type == 'Linux':
            base_log.update({
                'RemoteHostname': log_data.get('RemoteHostname', ''),
                'Status': log_data.get('Status', ''),
                'BytesSent': log_data.get('BytesSent', 0),
                'BytesReceived': log_data.get('BytesReceived', 0),
                'IsSuspicious': log_data.get('IsSuspicious', False),
                'Severity': log_data.get('Severity', 'low')
            })

        return base_log 