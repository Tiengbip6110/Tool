import asyncio
import logging
from datetime import datetime, timedelta

from data_fetcher import DataFetcher
from analyzer import Analyzer
from telegram_bot import TelegramReporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
REPORT_INTERVAL_SECONDS = 3600  # 1 hour

class Coordinator:
    def __init__(self):
        self.fetcher = DataFetcher(interval_ms=500)
        self.analyzer = Analyzer()
        self.reporter = TelegramReporter()
        self.last_report_time = datetime.now() - timedelta(seconds=REPORT_INTERVAL_SECONDS - 10) # Report 10s after start

    async def process_new_session(self, session_data: dict):
        # Callback from DataFetcher when a new session arrives
        await self.analyzer.add_session(session_data)

        # Check if it's time to report
        now = datetime.now()
        if (now - self.last_report_time).total_seconds() >= REPORT_INTERVAL_SECONDS:
            await self.send_report()
            self.last_report_time = now

    async def send_report(self):
        if not self.analyzer.history:
            logger.warning("No history to report yet.")
            return

        last_session = self.analyzer.history[-1]
        best_algo, predicted_result, accuracy = self.analyzer.get_best_prediction()

        # If still no best algo due to lack of data
        if not best_algo:
            best_algo = "waiting_for_data"
            predicted_result = "TAI"
            accuracy = 0.0

        msg = self.reporter.format_report(
            session_id=last_session["id"],
            result=last_session["result"],
            point=last_session["point"],
            dices=last_session["dices"],
            predicted_next=predicted_result,
            best_algo=best_algo,
            accuracy=accuracy
        )

        logger.info("Sending hourly Telegram report.")
        await self.reporter.send_message(msg)

    async def run(self):
        logger.info("Starting TXMD5 Predictor System...")
        # Register callback
        self.fetcher.add_callback(self.process_new_session)

        # We start the fetcher loop. It runs indefinitely.
        await self.fetcher.run()

async def main():
    coordinator = Coordinator()
    await coordinator.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped manually.")
