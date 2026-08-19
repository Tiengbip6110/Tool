import aiohttp
import asyncio
import os

class TelegramBot:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "8308036418")

    async def send_message(self, text):
        if not self.token:
            print("No Telegram Bot Token configured. Skipping message:", text)
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        print(f"Failed to send telegram message: {await response.text()}")
        except Exception as e:
            print(f"Error sending telegram message: {e}")

    async def run_hourly_reporting(self, analyzer):
        while True:
            await asyncio.sleep(3600)  # 1 hour

            # Compute some quick stats for the report
            # The optimization already runs on misses, but let's trigger a full evaluation
            res = await analyzer._simulate_and_optimize()
            if res:
                best_algo, scores = res
                total_sessions = sum(scores.values()) # Not exactly, but for reporting mock

                report = (
                    f"🏆 Hourly System Report 🏆\n"
                    f"Current active algorithm: {best_algo}\n"
                    f"Scores across algorithms:\n"
                )

                for algo, score in scores.items():
                    report += f"- {algo}: {score} correct predictions\n"

                await self.send_message(report)
