import asyncio
import aiohttp
import logging
import json
from dotenv import load_dotenv

# Memory: Load dotenv before importing local modules
load_dotenv()

from analyzer import Analyzer
from bot import send_telegram_message

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
POLL_INTERVAL = 0.5  # 500ms

analyzer = Analyzer()
stats = {
    "total_predictions": 0,
    "correct_predictions": 0
}

async def fetch_initial_data(session):
    try:
        # Standard browser User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        async with session.get(API_URL, headers=headers) as response:
            if response.status == 200:
                data = await response.json()

                # Memory: Data is under the 'list' key
                sessions = data.get("list", [])

                if sessions:
                    logger.info(f"Fetched {len(sessions)} initial sessions.")
                    # Memory: Parse in reverse order (oldest to newest)
                    for s in reversed(sessions):
                        analyzer.add_session(s)

                    # Initial backtest optimization
                    logger.info("Running initial _simulate_and_optimize...")
                    best_algo = analyzer._simulate_and_optimize()
                    if best_algo:
                        logger.info(f"Initial optimization complete. Best Algo: {best_algo[0]} (Accuracy: {best_algo[1]:.2%})")
                    return True
            else:
                logger.error(f"Failed to fetch initial data: HTTP {response.status}")
                return False
    except Exception as e:
        logger.error(f"Exception during initial fetch: {e}")
        return False

async def polling_loop(session):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    last_session_id = None
    if analyzer.history:
        last_session_id = analyzer.history[-1].get("id")

    current_prediction = analyzer.get_prediction()
    logger.info(f"Initial Prediction for next session: {current_prediction}")

    while True:
        try:
            async with session.get(API_URL, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    sessions = data.get("list", [])
                    if sessions:
                        latest_session = sessions[0]
                        latest_id = latest_session.get("id")

                        if last_session_id and latest_id != last_session_id:
                            # A new session has started, meaning the previous session has finished
                            # The finished session is now at index 1 in the API response
                            if len(sessions) > 1 and sessions[1].get("id") == last_session_id:
                                finished_session = sessions[1]
                                actual_result = finished_session.get("resultTruyenThong") or finished_session.get("result")
                                logger.info(f"Session {last_session_id} finished. Result: {actual_result}")

                                stats["total_predictions"] += 1
                                if current_prediction == actual_result:
                                    stats["correct_predictions"] += 1
                                    logger.info("Prediction CORRECT!")
                                else:
                                    logger.info("Prediction INCORRECT. Triggering optimization...")
                                    best_algo = analyzer._simulate_and_optimize()
                                    if best_algo:
                                        logger.info(f"Optimization complete. New Best Algo: {best_algo[0]} (Accuracy: {best_algo[1]:.2%})")

                                # Add the finished session to history with its results
                                analyzer.add_session(finished_session)

                            # Update the last seen session to the newly started one
                            last_session_id = latest_id

                            # Generate prediction for the newly started session (which will end next)
                            current_prediction = analyzer.get_prediction()
                            logger.info(f"Next Prediction for session {latest_id}: {current_prediction}")

        except Exception as e:
            logger.error(f"Error in polling loop: {e}")

        await asyncio.sleep(POLL_INTERVAL)

async def report_loop():
    while True:
        await asyncio.sleep(3600)  # Wait 1 hour
        try:
            acc = 0
            if stats["total_predictions"] > 0:
                acc = (stats["correct_predictions"] / stats["total_predictions"]) * 100

            report_msg = (
                f"📊 *TxMD5 Algorithm Report*\n\n"
                f"🧠 *Best Algorithm*: `{analyzer.best_algo}`\n"
                f"🎯 *Total Predictions*: {stats['total_predictions']}\n"
                f"✅ *Correct*: {stats['correct_predictions']}\n"
                f"📈 *Accuracy*: {acc:.2f}%\n"
            )
            await send_telegram_message(report_msg)

            # Reset stats for the next hour if desired (or keep lifetime stats)
            # stats["total_predictions"] = 0
            # stats["correct_predictions"] = 0

        except Exception as e:
            logger.error(f"Error in report loop: {e}")

async def main():
    # Memory: Disable SSL verification by passing ssl=False to aiohttp.TCPConnector
    connector = aiohttp.TCPConnector(ssl=False)

    # Memory: aiohttp.ClientSession() context manager opened outside the loop
    async with aiohttp.ClientSession(connector=connector) as session:
        # 1. Fetch initial data and run backtesting
        success = await fetch_initial_data(session)
        if not success:
            logger.warning("Could not complete initial setup. Exiting.")
            return

        logger.info("Main script setup completed. Starting polling loop...")

        # 2. Start the continuous polling loop
        polling_task = asyncio.create_task(polling_loop(session))

        # 3. Start the hourly report loop
        report_task = asyncio.create_task(report_loop())

        # Wait for tasks (this will run indefinitely)
        await asyncio.gather(polling_task, report_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
