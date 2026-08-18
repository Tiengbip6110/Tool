import asyncio
import aiohttp
import logging
from dotenv import load_dotenv

# Load env before importing local modules that might rely on them
load_dotenv()

from analyzer import Analyzer
from bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

async def fetch_initial_data(analyzer):
    """
    Perform an initial backtesting fetch on startup, parsing historical
    sessions in reverse order (oldest to newest) to train the analyzer.
    """
    logger.info("Fetching initial data...")
    connector = aiohttp.TCPConnector(ssl=False)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        try:
            async with session.get(API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    sessions = data.get('list', [])

                    if not sessions:
                        logger.warning("No sessions returned from API during initial fetch.")
                        return

                    logger.info(f"Loaded {len(sessions)} historical sessions.")

                    # Process oldest to newest
                    for s in reversed(sessions):
                        analyzer.add_session(s)

                    # Pre-train / optimize on initial data
                    await analyzer._simulate_and_optimize()
                else:
                    logger.error(f"Initial fetch failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error during initial fetch: {e}")

async def polling_loop(analyzer):
    """
    Actively poll the API every 500ms for new data.
    """
    logger.info("Starting active polling loop (500ms)...")
    connector = aiohttp.TCPConnector(ssl=False)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    last_prediction = None
    last_predicted_id = None

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        while True:
            try:
                async with session.get(API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        sessions = data.get('list', [])

                        if len(sessions) >= 2:
                            # index 0 is currently active (unresolved), index 1 is the latest finished
                            latest_finished = sessions[1]
                            current_active = sessions[0]

                            is_new = analyzer.add_session(latest_finished)

                            if is_new:
                                logger.info(f"New session finished: {latest_finished.get('id')} - Result: {latest_finished.get('resultTruyenThong') or latest_finished.get('result')} (Point: {latest_finished.get('point')})")

                                # Check last prediction
                                if last_prediction and last_predicted_id == latest_finished.get('id'):
                                    actual = latest_finished.get('resultTruyenThong') or latest_finished.get('result')
                                    if last_prediction != actual:
                                        logger.info(f"Prediction failed (Predicted {last_prediction}, Actual {actual}). Re-optimizing...")
                                        await analyzer._simulate_and_optimize()
                                    else:
                                        logger.info("Prediction successful! 🎉")

                                # Predict for current_active
                                next_pred = await analyzer.predict_next()
                                if next_pred:
                                    last_prediction = next_pred
                                    last_predicted_id = current_active.get('id')
                                    logger.info(f"Predicting {last_prediction} for session {last_predicted_id} using {analyzer.best_algorithm}")

                    else:
                        logger.error(f"Polling failed with status {response.status}")
            except Exception as e:
                logger.error(f"Error during polling: {e}")

            await asyncio.sleep(0.5)

async def main():
    analyzer = Analyzer()
    bot = TelegramBot(analyzer)

    # 1. Fetch initial data
    await fetch_initial_data(analyzer)

    # 2. Start concurrent tasks
    tasks = [
        asyncio.create_task(polling_loop(analyzer)),
        asyncio.create_task(bot.poll_updates()),
        asyncio.create_task(bot.hourly_reporter())
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
