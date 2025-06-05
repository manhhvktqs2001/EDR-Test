import os
import sys
import logging
from plyer import notification
from datetime import datetime
import time

class NotificationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._check_plyer_installed()
        self.last_notify_time = 0
        self.notify_interval = 2  # seconds
        self.last_message = None

    def _check_plyer_installed(self):
        """Kiểm tra và cài đặt plyer nếu chưa có"""
        try:
            import plyer
        except ImportError:
            self.logger.error("Plyer not installed. Installing...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "plyer"])
                self.logger.info("Plyer installed successfully")
            except Exception as e:
                self.logger.error(f"Failed to install plyer: {e}")
                raise

    def show_notification(self, title="EDR Alert", message="", timeout=10):
        """
        Hiển thị thông báo popup
        
        Args:
            title (str): Tiêu đề thông báo
            message (str): Nội dung thông báo
            timeout (int): Thời gian hiển thị (giây)
        """
        try:
            now = time.time()
            # Nếu nội dung giống lần trước thì bỏ qua
            if self.last_message == (title, message):
                self.logger.info("Notification skipped (duplicate content).")
                return
            # Nếu quá nhanh thì cũng bỏ qua
            if now - self.last_notify_time < self.notify_interval:
                self.logger.info("Notification skipped to prevent spam.")
                return
            self.last_notify_time = now
            self.last_message = (title, message)
            # Giới hạn độ dài title và message
            max_title_len = 48
            max_msg_len = 180
            short_title = title if len(title) <= max_title_len else title[:max_title_len-3] + "..."
            short_message = message if len(message) <= max_msg_len else message[:max_msg_len-3] + "..."
            # Thêm timestamp vào message (vẫn đảm bảo không vượt quá max_msg_len)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ts_prefix = f"[{timestamp}] "
            if len(ts_prefix) + len(short_message) > max_msg_len:
                short_message = short_message[:max_msg_len-len(ts_prefix)-3] + "..."
            full_message = ts_prefix + short_message
            # Hiển thị thông báo
            notification.notify(
                title=short_title,
                message=full_message,
                app_name="EDR Agent",
                timeout=timeout
            )
            
            # Log thông báo
            self.logger.info(f"Notification shown: {short_title} - {full_message}")
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
            # Fallback: In ra console nếu không hiển thị được popup
            print(f"\n{title}: {message}\n") 