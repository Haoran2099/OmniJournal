import ollama
import pyautogui
from io import BytesIO
from config import Config

class WorkContextManager:
    """
    Classifies the current application context and provides context-aware prompts 
    for the Vision Language Model (VLM).
    """
    def __init__(self):
        # Mapping application names to categories
        self.categories = {
            "CODING": ["code", "pycharm", "cursor", "sublime", "intellij", "terminal", "iterm", "xcode", "vscode", "electron"],
            "PAPER_READING": ["zotero", "pdf", "preview", "acrobat", "cajviewer", "readpaper"],
            "WRITING": ["word", "notion", "obsidian", "pages", "typora", "notes", "feishu", "dingtalk", "latex", "overleaf"],
            "MEDIA": ["bilibili", "youtube", "vimeo", "iina", "vlc", "quicktime", "wechat", "video", "live", "movie"]
        }
        
        # Context-specific prompts for the VLM
        self.prompts = {
            "CODING": "Analyze this code screenshot. Briefly describe the functionality, logic, or module the user is currently implementing. Ignore UI details.",
            "PAPER_READING": "This is an academic paper or document. Summarize the key text, abstract, or figure shown in the center. What is the main research topic?",
            "WRITING": "The user is writing a document. Summarize the main topic or content of the text visible in the editor.",
            "MEDIA": "Extract the subtitle or key visual information from this media frame. What concept is being explained?",
            "DEFAULT": "Describe the main activity on the screen in one sentence."
        }

    def classify_app(self, app_name, title):
        """
        Determines the category and appropriate prompt based on the window title and app name.
        Returns: (Category, Prompt)
        """
        search_string = (str(app_name) + " " + str(title)).lower()
        
        for category, keywords in self.categories.items():
            if any(k in search_string for k in keywords):
                return category, self.prompts[category]
        
        return "GENERAL", self.prompts["DEFAULT"]


class VisualHarvester:
    """
    Handles screen capture and interaction with the Vision Language Model.
    """
    def harvest(self, context_prompt):
        """
        Captures the screen and generates a description using the VLM.
        """
        try:
            screenshot = pyautogui.screenshot()
            
            # Convert RGBA to RGB for JPEG compatibility (crucial for macOS)
            if screenshot.mode in ("RGBA", "P"):
                screenshot = screenshot.convert("RGB")
            
            img_byte_arr = BytesIO()
            screenshot.save(img_byte_arr, format='JPEG', quality=85)
            img_bytes = img_byte_arr.getvalue()

            # Generate description via Ollama
            response = ollama.generate(
                model=Config.VLM_MODEL, 
                prompt=context_prompt, 
                images=[img_bytes], 
                stream=False
            )
            return response['response'].strip()
        except Exception as e:
            return f"Error during visual harvesting: {str(e)}"