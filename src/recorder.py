import time
import threading
import os
import json
import datetime
import ollama
from watchdog.observers import Observer

from config import Config
from src.utils import JournalLogger, ContextSensor, WindowSensor, FileChangeHandler
from src.analysis import WorkContextManager, VisualHarvester

class LifeRecorderAgent:
    """
    Main agent that orchestrates sensing, visual harvesting, and logging.
    """
    def __init__(self):
        self.logger = JournalLogger()
        self.ctx_sensor = ContextSensor()
        self.win_sensor = WindowSensor()
        self.harvester = VisualHarvester()
        self.context_manager = WorkContextManager()
        
        # File System Monitoring
        self.observer = Observer()
        event_handler = FileChangeHandler(self.logger, self.ctx_sensor)
        if os.path.exists(Config.MONITOR_PATH):
            self.observer.schedule(event_handler, Config.MONITOR_PATH, recursive=True)
            self.observer.start()
        
        # State Tracking
        self.last_app = ""
        self.last_title = ""
        self.last_ssid = ""
        self.last_snapshot_time = 0
        self.is_idle = False

    def run(self):
        print(f"[INFO] OmniJournal Agent Started.")
        print(f"[INFO] VLM Model: {Config.VLM_MODEL} | LLM Model: {Config.LLM_MODEL}")
        print(f"[INFO] Logs directory: {Config.LOG_ROOT}")
        print("[INFO] Press Ctrl+C to stop and generate the daily summary.")
        
        try:
            while True:
                idle_sec = self.ctx_sensor.get_idle_time()
                current_ssid = self.ctx_sensor.get_wifi_ssid()
                app, title = self.win_sensor.get_active_window()
                current_time = time.time()

                # 1. Context Classification
                category, prompt = self.context_manager.classify_app(app or "", title or "")
                
                # Check for system-level media playback
                is_system_media = self.ctx_sensor.is_media_playing()
                is_media_context = (category == "MEDIA" or is_system_media)

                # --- Scenario A: Media/Passive Learning ---
                if is_media_context:
                    if self.is_idle:
                        self.is_idle = False
                    
                    # Log window change
                    if app and (app != self.last_app or title != self.last_title):
                        self.logger.log("WATCHING", f"[{app}] {title}", context={"wifi": current_ssid})
                        self.last_app = app
                        self.last_title = title
                    
                    # Trigger Visual Harvesting
                    if current_time - self.last_snapshot_time > Config.MEDIA_HARVEST_INTERVAL:
                        print(f"[INFO] Harvesting visual context from media: {app}...")
                        threading.Thread(target=self._run_vlm_task, args=("HARVEST", prompt, f"[{app}] {title}")).start()
                        self.last_snapshot_time = current_time

                # --- Scenario B: Idle State ---
                elif idle_sec > Config.IDLE_THRESHOLD:
                    if not self.is_idle:
                        self.logger.log("IDLE", f"User is away (Idle > {int(Config.IDLE_THRESHOLD/60)} mins)")
                        self.is_idle = True
                
                # --- Scenario C: Active Work ---
                else:
                    if self.is_idle:
                        self.logger.log("IDLE", "User is active again")
                        self.is_idle = False

                    # Log Network Context Change
                    if current_ssid != self.last_ssid:
                        self.logger.log("WIFI", f"Location changed: {current_ssid}")
                        self.last_ssid = current_ssid
                    
                    # Log Focus Change
                    if app and (app != self.last_app or title != self.last_title):
                        self.logger.log("FOCUS", f"[{app}] {title}", context={"wifi": current_ssid, "category": category})
                        self.last_app = app
                        self.last_title = title

                    # Work Progress Tracking (VLM)
                    if category in ["CODING", "PAPER_READING", "WRITING"]:
                        if current_time - self.last_snapshot_time > Config.WORK_PROGRESS_INTERVAL:
                            print(f"[INFO] Tracking work progress ({category})...")
                            threading.Thread(target=self._run_vlm_task, args=("PROGRESS", prompt, f"[{app}] {title}")).start()
                            self.last_snapshot_time = current_time

                time.sleep(Config.SAMPLE_INTERVAL)

        except KeyboardInterrupt:
            self.observer.stop()
            self.generate_daily_summary()

    def _run_vlm_task(self, log_type, prompt, context_info):
        """Runs the VLM analysis in a separate thread to avoid blocking the main loop."""
        result = self.harvester.harvest(prompt)
        self.logger.log(log_type, f"Analyzed {context_info}: {result}")

    def generate_daily_summary(self):
        print("\n[INFO] Generating daily summary via LLM...")
        log_file = self.logger.get_today_file()
        if not os.path.exists(log_file):
            print("[WARN] No logs found for today.")
            return

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        log_text = ""
        # Filter and format logs to save context window
        for line in lines:
            try:
                d = json.loads(line)
                if d['type'] in ["HARVEST", "PROGRESS"]:
                    log_text += f"IMPORTANT: [{d['type']}] {d['content']}\n"
                elif d['type'] == "FOCUS":
                    log_text += f"[{d['timestamp']}] FOCUS: {d['content']}\n"
                else:
                    log_text += f"[{d['timestamp']}] {d['type']}: {d['content']}\n"
            except json.JSONDecodeError:
                continue

        prompt = (
            "You are an omniscient personal assistant. Analyze the user's raw activity logs to reconstruct their day.\n"
            "Key Instructions:\n"
            "1. Use [PROGRESS] tags to describe technical work details (e.g., specific code functions, research paper topics).\n"
            "2. Use [HARVEST] tags to summarize knowledge gained from passive media consumption.\n"
            "3. Use [FOCUS] tags to determine the timeline and app usage.\n\n"
            "Output Format (Markdown):\n"
            "## Daily Achievements\n"
            "### Deep Work & Progress\n"
            "- (Synthesize technical/work details here)\n"
            "### Knowledge Inputs\n"
            "- (Synthesize learnings from videos/reading here)\n"
            "### Timeline & Context\n"
            "- (Overview of time distribution and location changes)"
        )

        try:
            print("[INFO] Sending data to LLM...")
            response = ollama.chat(model=Config.LLM_MODEL, messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': log_text[-6000:]}, # Limit context to last ~6000 chars
            ])
            
            summary_path = os.path.join(Config.LOG_ROOT, f"Summary_{datetime.datetime.now().strftime('%Y-%m-%d')}.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(response['message']['content'])
            
            print(f"[SUCCESS] Summary generated: {summary_path}")
            print("-" * 50)
            print(response['message']['content'])
            print("-" * 50)
            
        except Exception as e:
            print(f"[ERROR] LLM Generation failed: {e}")