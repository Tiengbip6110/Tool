import os
import aiohttp
import asyncio

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "8308036418")
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, text):
        """Sends a text message to the configured chat_id."""
        if not self.token or self.token == 'your_telegram_bot_token':
            print(f"[Telegram Bot] Not configured. Message skipped: {text[:50]}...")
            return

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/sendMessage", json=payload) as response:
                    if response.status != 200:
                        print(f"[Telegram Bot] Failed to send message: {await response.text()}")
        except Exception as e:
            print(f"[Telegram Bot] Error sending message: {e}")

    async def report_hourly(self, analyzer, total_sessions):
        """Sends an hourly report with the current best algorithm and statistics."""
        message = (
            f"<b>📊 BÁO CÁO HÀNG GIỜ TXMD5</b>\n\n"
            f"<b>⚙️ Thuật toán tối ưu:</b> {analyzer.best_algo_name}\n"
            f"<b>🎯 Tỷ lệ thắng (Win rate):</b> {analyzer.win_rate:.2f}%\n"
            f"<b>🔄 Tổng số phiên đã theo dõi:</b> {total_sessions}\n"
            f"<b>✅ Các thuật toán đang chạy:</b> Random, Markov, Trend, Recent Majority, Sum Analysis, LLM Ensemble\n\n"
            f"<i>Bot đang liên tục cập nhật và tối ưu...</i>"
        )
        await self.send_message(message)
