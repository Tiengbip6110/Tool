import asyncio
import aiohttp
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token=None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.target_chat_id = "8308036418" # default target chat id from memory
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.session = None

    async def init_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def start_polling(self):
        """Asynchronous polling loop to fetch updates from Telegram."""
        if not self.token:
            logger.warning("No Telegram token provided. Bot polling will not start.")
            return

        await self.init_session()
        offset = None

        logger.info("Started Telegram bot polling...")

        while True:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {"timeout": 30}
                if offset:
                    params["offset"] = offset

                async with self.session.get(url, params=params, ssl=False) as response:
                    if response.status == 200:
                        data = await response.json()
                        updates = data.get("result", [])
                        for update in updates:
                            offset = update["update_id"] + 1
                            await self.handle_update(update)
                    else:
                        logger.error(f"Telegram API returned status: {response.status}")
                        await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in bot polling loop: {e}")
                await asyncio.sleep(5)

    async def handle_update(self, update):
        """Handle incoming telegram messages."""
        if "message" in update and "text" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"]["text"]

            # Simple handling of messages (like /start, /status, etc.)
            if text == "/start":
                await self.send_message(chat_id, "Bot started monitoring!")
            elif text == "/status":
                await self.send_message(chat_id, "Bot is running and monitoring txmd5...")

    async def send_message(self, chat_id, text):
        """Send message to a specific chat."""
        if not self.token or not self.session:
            return

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with self.session.post(url, json=payload, ssl=False) as response:
                if response.status != 200:
                    logger.error(f"Failed to send message: {await response.text()}")
        except Exception as e:
            logger.error(f"Error sending telegram message: {e}")

    async def send_hourly_report(self, stats):
        """
        Send hourly prediction statistics, logic performance, and % accuracy to the target chat ID.
        stats is expected to be a dict with:
        - total_predictions
        - correct_predictions
        - accuracy
        - current_algorithm
        - logic_performance (dict of algorithm names to their accuracy)
        - next_predictions (optional)
        """
        await self.init_session()

        total = stats.get('total_predictions', 0)
        correct = stats.get('correct_predictions', 0)
        accuracy = stats.get('accuracy', 0.0)
        current_algo = stats.get('current_algorithm', 'N/A')
        logic_perf = stats.get('logic_performance', {})

        report_lines = [
            "📊 <b>HOURLY REPORT - SUPER PROJECT</b> 📊",
            "",
            f"🔹 <b>Total Predictions:</b> {total}",
            f"🔹 <b>Correct:</b> {correct}",
            f"🔹 <b>Overall Accuracy:</b> {accuracy:.2f}%",
            f"🔹 <b>Current Optimal Algorithm:</b> {current_algo}",
            "",
            "⚙️ <b>Logic Performance:</b>"
        ]

        for algo, perf in logic_perf.items():
            report_lines.append(f"  - {algo}: {perf:.2f}%")

        if 'next_predictions' in stats:
            report_lines.append("")
            report_lines.append(f"🔮 <b>Next Prediction(s):</b> {stats['next_predictions']}")

        message_text = "\n".join(report_lines)
        await self.send_message(self.target_chat_id, message_text)
