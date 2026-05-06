import os
import logging
import aiohttp
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token or self.bot_token == 'your_telegram_bot_token':
            logger.warning("Telegram Bot Token is not configured.")
        if not self.chat_id or self.chat_id == '8308036418':
            # It's okay if it's the default, but we should log it
            logger.info(f"Using default Telegram Chat ID: {self.chat_id}")

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_message(self, text: str):
        if not self.bot_token or self.bot_token == 'your_telegram_bot_token':
            logger.debug(f"Simulated Telegram Message (Token not set): {text}")
            return False

        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Successfully sent message to Telegram.")
                        return True
                    else:
                        resp_text = await response.text()
                        logger.error(f"Failed to send Telegram message. Status: {response.status}, Error: {resp_text}")
                        return False
        except Exception as e:
            logger.error(f"Exception while sending Telegram message: {e}")
            return False

    async def send_hourly_report(self, stats: Dict[str, Any]):
        best_logic = stats.get('best_logic', 'N/A')
        total_history = stats.get('total_history_analyzed', 0)
        weights = stats.get('weights', {})

        # Format weights nicely
        weights_str = "\n".join([f"- {k}: {v:.2f}" for k, v in weights.items()])

        message = (
            "📊 <b>SUPER PROJECT - Hourly Optimization Report</b> 📊\n\n"
            f"🔄 <b>Total Sessions Analyzed:</b> {total_history}\n"
            f"🏆 <b>Current Best Logic:</b> {best_logic}\n\n"
            "⚖️ <b>Algorithm Weights (Based on Accuracy):</b>\n"
            f"{weights_str}\n\n"
            "🤖 <i>The system continues to poll every 500ms and simulate on prediction errors.</i>"
        )

        await self.send_message(message)
