<<<<<<< HEAD
# Database settings
DB_SETTINGS = {
    'connection_string': "Driver={ODBC Driver 17 for SQL Server};Server=MANH;Database=EDR_System;Trusted_Connection=yes;"
}
 
# Server settings
SERVER_SETTINGS = {
    'host': '0.0.0.0',  # Lắng nghe trên tất cả các địa chỉ để agent và dashboard có thể kết nối
    'port': 5000
=======
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.ERROR,  # Chỉ hiển thị ERROR và CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Tắt các log không cần thiết
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

# Server Configuration
SERVER_CONFIG = {
    'host': '192.168.20.85',  # Server IP address
    'port': 5000,             # Server port
    'reconnect_interval': 5,  # Seconds between reconnection attempts
    'max_retries': 3          # Maximum number of reconnection attempts
}

# Agent Configuration
AGENT_CONFIG = {
    'hostname': None,         # Will be set automatically
    'agent_id': None,         # Will be set by server
    'log_interval': 10        # Seconds between log transmissions
}

# Logging Configuration
LOG_CONFIG = {
    'level': 'ERROR',         # Chỉ hiển thị lỗi
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'agent.log'
}

# Monitor Configuration
MONITOR_CONFIG = {
    'process': {
        'suspicious_processes': [
            'cmd.exe', 'powershell.exe', 'wmic.exe', 'net.exe',
            'reg.exe', 'schtasks.exe', 'at.exe', 'sc.exe'
        ]
    },
    'network': {
        'suspicious_ports': [22, 23, 3389, 445, 1433, 3306, 5432, 27017]
    },
    'file': {
        'suspicious_extensions': ['.exe', '.dll', '.bat', '.cmd', '.ps1', '.vbs', '.js'],
        'sensitive_paths': [
            'System32',
            'Program Files',
            'Program Files (x86)',
            'Windows',
            'AppData',
            'Users'
        ],
        'monitored_paths': [
            'C:\\Windows\\System32',
            'C:\\Program Files',
            'C:\\Program Files (x86)',
            'C:\\Users'
        ]
    }
>>>>>>> 6d349bf (Initial commit)
} 