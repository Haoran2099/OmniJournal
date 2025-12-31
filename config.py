import os

class Config:
    """
    Configuration settings for the OmniJournal application.
    """
    # System Paths
    USER_HOME = os.path.expanduser("~")
    # Path to the directory you want to monitor (e.g., Thesis folder, Code repository)
    MONITOR_PATH = os.path.join(USER_HOME, "Documents", "Research")
    # Path where logs and summaries will be stored
    LOG_ROOT = os.path.join(USER_HOME, "Downloads", "OmniJournal_Data")
    
    # Operational Settings
    SAMPLE_INTERVAL = 2          # Main loop cycle time in seconds
    IDLE_THRESHOLD = 60          # Time in seconds before user is considered idle
    
    # Model Configuration
    LLM_MODEL = "llama3"         # Model for daily summarization
    VLM_MODEL = "llava"          # Model for visual analysis (OCR/Captioning)
    
    # Sampling Frequencies (in seconds)
    MEDIA_HARVEST_INTERVAL = 30  # Interval for analyzing video content (Passive Learning)
    WORK_PROGRESS_INTERVAL = 30  # Interval for analyzing active work (Coding/Reading)