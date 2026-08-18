import os
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, analyzer):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "8308036418")
        self.analyzer = analyzer
        self.api_url = f"https://api.telegram.org/bot{self.token}"

        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Telegram bot will not function.")

    async def send_message(self, text):
        if not self.token:
            return

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send telegram message: {await response.text()}")
        except Exception as e:
            logger.error(f"Error sending telegram message: {e}")

    async def poll_updates(self):
        """
        Long-running async polling loop using aiohttp for Telegram updates.
        """
        if not self.token:
            return

        offset = 0
        url = f"{self.api_url}/getUpdates"

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    payload = {"offset": offset, "timeout": 30}
                    async with session.get(url, params=payload, timeout=40) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("ok"):
                                for update in data.get("result", []):
                                    offset = update["update_id"] + 1
                                    await self.handle_update(update)
                        else:
                            await asyncio.sleep(5)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Telegram polling error: {e}")
                    await asyncio.sleep(5)

    async def handle_update(self, update):
        if "message" not in update:
            return

        message = update["message"]
        text = message.get("text", "")

        if text.startswith("/status"):
            await self.send_status_report()

    async def send_status_report(self):
        best_algo = self.analyzer.best_algorithm or "None"
        stats = self.analyzer.accuracy_stats

        msg = f"📊 <b>Algorithm Status Report</b>\n\n"
        msg += f"🏆 Best Algorithm: <b>{best_algo}</b>\n\n"
        msg += "📈 <b>Accuracy Stats:</b>\n"

        for algo, acc in stats.items():
            msg += f"- {algo}: {acc:.2f}%\n"

        await self.send_message(msg)

    async def hourly_reporter(self):
        """
        Background task to send hourly reports.
        """
        while True:
            await asyncio.sleep(3600)  # 1 hour
            await self.send_status_report()
