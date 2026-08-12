import asyncio
import aiohttp
import logging
import time
import nest_asyncio

# Apply nest_asyncio to allow nested event loops if needed by some async integrations
nest_asyncio.apply()

# Load environment variables before local imports
from dotenv import load_dotenv
load_dotenv()

from analyzer import Analyzer
from bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
POLL_INTERVAL = 0.5  # 500ms
REPORT_INTERVAL = 3600  # 1 hour in seconds

async def fetch_sessions(session):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # User-Agent and ssl=False required as per memory to prevent connection failures
        async with session.get(API_URL, headers=headers, ssl=False, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('list', [])
            else:
                logger.error(f"Failed to fetch data, status: {response.status}")
                return []
    except Exception as e:
        logger.error(f"Error fetching API: {e}")
        return []

async def main_loop():
    analyzer = Analyzer()
    bot = TelegramBot()

    # Start bot polling in background
    bot_task = asyncio.create_task(bot.start_polling())

    last_report_time = time.time()
    last_predicted_session_id = None
    current_prediction = None

    # A single ClientSession for API polling
    async with aiohttp.ClientSession() as session:
        logger.info("Starting initial backtesting phase...")
        initial_sessions = await fetch_sessions(session)

        if initial_sessions:
            # Parse reverse history (oldest to newest)
            for s in reversed(initial_sessions):
                analyzer.add_session(s)

            # Initial optimization
            await analyzer._simulate_and_optimize()
            logger.info("Initial backtesting complete.")
        else:
            logger.warning("Could not fetch initial history.")

        logger.info("Entering active polling loop...")
        while True:
            try:
                sessions = await fetch_sessions(session)

                if not sessions:
                    await asyncio.sleep(POLL_INTERVAL)
                    continue

                # Update history with the latest (index 0) - it might be ongoing
                latest_session = sessions[0]
                analyzer.add_session(latest_session)

                # If we have a finished session at index 1 to evaluate our previous prediction against
                if len(sessions) > 1:
                    finished_session = sessions[1]
                    finished_id = finished_session['id']

                    # Ensure the finished session with the actual result updates our history
                    analyzer.add_session(finished_session)

                    if last_predicted_session_id == finished_id and current_prediction:
                        actual = finished_session.get('resultTruyenThong')
                        if actual:
                            analyzer.total_predictions += 1
                            if current_prediction == actual:
                                analyzer.correct_predictions += 1
                            else:
                                # Re-optimize on failure (as per requirements)
                                logger.info(f"Prediction failed for session {finished_id}. Re-optimizing...")
                                await analyzer._simulate_and_optimize()

                            last_predicted_session_id = None
                            current_prediction = None

                # Make a new prediction for the ongoing session if we haven't yet
                if last_predicted_session_id != latest_session['id']:
                    current_prediction = await analyzer.predict_next(skip_llm=False)
                    last_predicted_session_id = latest_session['id']
                    logger.info(f"New prediction for session {last_predicted_session_id}: {current_prediction} (Algo: {analyzer.current_optimal_algo})")

                # Check if it's time to send an hourly report
                current_time = time.time()
                if current_time - last_report_time >= REPORT_INTERVAL:
                    logger.info("Sending hourly report...")
                    stats = analyzer.get_stats()
                    stats['next_predictions'] = current_prediction
                    await bot.send_hourly_report(stats)
                    last_report_time = current_time

            except Exception as e:
                logger.error(f"Error in main polling loop: {e}")

            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Shutting down...")