import aiohttp
import os
import asyncio

class TelegramReporter:
    def __init__(self, chat_id="8308036418"):
        self.chat_id = chat_id
        # Expect the user to provide TELEGRAM_BOT_TOKEN environment variable
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

    async def send_report(self, text):
        if self.bot_token == "YOUR_BOT_TOKEN_HERE":
            print(f"Telegram Bot Token not set. Would have sent: {text}")
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        print("Report sent successfully.")
                    else:
                        print(f"Failed to send report. Status: {response.status}")
        except Exception as e:
            print(f"Error sending report: {e}")

    async def report_loop(self, analyzer):
        while True:
            # Wait for 1 hour (3600 seconds)
            await asyncio.sleep(3600)

            total = analyzer.total_predictions
            correct = analyzer.correct_predictions
            accuracy = (correct / total * 100) if total > 0 else 0
            best_algo = analyzer.current_best_algorithm or "None"

            report_text = (
                f"<b>📊 BÁO CÁO DỰ ĐOÁN TÀI XỈU MD5 📊</b>\n"
                f"🔹 <b>Tổng số phiên dự đoán:</b> {total}\n"
                f"🔹 <b>Dự đoán đúng:</b> {correct}\n"
                f"🔹 <b>Tỷ lệ chính xác:</b> {accuracy:.2f}%\n"
                f"🔹 <b>Thuật toán tốt nhất hiện tại:</b> {best_algo}\n"
            )

            await self.send_report(report_text)
