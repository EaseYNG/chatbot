import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TEMPERATURE = 0.7

FILES_DIR = os.path.join(PROJECT_ROOT, "files")
HISTORY_FILE = os.path.join(PROJECT_ROOT, "memory", "long_history.json")
CHECKPOINT_DB = os.path.join(PROJECT_ROOT, "memory", "checkpoints.sqlite")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

API_PREFIX = "/api"
CORS_ORIGINS = ["http://localhost:5173"]
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
