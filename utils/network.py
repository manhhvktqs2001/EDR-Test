import logging
import socketio
import requests
from datetime import datetime
from config import SERVER_CONFIG
import threading
import socket

class NetworkManager:
    def __init__(self):
        print("Initializing NetworkManager...")
        self.logger = logging.getLogger(__name__)
        self.sio = None
        self.shutdown_event = threading.Event()
        self.connected = False
        self.lock = threading.Lock()
        self.server_url = f"http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}"
        print(f"NetworkManager initialized with server URL: {self.server_url}")

    def _log(self, level, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp} - {level} - {message}"
        print(log_message)  # In ra console
        if level == "ERROR":
            logging.error(message)
        else:
            logging.info(message)

    def set_socketio(self, sio):
        """Set Socket.IO client"""
        print("Setting Socket.IO client...")
        self.sio = sio
        print("Socket.IO client set successfully")

    def is_connected(self):
        """Check if connected to server"""
        connected = self.connected and self.sio and self.sio.connected
        print(f"Connection status: {connected}")
        return connected

    def connect(self, host, port):
        """Connect to server"""
        try:
            print(f"Attempting to connect to {host}:{port}...")
            if not self.sio:
                print("Socket.IO client not initialized")
                return False
            
            with self.lock:
                if not self.sio.connected:
                    print("Connecting to server...")
                    self.sio.connect(f'http://{host}:{port}')
                    self.connected = True
                    print("Connected successfully")
                    return True
            print("Already connected")
            return True
        except Exception as e:
            print(f"Error connecting to server: {e}")
            logging.error(f"Error connecting to server: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from server"""
        try:
            if self.sio and self.sio.connected:
                self.sio.disconnect()
            self.connected = False
        except Exception as e:
            logging.error(f"Error disconnecting from server: {e}")

    def emit(self, event, data):
        """Emit event to server"""
        try:
            if self.is_connected():
                self.sio.emit(event, data)
                print(f"[DEBUG] Emit event '{event}' thành công.")
                return True
            else:
                print(f"[WARNING] Socket.IO not connected, cannot emit event: {event}")
                logging.warning(f"Socket.IO not connected, cannot emit event: {event}")
            return False
        except Exception as e:
            print(f"[ERROR] Error emitting event {event}: {e}")
            logging.error(f"Error emitting event {event}: {e}")
            return False

    def shutdown(self):
        """Shutdown network manager"""
        try:
            self.shutdown_event.set()
            self.disconnect()
        except Exception as e:
            logging.error(f"Error shutting down network manager: {e}")

    def send_process_log(self, process_info):
        """Send process log to server"""
        try:
            if self.is_connected():
                self.emit('process_logs', {
                    'hostname': socket.gethostname(),
                    'logs': [process_info]
                })
                logging.info(f"Sending process log: {process_info.get('ProcessName', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Error sending process log: {e}")

    def send_network_log(self, network_info):
        """Send network log to server"""
        try:
            if self.is_connected():
                self.emit('network_logs', {
                    'hostname': socket.gethostname(),
                    'logs': [network_info]
                })
                logging.info(f"Sending network log: {network_info.get('ProcessName', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Error sending network log: {e}")

    def send_file_log(self, file_info):
        """Send file log to server"""
        try:
            if self.is_connected():
                self.emit('file_logs', {
                    'hostname': socket.gethostname(),
                    'logs': [file_info]
                })
                logging.info(f"Sending file log: {file_info.get('FileName', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Error sending file log: {e}")

    def send_alert(self, alert_info):
        """Send alert to server"""
        try:
            if self.is_connected():
                self.emit('alert', {
                    'timestamp': datetime.now().isoformat(),
                    'alert_info': alert_info
                })
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")

    def get_server_url(self):
        """Get the server URL"""
        return self.server_url 