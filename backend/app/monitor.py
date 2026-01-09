import time
import subprocess
import threading
from app.core.config import settings
from app.core.logger import logger
from pathlib import Path

class LogMonitor:
    def __init__(self):
        self.stop_event = threading.Event()
        self.log_dir = settings.BASE_DIR / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.monitored_files = set()

    def start(self):
        """Start the monitor loop in a background thread"""
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("🕵️ Auto Monitor started in background.")

    def _monitor_loop(self):
        logger.info(f"Monitoring {self.log_dir.absolute()} for new activity logs...")
        
        while not self.stop_event.is_set():
            try:
                # List all .log files
                files = list(self.log_dir.glob("*.log"))
                
                for file in files:
                    if file.name not in self.monitored_files:
                        # Found a new log file!
                        ip_label = file.stem.replace("_", ":")
                        window_title = f"Activity: {ip_label}"
                        
                        # Check if window already exists to prevent popping up on reload
                        if self._is_window_open(window_title):
                            self.monitored_files.add(file.name)
                            continue

                        # Launch using the tailored PowerShell script
                        # logic: start "Title" powershell -File script.ps1 ...
                        scripts_dir = Path(__file__).parent.parent / "scripts"
                        ps_script = scripts_dir / "tail_log.ps1"
                        
                        if not ps_script.exists():
                             # Fallback if script missing
                             logger.warning("tail_log.ps1 not found, using simple tail")
                             cmd = f'start "{window_title}" powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content \'{file.absolute()}\' -Wait -Tail 10"'
                        else:
                             # Use the robust script
                             cmd = f'start "{window_title}" powershell -NoProfile -ExecutionPolicy Bypass -File "{ps_script.absolute()}" -LogPath "{file.absolute()}" -Title "{window_title}"'
                             
                        subprocess.Popen(cmd, shell=True)
                        self.monitored_files.add(file.name)
                        logger.info(f"✨ Spawned monitor for {ip_label}")
                
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)

    def _is_window_open(self, title: str) -> bool:
        """Check if a window with the given title exists using PowerShell (Windows only)"""
        try:
            # Using PowerShell to find the window title is more reliable than tasklist
            # Get-Process | Where-Object { $_.MainWindowTitle -eq 'title' }
            ps_cmd = f"Get-Process | Where-Object {{ $_.MainWindowTitle -eq '{title}' }} | Select-Object -ExpandProperty Id"
            cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{ps_cmd}"'
            
            output = subprocess.check_output(cmd, shell=True).decode(errors='ignore').strip()
            
            # If output contains a PID, the window exists
            return len(output) > 0
        except:
            return False
