import os
import aiohttp
from typing import Dict, Any

class TelegramBot:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = "8308036418" # Targeted chat ID
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    async def send_telegram_message(self, text: str):
        """Sends a message to the target chat ID using aiohttp."""
        if not self.token:
            print(f"[Telegram Mock] Would send to {self.chat_id}: {text}")
            return

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status != 200:
                        error_data = await response.text()
                        print(f"Telegram API Error: {response.status} - {error_data}")
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

    async def format_and_send_hourly_report(self, prediction_stats: Dict[str, Any]):
        """Formats prediction stats and logic performance, and sends the report hourly."""
        best_algo = prediction_stats.get('best_algorithm', 'N/A')
        total_predictions = prediction_stats.get('total', 0)
        correct_predictions = prediction_stats.get('correct', 0)

        accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0.0

        report_text = (
            f"📊 <b>Hourly Algorithm Report</b>\n\n"
            f"🔹 <b>Best Algorithm:</b> {best_algo}\n"
            f"🔹 <b>Total Sessions Predicted:</b> {total_predictions}\n"
            f"🔹 <b>Accuracy:</b> {accuracy:.2f}%\n"
            f"🔹 <b>Correct Predictions:</b> {correct_predictions}\n"
            f"\n<i>Algorithm logic evaluated and optimized across historical data.</i>"
        )

        await self.send_telegram_message(report_text)
