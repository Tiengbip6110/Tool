import asyncio
import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

async def send_telegram_message(session, text):
    token = os.getenv("TELEGRAM_TOKEN", "dummy_token")
    chat_id = "8308036418"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                logger.error(f"Failed to send telegram message: {await response.text()}")
    except Exception as e:
        logger.error(f"Error sending telegram message: {e}")

async def start_reporting_loop(analyzer):
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour

            report_text = f"Hourly Report:\n"
            report_text += f"Total Sessions Analyzed: {len(analyzer.history)}\n"
            report_text += f"Best Algorithm: {analyzer.best_algo}\n"
            report_text += f"Accuracy: {analyzer.best_accuracy:.2f}%\n"

            await send_telegram_message(session, report_text)
