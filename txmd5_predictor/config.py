import os
from dotenv import load_dotenv

# Load env variables before other imports
load_dotenv()

# API Configuration
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
POLL_INTERVAL = 0.5  # 500ms

# Telegram Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8308036418")

# LLM API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Algorithm Configuration
ALGORITHMS = ["markov", "trend", "majority", "sum_analysis"]
