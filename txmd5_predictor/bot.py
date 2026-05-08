import os
import logging
from aiogram import Bot, Dispatcher

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = "8308036418"  # Target Chat ID from memory

        if token:
            self.bot = Bot(token=token)
            self.dp = Dispatcher()
        else:
            self.bot = None
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot will not function.")

    async def send_message(self, text):
        if self.bot:
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=text)
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
        else:
            logger.info(f"Mock Telegram Send: {text}")

bot = TelegramBot()
