import asyncio
import aiohttp
from loguru import logger

class Reporter:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.chat_id = "8308036418"
        self.is_running = False

    async def report_loop(self):
        self.is_running = True
        logger.info("Reporter started. Will report every 1 hour (3600 seconds).")
        while self.is_running:
            await asyncio.sleep(3600)  # Wait 1 hour

            # Force a re-optimization before reporting
            self.analyzer._simulate_and_optimize()

            stats = self.analyzer.stats
            total = stats["total_predicted"]
            correct = stats["correct_predictions"]
            acc = self.analyzer.get_accuracy()
            best_alg = self.analyzer.best_algorithm

            message = (
                f"📊 <b>BÁO CÁO TXMD5 THEO GIỜ</b>\n"
                f"---------------------------\n"
                f"🧠 <b>Thuật toán tối ưu hiện tại:</b> {best_alg}\n"
                f"🎯 <b>Tổng phiên đã dự đoán:</b> {total}\n"
                f"✅ <b>Số phiên đoán đúng:</b> {correct}\n"
                f"📈 <b>Tỷ lệ chính xác:</b> {acc:.2f}%\n"
            )

            logger.info("Hourly Report Generated:\n" + message)
            await self.send_telegram_message(message)

    async def send_telegram_message(self, message: str):
        # We don't have the bot token, only the bot link: http://t.me/botbaocaocc_bot
        # We will just print a warning that token is missing, but log the message.
        # If the user provides a token via env or later, it will work.
        import os
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN environment variable not set. Skipping Telegram notification.")
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        resp_text = await response.text()
                        logger.error(f"Failed to send Telegram message: {resp_text}")
                    else:
                        logger.success("Hourly report sent to Telegram successfully.")
            except Exception as e:
                logger.error(f"Error sending Telegram message: {e}")

    def stop(self):
        self.is_running = False
