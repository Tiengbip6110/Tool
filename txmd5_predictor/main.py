import os
from dotenv import load_dotenv

# Load env variables before anything else
load_dotenv()

import asyncio
import aiohttp
import logging
from analyzer import Analyzer
from bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

class App:
    def __init__(self):
        self.analyzer = Analyzer()
        self.bot = TelegramBot(os.getenv('TELEGRAM_TOKEN', ''), os.getenv('TELEGRAM_CHAT_ID', '8308036418'))
        self.last_session_id = None
        self.stats = {'sessions_predicted': 0}
        self.last_prediction = None
        self.last_predicted_session_id = None

    async def fetch_data(self, session):
        headers = {'User-Agent': USER_AGENT}
        try:
            async with session.get(API_URL, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API returned status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None

    async def run(self):
        logger.info("Starting TXMD5 Predictor...")

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Initial fetch to train analyzer
            logger.info("Fetching initial history...")
            initial_data = await self.fetch_data(session)
            if initial_data and 'data' in initial_data and 'list' in initial_data['data']:
                history_list = initial_data['data']['list']
            elif initial_data and 'list' in initial_data:
                # Based on memory: "historical session data under the 'list' key"
                history_list = initial_data['list']
            else:
                history_list = []

            if history_list:
                # Parse in reverse order (oldest to newest)
                for item in reversed(history_list):
                    self.analyzer.add_session(item)
                    self.last_session_id = item.get('id')
                logger.info(f"Loaded {len(history_list)} historical sessions.")
                self.analyzer._simulate_and_optimize()

            # Start bot tasks
            asyncio.create_task(self.bot.report_loop(self.analyzer, lambda: self.stats))
            asyncio.create_task(self.bot.poll_commands(lambda: self.stats))

            # Main polling loop
            while True:
                data = await self.fetch_data(session)

                if data:
                    list_data = data.get('list', data.get('data', {}).get('list', []))
                    if list_data:
                        latest = list_data[0] # Assuming first item is latest
                        latest_id = latest.get('id')

                        if latest_id != self.last_session_id:
                            logger.info(f"New session detected: {latest_id}")

                            # If we made a prediction for this session, check it
                            if self.last_prediction and self.last_predicted_session_id == latest_id:
                                actual_result = self.analyzer._get_result(latest)
                                if self.last_prediction != actual_result:
                                    logger.info(f"Prediction failed (Predicted: {self.last_prediction}, Actual: {actual_result}). Triggering re-optimization.")
                                    self.analyzer._simulate_and_optimize()
                                else:
                                    logger.info(f"Prediction correct: {actual_result}")

                            self.analyzer.add_session(latest)
                            self.last_session_id = latest_id

                            # Make next prediction
                            prediction = self.analyzer.predict()
                            if prediction:
                                self.last_prediction = prediction
                                # In real app, the next session ID might be known or just latest_id + 1
                                # For logging purposes:
                                self.last_predicted_session_id = latest_id + 1 if isinstance(latest_id, int) else None
                                self.stats['sessions_predicted'] += 1
                                logger.info(f"Predicted next session: {prediction} using {self.analyzer.best_algorithm}")

                await asyncio.sleep(0.5)

if __name__ == "__main__":
    app = App()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Shutting down.")
