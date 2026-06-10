import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

async def send_telegram_message(message: str):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "8308036418")

    if not bot_token or bot_token == "your_telegram_bot_token":
        logger.warning("TELEGRAM_BOT_TOKEN not configured. Skipping Telegram notification.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        # We also pass ssl=False here if we want consistency with the memory note,
        # but typically Telegram API SSL works fine. Added just in case.
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Failed to send Telegram message: {response.status} {text}")
                else:
                    logger.info("Successfully sent Telegram report.")
    except Exception as e:
        logger.error(f"Exception while sending Telegram message: {e}")
