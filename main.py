import os
import sys
import json
import time
import logging
import socket
import threading
import socketio
import ctypes
import platform
import psutil
import uuid
from datetime import datetime
from monitors.process_monitor import ProcessMonitor
from monitors.network_monitor import NetworkMonitor
from monitors.file_monitor import FileMonitor
from utils.network import NetworkManager

# Biến toàn cục
sio_connected = False
sio = None
shutdown_event = threading.Event()
network_manager = NetworkManager()

def is_admin():
    """Kiểm tra quyền admin trên Windows"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Chạy lại chương trình với quyền admin"""
    try:
        if sys.platform == 'win32':
            if not is_admin():
                # Lấy đường dẫn tuyệt đối của script
                script = os.path.abspath(sys.argv[0])
                params = ' '.join(sys.argv[1:])
                
                # Chạy lại với quyền admin
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    f'"{script}" {params}', 
                    None, 
                    1
                )
                if ret > 32:
                    sys.exit(0)
                else:
                    logging.error("Failed to get admin privileges")
                    sys.exit(1)
    except Exception as e:
        logging.error(f"Error requesting admin privileges: {e}")
        sys.exit(1)

def get_system_info():
    """Lấy thông tin hệ thống"""
    try:
        info = {
            'hostname': socket.gethostname(),
            'os_type': 'Windows',
            'os_version': platform.version(),
            'architecture': platform.machine(),
            'ip': socket.gethostbyname(socket.gethostname()),
            'mac': ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(40, -8, -8)]),
            'version': '1.0.0',
            'kernel': platform.uname().release,
            'user': os.getlogin(),
            'uptime': int(time.time() - psutil.boot_time()),
            'processor': platform.processor(),
            'platform': platform.platform()
        }
        logging.info(f"System info collected: {info}")
        return info
    except Exception as e:
        logging.error(f"Error getting system info: {e}")
        return {
            'hostname': socket.gethostname(),
            'os_type': 'Windows',
            'version': '1.0.0'
        }

def setup_logging():
    """Khởi tạo logging"""
    try:
        # Tạo thư mục logs nếu chưa tồn tại
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Cấu hình logging
        log_file = os.path.join('logs', 'agent.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging initialized")
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        raise

def load_config():
    """Load cấu hình từ file config.json"""
    try:
        config_file = 'config.json'
        if not os.path.exists(config_file):
            # Tạo file config mặc định nếu chưa tồn tại
            default_config = {
                'server_url': 'http://192.168.20.85:5000',
                'process_interval': 5,
                'network_interval': 5,
                'file_interval': 5,
                'watch_paths': ['.']
            }
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            logging.info(f"Created default config file: {config_file}")
            return default_config
            
        # Đọc config từ file
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Kiểm tra và thêm các giá trị mặc định nếu thiếu
        default_config = {
            'server_url': 'http://192.168.20.85:5000',
            'process_interval': 5,
            'network_interval': 5,
            'file_interval': 5,
            'watch_paths': ['.']
        }
        
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
                logging.info(f"Added default value for {key}: {value}")
                
        logging.info("Config loaded successfully")
        return config
        
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        raise

def save_log_to_file(log_data):
    """Lưu log tạm thời vào file"""
    try:
        # Tạo thư mục pending_logs nếu chưa tồn tại
        pending_logs_dir = 'pending_logs'
        if not os.path.exists(pending_logs_dir):
            try:
                os.makedirs(pending_logs_dir)
            except FileExistsError:
                # Thư mục đã được tạo bởi process khác
                pass
                
        # Tạo tên file duy nhất
        timestamp = int(time.time())
        log_type = log_data.get('type', 'unknown')
        log_file = os.path.join(pending_logs_dir, f"{log_type}_{timestamp}.json")
        
        # Đảm bảo tên file là duy nhất
        counter = 0
        while os.path.exists(log_file):
            counter += 1
            log_file = os.path.join(pending_logs_dir, f"{log_type}_{timestamp}_{counter}.json")
            
        # Lưu log vào file
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Saved pending log to {log_file}")
        
    except Exception as e:
        logging.error(f"Error saving pending log: {e}")

def send_pending_logs(sio):
    """Gửi các log tạm thời đến server"""
    try:
        pending_logs_dir = 'pending_logs'
        if not os.path.exists(pending_logs_dir):
            return
            
        # Lấy danh sách file log tạm thời
        log_files = [f for f in os.listdir(pending_logs_dir) if f.endswith('.json')]
        
        if log_files:
            logging.info(f"Found {len(log_files)} pending logs to send")
        
        for log_file in log_files:
            try:
                # Đọc log
                with open(os.path.join(pending_logs_dir, log_file), 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    
                # Gửi log
                if sio.connected:
                    # Xác định loại log từ tên file
                    if log_file.startswith('process_'):
                        sio.emit('send_log', {
                            'type': 'process',
                            'data': log_data.get('data', {})
                        })
                        logging.info(f"Sent process logs")
                    elif log_file.startswith('file_'):
                        sio.emit('send_log', {
                            'type': 'file',
                            'data': log_data.get('data', {})
                        })
                        logging.info(f"Sent file logs")
                    elif log_file.startswith('network_'):
                        sio.emit('send_log', {
                            'type': 'network',
                            'data': log_data.get('data', {})
                        })
                        logging.info(f"Sent network logs")
                        
                    # Xóa file sau khi gửi thành công
                    os.remove(os.path.join(pending_logs_dir, log_file))
                else:
                    logging.warning("Cannot send pending log - not connected to server")
                    break
                    
            except Exception as e:
                logging.error(f"Error sending pending log {log_file}: {e}")
                
    except Exception as e:
        logging.error(f"Error sending pending logs: {e}")

def start_monitors(config):
    """Khởi động các monitor"""
    try:
        # Khởi tạo các monitor với config
        process_monitor = ProcessMonitor(config)
        network_monitor = NetworkMonitor(config)
        file_monitor = FileMonitor(config)
        
        # Bắt đầu các monitor
        process_monitor.start()
        network_monitor.start()
        file_monitor.start()
        
        return process_monitor, network_monitor, file_monitor
        
    except Exception as e:
        logging.error(f"Error starting monitors: {e}")
        return None, None, None

def start_log_sender(sio):
    """Khởi động thread gửi logs định kỳ"""
    def send_logs_periodically():
        while not shutdown_event.is_set():
            try:
                if sio.connected:
                    send_pending_logs(sio)
                time.sleep(5)  # Gửi logs mỗi 5 giây
            except Exception as e:
                logging.error(f"Error in log sender thread: {e}")
                time.sleep(5)  # Đợi 5 giây nếu có lỗi
                
    # Khởi động thread
    sender_thread = threading.Thread(target=send_logs_periodically)
    sender_thread.daemon = True
    sender_thread.start()
    logging.info("Log sender thread started")
    return sender_thread

def main():
    """Hàm chính"""
    try:
        # Kiểm tra và yêu cầu quyền admin trên Windows
        if sys.platform == 'win32':
            run_as_admin()
            
        # Khởi tạo logging
        setup_logging()
        
        # Load config
        config = load_config()
        
        # Khởi tạo socket client
        global sio
        sio = socketio.Client()
        network_manager.set_socketio(sio)
        
        # Đăng ký các event handlers
        @sio.event
        def connect():
            global sio_connected
            sio_connected = True
            logging.info("Connected to server")
            
            # Gửi thông tin hệ thống
            system_info = get_system_info()
            sio.emit('register', system_info)
            
            # Gửi logs tạm thời
            send_pending_logs(sio)
            
        @sio.event
        def disconnect():
            global sio_connected
            sio_connected = False
            logging.info("Disconnected from server")
            
        # Kết nối đến server
        try:
            sio.connect(config['server_url'])
        except Exception as e:
            logging.error(f"Failed to connect to server: {e}")
            return
            
        # Khởi động các monitor
        process_monitor, network_monitor, file_monitor = start_monitors(config)
        if not all([process_monitor, network_monitor, file_monitor]):
            logging.error("Failed to start monitors")
            return
            
        # Khởi động thread gửi logs
        log_sender = start_log_sender(sio)
        if not log_sender:
            logging.error("Failed to start log sender")
            return
            
        # Giữ chương trình chạy
        try:
            while not shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
        finally:
            # Dừng các monitor
            if process_monitor:
                process_monitor.stop()
            if network_monitor:
                network_monitor.stop()
            if file_monitor:
                file_monitor.stop()
            # Ngắt kết nối
            if sio.connected:
                sio.disconnect()
            
    except Exception as e:
        logging.error(f"Error in main: {e}")
        return

if __name__ == "__main__":
    main()
