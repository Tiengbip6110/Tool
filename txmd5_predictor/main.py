import asyncio
import aiohttp
import logging
import json
import time
from dotenv import load_dotenv

# Load env vars BEFORE importing local modules that use them
load_dotenv()

from analyzer import Txmd5Analyzer
from bot import TelegramBot
from ai_clients import AIClients

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

class MainApp:
    def __init__(self):
        self.analyzer = Txmd5Analyzer()
        self.bot = TelegramBot()
        self.ai_clients = AIClients()

        self.last_phien = None
        self.last_prediction = None
        self.last_prediction_confidence = 0.0

    async def fetch_api_data(self, session: aiohttp.ClientSession):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with session.get(API_URL, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # The api historical data is under 'list'
                    if 'list' in data and len(data['list']) > 0:
                        return data['list']
                else:
                    logger.warning(f"API returned status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching API data: {e}")
        return None

    async def poll_loop(self):
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            logger.info("Starting initial API fetch for backtesting...")
            initial_data = await self.fetch_api_data(session)
            if initial_data:
                self.analyzer.process_initial_batch(initial_data)
                self.last_phien = initial_data[0].get('id')
                logger.info(f"Initial backtesting complete. Latest phien: {self.last_phien}")
            else:
                logger.error("Failed to fetch initial data. Will keep trying in loop.")

            logger.info("Starting 500ms continuous polling loop.")
            while True:
                data_list = await self.fetch_api_data(session)

                if data_list:
                    latest_item = data_list[0]
                    current_phien = latest_item.get('id')

                    if current_phien != self.last_phien:
                        # New session detected
                        logger.info(f"New session detected: {current_phien} - Result: {latest_item.get('point')}")

                        # Verify previous prediction
                        actual_outcome = self.analyzer.determine_outcome(latest_item.get('point'))
                        if self.last_prediction:
                            if self.last_prediction == actual_outcome:
                                logger.info(f"Prediction CORRECT! Predicted: {self.last_prediction}")
                            else:
                                logger.info(f"Prediction WRONG! Predicted: {self.last_prediction}, Actual: {actual_outcome}")
                                logger.info("Triggering simulation and optimization due to error...")
                                self.analyzer._simulate_and_optimize()

                                # Optionally get AI suggestions on error (non-blocking)
                                asyncio.create_task(self.ai_clients.get_all_suggestions(self.analyzer.history[-20:]))

                        # Add to history
                        self.analyzer.add_history(latest_item)
                        self.last_phien = current_phien

                        # Make new prediction
                        pred, conf, logic = self.analyzer.ensemble_predict()
                        self.last_prediction = pred
                        self.last_prediction_confidence = conf

                        logger.info(f"Next Prediction: {pred} (Confidence: {conf*100:.1f}%) using {logic}")

                await asyncio.sleep(0.5)

    async def hourly_reporter(self):
        while True:
            # Wait for 1 hour (3600 seconds)
            await asyncio.sleep(3600)
            logger.info("Sending hourly optimization report...")
            stats = self.analyzer.get_stats_summary()
            await self.bot.send_hourly_report(stats)

    async def run(self):
        await self.bot.send_message("🚀 SUPER PROJECT AI Predictor started. Initiating backtesting and polling loop...")

        # Run polling and reporting concurrently
        poll_task = asyncio.create_task(self.poll_loop())
        report_task = asyncio.create_task(self.hourly_reporter())

        await asyncio.gather(poll_task, report_task)

if __name__ == '__main__':
    app = MainApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Application stopped manually.")
