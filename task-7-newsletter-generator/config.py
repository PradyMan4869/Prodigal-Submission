from dotenv import load_dotenv
import os

load_dotenv()

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- OpenAI API Key ---
# Make sure to set this environment variable for LangChain to work
# It's not in the .env to avoid accidental commits.
# Set it in your shell: export OPENAI_API_KEY='your_key'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- News Sources ---
NEWS_SOURCES = {
    "CoinDesk": "https://www.coindesk.com/",
    "CoinTelegraph": "https://cointelegraph.com/",
    "Decrypt": "https://decrypt.co/",
    "Bankless": "https://www.bankless.com/",
    "The Block": "https://www.theblock.co/",
}

# --- Agent Configuration ---
NUM_ARTICLES_TO_SELECT = 10
SIMILARITY_THRESHOLD = 0.8  # For deduplication (cosine similarity)
LLM_MODEL_NAME = "gpt-3.5-turbo"

# --- Scheduler Configuration ---
# Run the job every day at a specific time (e.g., 08:00 UTC)
# For testing, you might want a shorter interval.
# For a 2-day simulation, we will run it every few minutes.
# Set to 'daily' for production, 'testing' for frequent runs.
SCHEDULE_MODE = 'testing' 
TESTING_INTERVAL_MINUTES = 5 # Run every 5 minutes for simulation
DAILY_RUN_TIME = "08:00" # UTC time
