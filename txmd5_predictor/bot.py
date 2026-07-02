import aiohttp
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/"

    async def send_message(self, message: str):
        if not self.token or not self.chat_id:
            logger.warning("Telegram token or chat ID is missing. Cannot send message.")
            return False

        url = self.api_url + "sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.error(f"Failed to send Telegram message. Status: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Exception sending Telegram message: {e}")
            return False

    async def get_updates(self, offset=None):
        if not self.token:
            return []

        url = self.api_url + "getUpdates"
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result", [])
                    return []
        except Exception as e:
            logger.error(f"Exception getting Telegram updates: {e}")
            return []
