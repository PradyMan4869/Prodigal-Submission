import telegram
import logging
import asyncio

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_telegram_message(message: str):
    """
    Sends a message to the configured Telegram chat using the bot.
    
    Args:
        message: The text of the message to send. Supports Markdown.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("Telegram Bot Token or Chat ID is not configured. Cannot send message.")
        return

    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        logging.info(f"Sending newsletter to chat ID: {TELEGRAM_CHAT_ID}")
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        logging.info("Newsletter successfully sent to Telegram.")
    except Exception as e:
        logging.error(f"Failed to send message to Telegram: {e}")

if __name__ == '__main__':
    # For testing the sender independently
    test_message = "*Test Newsletter*\n\nThis is a _test_ message from the generator script."
    asyncio.run(send_telegram_message(test_message))
