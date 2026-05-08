import asyncio
import aiohttp
import logging
import os
import json
import time
from dotenv import load_dotenv

# Load env vars first before importing local modules that use them
load_dotenv()

from analyzer import Analyzer
from bot import bot
from ai_clients import ai_clients

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class PredictorEngine:
    def __init__(self):
        self.analyzer = Analyzer()
        self.last_session_id = None
        self.last_prediction = None
        self.last_report_time = time.time()

    async def fetch_data(self, session):
        headers = {"User-Agent": USER_AGENT}
        try:
            async with session.get(API_URL, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"API returned status: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching API data: {e}")
            return None

    async def initial_backtest(self, session):
        logger.info("Starting initial backtest...")
        data = await self.fetch_data(session)
        if data and 'list' in data:
            sessions = data['list']
            # API might return newest first. We need oldest first to train forward.
            # Assuming sessions[0] is newest.
            sessions.reverse()
            for s in sessions:
                if 'id' in s and 'point' in s:
                    self.analyzer.add_session({'id': s['id'], 'point': s['point']})
                    self.last_session_id = s['id']

            logger.info(f"Loaded {len(sessions)} historical sessions. Optimizing...")
            self.analyzer._simulate_and_optimize()
            logger.info("Initial backtest complete.")
            await bot.send_message("Initial backtest complete. Bot starting up.\n\n" + self.analyzer.get_stats())
        else:
            logger.error("Failed to fetch initial data for backtest. Format might be wrong.")

    async def run_loop(self):
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            await self.initial_backtest(session)

            while True:
                try:
                    data = await self.fetch_data(session)

                    if data and 'list' in data:
                        sessions = data['list']
                    if sessions:
                        newest_session = sessions[0] # assuming index 0 is newest

                        if 'id' in newest_session and 'point' in newest_session:
                            current_id = newest_session['id']

                            if self.last_session_id != current_id:
                                # We have a new session!
                                logger.info(f"New session detected: {current_id} (Point: {newest_session['point']})")

                                # Verify last prediction if we made one
                                if self.last_prediction:
                                    actual_result = self.analyzer._get_result_from_point(newest_session['point'])
                                    if self.last_prediction != actual_result:
                                        logger.info(f"Prediction failed! Predicted {self.last_prediction}, got {actual_result}. Triggering optimization.")
                                        self.analyzer._simulate_and_optimize()
                                    else:
                                        logger.info(f"Prediction correct! Predicted {self.last_prediction}, got {actual_result}.")

                                # Add new session to history
                                self.analyzer.add_session({'id': current_id, 'point': newest_session['point']})
                                self.last_session_id = current_id

                                # Make next prediction
                                next_id = current_id + 1
                                self.last_prediction = await self.analyzer.ensemble_predict(ai_clients)
                                logger.info(f"Predicting for session {next_id}: {self.last_prediction} (Algorithm: {self.analyzer.best_algorithm})")

                    # Check for hourly report
                    current_time = time.time()
                    if current_time - self.last_report_time > 3600: # 1 hour
                        logger.info("Sending hourly report...")
                        report_text = f"Hourly Update\n\n{self.analyzer.get_stats()}"
                        await bot.send_message(report_text)
                        self.last_report_time = current_time

                except Exception as e:
                    logger.error(f"Error in main loop: {e}")

                await asyncio.sleep(0.5) # Poll every 500ms

async def main():
    engine = PredictorEngine()
    await engine.run_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down predictor.")
