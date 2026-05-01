import asyncio
import logging
from telegram import Bot

class TelegramReporter:
    def __init__(self, token="DUMMY_TOKEN", chat_id="8308036418"):
        self.chat_id = chat_id
        self.enabled = False
        if token and ":" in token:
            self.bot = Bot(token=token)
            self.enabled = True
        else:
            logging.warning("No valid TELEGRAM_BOT_TOKEN provided. Telegram reporting is disabled.")

    async def report_loop(self, analyzer):
        while True:
            await asyncio.sleep(3600)  # Wait 1 hour

            if not self.enabled:
                continue

            total_sessions = len(analyzer.history)
            best_alg = analyzer.best_algorithm
            stats = analyzer.accuracy_stats

            message = (
                f"Hourly Report\n"
                f"Total Sessions Analyzed: {total_sessions}\n"
                f"Best Algorithm: {best_alg}\n"
                f"Algorithm Stats:\n"
            )
            for alg, acc in stats.items():
                message += f" - {alg}: {acc*100:.2f}%\n"

            try:
                await self.bot.send_message(chat_id=self.chat_id, text=message)
                logging.info("Sent hourly Telegram report.")
            except Exception as e:
                logging.error(f"Failed to send Telegram report: {e}")
