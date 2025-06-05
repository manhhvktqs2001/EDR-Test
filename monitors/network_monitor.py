import os
import sys
import time
import psutil
import logging
import threading
from datetime import datetime
import socket
from utils.log_normalizer import LogNormalizer

class NetworkMonitor:
    def __init__(self, config):
        """Khởi tạo network monitor"""
        self.running = False
        self.thread = None
        self.interval = config.get('network_interval', 5)  # Default 5 seconds if not specified
        self.hostname = socket.gethostname()
        self.log_normalizer = LogNormalizer()
        self.last_connections = set()
        
    def start(self):
        """Bắt đầu monitor"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = True
            self.thread.start()
            logging.info("Network monitor started")
            
    def stop(self):
        """Dừng monitor"""
        self.running = False
        if self.thread:
            self.thread.join()
            logging.info("Network monitor stopped")
            
    def get_process_info(self, pid):
        try:
            process = psutil.Process(pid)
            return {
                'pid': pid,
                'name': process.name()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return {'pid': pid, 'name': 'unknown'}
        except Exception as e:
            logging.error(f"Error getting process info: {e}")
            return {'pid': pid, 'name': 'unknown'}

    def collect_network_logs(self):
        try:
            current_connections = set()
            network_logs = []
            
            # Lấy tất cả kết nối mạng
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                try:
                    # Skip if no local address
                    if not conn.laddr:
                        continue
                        
                    # Tạo key duy nhất cho kết nối
                    local_addr = f"{conn.laddr[0]}:{conn.laddr[1]}"
                    remote_addr = f"{conn.raddr[0]}:{conn.raddr[1]}" if conn.raddr else "0.0.0.0:0"
                    conn_key = f"{local_addr}-{remote_addr}"
                    current_connections.add(conn_key)
                    
                    # Lấy thông tin process
                    process_info = self.get_process_info(conn.pid)
                    
                    # Xác định hướng kết nối
                    direction = 'Outbound' if conn.status == 'ESTABLISHED' else 'Inbound'
                    
                    # Tạo log entry với đầy đủ các trường
                    log_entry = {
                        'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Hostname': self.hostname,
                        'ProcessID': process_info['pid'],
                        'ProcessName': process_info['name'],
                        'Protocol': conn.type,
                        'LocalAddress': conn.laddr[0],
                        'LocalPort': conn.laddr[1],
                        'RemoteAddress': conn.raddr[0] if conn.raddr else '',
                        'RemotePort': conn.raddr[1] if conn.raddr else 0,
                        'Direction': direction
                    }
                    
                    # Chuẩn hóa log theo định dạng database
                    normalized_log = self.log_normalizer.normalize_network_log(log_entry, 'Windows')
                    network_logs.append(normalized_log)
                    
                except Exception as e:
                    logging.error(f"Error processing connection: {e}")
                    continue
            
            # Phát hiện kết nối mới và đã đóng
            new_connections = current_connections - self.last_connections
            closed_connections = self.last_connections - current_connections
            
            self.last_connections = current_connections
            
            return network_logs
            
        except Exception as e:
            logging.error(f"Error in collect_network_logs: {e}")
            return []

    def run(self):
        """Chạy monitor"""
        while self.running:
            try:
                # Lấy danh sách kết nối mạng
                network_logs = []
                for conn in psutil.net_connections(kind='inet'):
                    try:
                        # Lấy thông tin process
                        process = psutil.Process(conn.pid) if conn.pid else None
                        if process:
                            process_info = process.info
                            # Thêm thông tin kết nối
                            process_info.update({
                                'timestamp': datetime.now().isoformat(),
                                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else '',
                                'status': conn.status
                            })
                            network_logs.append(process_info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                    
                if network_logs:
                    # Lưu logs vào file
                    from main import save_log_to_file
                    save_log_to_file({
                        'type': 'network',
                        'data': {
                            'hostname': socket.gethostname(),
                            'logs': network_logs
                        }
                    })
                    
                time.sleep(self.interval)
                
            except Exception as e:
                logging.error(f"Error in network monitor: {e}")
                time.sleep(self.interval)

    def send_network_logs(self):
        """Gửi network logs đến server"""
        try:
            if not self.sio or not self.sio.connected:
                return
            
            # Lấy thông tin kết nối mạng
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                try:
                    conn_info = {
                        'fd': conn.fd,
                        'family': conn.family,
                        'type': conn.type,
                        'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid,
                        'timestamp': datetime.now().isoformat()
                    }
                    connections.append(conn_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
            if connections:
                self.sio.emit('network_logs', {
                    'hostname': socket.gethostname(),
                    'logs': connections
                })
            
        except Exception as e:
            logging.error(f"Error sending network logs: {e}")