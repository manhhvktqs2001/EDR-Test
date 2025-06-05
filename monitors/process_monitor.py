import os
import sys
import psutil
import logging
import hashlib
import requests
from datetime import datetime
import time
import socket
import threading
from utils.log_normalizer import LogNormalizer

if os.name != 'nt':  # Chỉ import pwd nếu không phải Windows
    import pwd

class ProcessMonitor:
    def __init__(self, config):
        """Khởi tạo process monitor"""
        self.running = False
        self.thread = None
        self.interval = config.get('process_interval', 5)  # Default 5 seconds if not specified
        self.hostname = socket.gethostname()
        self.log_normalizer = LogNormalizer()
        self.last_processes = set()
        
    def start(self):
        """Bắt đầu monitor"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = True
            self.thread.start()
            logging.info("Process monitor started")
            
    def stop(self):
        """Dừng monitor"""
        self.running = False
        if self.thread:
            self.thread.join()
            logging.info("Process monitor stopped")
            
    def get_process_hash(self, path):
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logging.error(f"Error calculating process hash: {e}")
        return ""

    def collect_process_logs(self):
        try:
            current_processes = set()
            process_logs = []
            
            for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'exe', 'username', 'cpu_percent', 'memory_info']):
                try:
                    process_info = proc.info
                    current_processes.add(process_info['pid'])
                    
                    # Tạo log entry với đầy đủ các trường
                    log_entry = {
                        'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Hostname': self.hostname,
                        'ProcessID': process_info['pid'],
                        'ParentProcessID': process_info['ppid'],
                        'ProcessName': process_info['name'],
                        'CommandLine': ' '.join(process_info['cmdline']) if process_info['cmdline'] else '',
                        'ExecutablePath': process_info['exe'] if process_info['exe'] else '',
                        'UserName': process_info['username'],
                        'CPUUsage': process_info['cpu_percent'],
                        'MemoryUsage': process_info['memory_info'].rss if process_info['memory_info'] else 0,
                        'Hash': self.get_process_hash(process_info['exe']) if process_info['exe'] else ''
                    }
                    
                    # Chuẩn hóa log theo định dạng database
                    normalized_log = self.log_normalizer.normalize_process_log(log_entry, 'Windows')
                    process_logs.append(normalized_log)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logging.error(f"Error collecting process info: {e}")
                    continue
            
            # Phát hiện process mới và đã kết thúc
            new_processes = current_processes - self.last_processes
            ended_processes = self.last_processes - current_processes
            
            self.last_processes = current_processes
            
            return process_logs
            
        except Exception as e:
            logging.error(f"Error in collect_process_logs: {e}")
            return []

    def run(self):
        """Chạy monitor"""
        while self.running:
            try:
                # Lấy danh sách process
                process_logs = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time', 'exe']):
                    try:
                        process_info = proc.info
                        # Thêm timestamp
                        process_info['timestamp'] = datetime.now().isoformat()
                        process_logs.append(process_info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                        
                if process_logs:
                    # Lưu logs vào file
                    from main import save_log_to_file
                    save_log_to_file({
                        'type': 'process',
                        'data': {
                            'hostname': socket.gethostname(),
                            'logs': process_logs
                        }
                    })
                    
                time.sleep(self.interval)
                
            except Exception as e:
                logging.error(f"Error in process monitor: {e}")
                time.sleep(self.interval)

    def send_process_logs(self):
        """Gửi process logs đến server"""
        try:
            if not self.sio or not self.sio.connected:
                return
            
            # Lấy danh sách process
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time', 'exe']):
                try:
                    process_info = proc.info
                    # Thêm timestamp
                    process_info['timestamp'] = datetime.now().isoformat()
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                
            if processes:
                self.sio.emit('process_logs', {
                    'hostname': socket.gethostname(),
                    'logs': processes
                })
            
        except Exception as e:
            logging.error(f"Error sending process logs: {e}")