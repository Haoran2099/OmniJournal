import os
import datetime
import json
import subprocess
from watchdog.events import FileSystemEventHandler
from config import Config

class JournalLogger:
    """
    Handles structured logging of events to local JSONL files.
    """
    def __init__(self):
        if not os.path.exists(Config.LOG_ROOT):
            try:
                os.makedirs(Config.LOG_ROOT)
            except OSError as e:
                print(f"[ERROR] Could not create log directory: {e}")

    def get_today_file(self):
        """Returns the path for today's log file."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return os.path.join(Config.LOG_ROOT, f"{today}.jsonl")

    def log(self, entry_type, content, context=None):
        """Writes a structured log entry."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "type": entry_type,
            "content": content,
            "context": context or {}
        }
        
        # Console output for real-time monitoring
        print(f"[{timestamp}] [{entry_type}] {content}")

        try:
            with open(self.get_today_file(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except IOError as e:
            print(f"[ERROR] Failed to write log: {e}")


class ContextSensor:
    """
    Interacts with macOS system APIs to retrieve idle time, battery status, etc.
    """
    def get_idle_time(self):
        """Returns system idle time in seconds using IOREG."""
        try:
            cmd = "ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print $NF; exit}'"
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if output:
                return int(output) / 1000000000 
            return 0
        except Exception:
            return 0

    def is_media_playing(self):
        """Checks for power assertions indicating media playback."""
        try:
            output = subprocess.check_output(["pmset", "-g", "assertions"]).decode()
            if "PreventUserIdleDisplaySleep" in output:
                return "level=255" in output or "PreventUserIdleDisplaySleep 1" in output
            return False
        except Exception:
            return False

    def get_wifi_ssid(self):
        """Retrieves the current Wi-Fi SSID."""
        try:
            cmd = ["networksetup", "-getairportnetwork", "en0"]
            output = subprocess.check_output(cmd).decode().strip()
            if "Current Wi-Fi Network" in output:
                return output.split(": ")[1]
            return "Offline"
        except Exception:
            return "Unknown"

    def get_battery_status(self):
        """Checks if the device is plugged in or on battery."""
        try:
            output = subprocess.check_output(["pmset", "-g", "batt"]).decode()
            if "AC Power" in output:
                return "Plugged In"
            return "Battery Mode"
        except Exception:
            return "Unknown"


class WindowSensor:
    """
    Uses AppleScript to retrieve the active window title and application name.
    """
    def get_active_window(self):
        script = '''
        global frontApp, frontAppName, windowTitle
        set windowTitle to ""
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            try
                tell process frontAppName
                    set windowTitle to value of attribute "AXTitle" of window 1
                end tell
            end try
        end tell
        return frontAppName & " ||| " & windowTitle
        '''
        try:
            result = subprocess.check_output(['osascript', '-e', script], stderr=subprocess.STDOUT)
            result = result.decode('utf-8').strip()
            if "|||" in result:
                app, title = result.split(" ||| ")
                title = title if title and title != "missing value" else ""
                return app, title
            return result, ""
        except Exception:
            return None, None


class FileChangeHandler(FileSystemEventHandler):
    """
    Watchdog handler to log file system modifications.
    """
    def __init__(self, logger, context_sensor):
        self.logger = logger
        self.context_sensor = context_sensor

    def on_modified(self, event):
        if not event.is_directory and not event.src_path.endswith(('.DS_Store', '.json', '.tmp', '.log')):
            filename = os.path.basename(event.src_path)
            self.logger.log("FILE_MOD", f"Modified: {filename}", context={"wifi": self.context_sensor.get_wifi_ssid()})