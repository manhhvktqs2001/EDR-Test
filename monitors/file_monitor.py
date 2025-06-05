import os
import time
import logging
import socket
import hashlib
import psutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.log_normalizer import LogNormalizer

class FileMonitor:
    def __init__(self, config):
        """Khởi tạo file monitor"""
        self.running = False
        self.thread = None
        self.interval = config.get('file_interval', 5)  # Default 5 seconds if not specified
        self.observer = None
        self.watch_paths = config.get('watch_paths', ['.'])
        self.hostname = socket.gethostname()
        self.log_normalizer = LogNormalizer()
        
    def start(self):
        """Bắt đầu monitor"""
        if not self.running:
            self.running = True
            self.observer = Observer()
            for path in self.watch_paths:
                self.observer.schedule(FileEventHandler(self), path, recursive=True)
            self.observer.start()
            logging.info("File monitor started")
            
    def stop(self):
        """Dừng monitor"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logging.info("File monitor stopped")
            
    def get_file_info(self, file_path):
        """Lấy thông tin file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            file_stat = os.stat(file_path)
            return {
                'FileName': os.path.basename(file_path),
                'FilePath': file_path,
                'FileSize': file_stat.st_size,
                'FileHash': self.get_file_hash(file_path),
                'EventType': 'Modify',
                'ProcessID': os.getpid(),
                'ProcessName': 'file_monitor'
            }
        except Exception as e:
            logging.error(f"Error getting file info for {file_path}: {e}")
            return None

    def get_file_hash(self, file_path):
        # Implementation of get_file_hash method
        pass

    def run(self):
        """Chạy monitor"""
        while self.running:
            try:
                # Lấy danh sách file đang mở
                file_logs = []
                for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                    try:
                        process_info = proc.info
                        # Lấy danh sách file đang mở
                        open_files = process_info.get('open_files', [])
                        if open_files:
                            for file in open_files:
                                try:
                                    file_info = self.get_file_info(file.path)
                                    if file_info:
                                        file_info.update({
                                            'timestamp': datetime.now().isoformat(),
                                            'pid': process_info['pid'],
                                            'process_name': process_info['name']
                                        })
                                        file_logs.append(file_info)
                                except Exception as e:
                                    logging.error(f"Error processing file {file.path}: {e}")
                                    continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                    
                if file_logs:
                    # Lưu logs vào file
                    from main import save_log_to_file
                    save_log_to_file({
                        'type': 'file',
                        'data': {
                            'hostname': socket.gethostname(),
                            'logs': file_logs
                        }
                    })
                    
                time.sleep(self.interval)
                
            except Exception as e:
                logging.error(f"Error in file monitor: {e}")
                time.sleep(self.interval)

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor
        
    def on_created(self, event):
        """Xử lý sự kiện tạo file"""
        try:
            if not event.is_directory:
                file_path = event.src_path
                file_info = self.monitor.get_file_info(file_path)
                if file_info:
                    file_info['EventType'] = 'created'
                    
                    # Gửi log
                    from main import sio, sio_connected
                    if sio_connected:
                        sio.emit('file_logs', {
                            'hostname': self.monitor.hostname,
                            'logs': [{
                                'Time': file_info['Time'],
                                'Hostname': file_info['Hostname'],
                                'FileName': file_info['FileName'],
                                'FilePath': file_info['FilePath'],
                                'FileSize': file_info['FileSize'],
                                'FileHash': file_info['FileHash'],
                                'EventType': file_info['EventType'],
                                'ProcessID': file_info['ProcessID'],
                                'ProcessName': file_info['ProcessName']
                            }]
                        })
                    else:
                        # Lưu tạm nếu mất kết nối
                        from main import save_log_to_file
                        save_log_to_file({
                            'type': 'file',
                            'data': {
                                'Time': file_info['Time'],
                                'Hostname': file_info['Hostname'],
                                'FileName': file_info['FileName'],
                                'FilePath': file_info['FilePath'],
                                'FileSize': file_info['FileSize'],
                                'FileHash': file_info['FileHash'],
                                'EventType': file_info['EventType'],
                                'ProcessID': file_info['ProcessID'],
                                'ProcessName': file_info['ProcessName']
                            }
                        })
                        
        except Exception as e:
            logging.error(f"Error handling file created event: {e}")
            
    def on_modified(self, event):
        """Xử lý sự kiện sửa file"""
        try:
            if not event.is_directory:
                file_path = event.src_path
                file_info = self.monitor.get_file_info(file_path)
                if file_info:
                    file_info['EventType'] = 'modified'
                    
                    # Gửi log
                    from main import sio, sio_connected
                    if sio_connected:
                        sio.emit('file_logs', {
                            'hostname': self.monitor.hostname,
                            'logs': [{
                                'Time': file_info['Time'],
                                'Hostname': file_info['Hostname'],
                                'FileName': file_info['FileName'],
                                'FilePath': file_info['FilePath'],
                                'FileSize': file_info['FileSize'],
                                'FileHash': file_info['FileHash'],
                                'EventType': file_info['EventType'],
                                'ProcessID': file_info['ProcessID'],
                                'ProcessName': file_info['ProcessName']
                            }]
                        })
                    else:
                        # Lưu tạm nếu mất kết nối
                        from main import save_log_to_file
                        save_log_to_file({
                            'type': 'file',
                            'data': {
                                'Time': file_info['Time'],
                                'Hostname': file_info['Hostname'],
                                'FileName': file_info['FileName'],
                                'FilePath': file_info['FilePath'],
                                'FileSize': file_info['FileSize'],
                                'FileHash': file_info['FileHash'],
                                'EventType': file_info['EventType'],
                                'ProcessID': file_info['ProcessID'],
                                'ProcessName': file_info['ProcessName']
                            }
                        })
                        
        except Exception as e:
            logging.error(f"Error handling file modified event: {e}")
            
    def on_deleted(self, event):
        """Xử lý sự kiện xóa file"""
        try:
            if not event.is_directory:
                file_path = event.src_path
                file_info = self.monitor.get_file_info(file_path)
                if file_info:
                    file_info['EventType'] = 'deleted'
                    
                    # Gửi log
                    from main import sio, sio_connected
                    if sio_connected:
                        sio.emit('file_logs', {
                            'hostname': self.monitor.hostname,
                            'logs': [{
                                'Time': file_info['Time'],
                                'Hostname': file_info['Hostname'],
                                'FileName': file_info['FileName'],
                                'FilePath': file_info['FilePath'],
                                'FileSize': file_info['FileSize'],
                                'FileHash': file_info['FileHash'],
                                'EventType': file_info['EventType'],
                                'ProcessID': file_info['ProcessID'],
                                'ProcessName': file_info['ProcessName']
                            }]
                        })
                    else:
                        # Lưu tạm nếu mất kết nối
                        from main import save_log_to_file
                        save_log_to_file({
                            'type': 'file',
                            'data': {
                                'Time': file_info['Time'],
                                'Hostname': file_info['Hostname'],
                                'FileName': file_info['FileName'],
                                'FilePath': file_info['FilePath'],
                                'FileSize': file_info['FileSize'],
                                'FileHash': file_info['FileHash'],
                                'EventType': file_info['EventType'],
                                'ProcessID': file_info['ProcessID'],
                                'ProcessName': file_info['ProcessName']
                            }
                        })
                        
        except Exception as e:
            logging.error(f"Error handling file deleted event: {e}")