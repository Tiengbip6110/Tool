import asyncio
import logging
import aiohttp
import sys
from datetime import datetime, timedelta

from config import POLL_INTERVAL
from api_client import fetch_sessions
from analyzer import Analyzer
from bot import send_telegram_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def report_task(analyzer: Analyzer):
    """Sends a report to Telegram every hour."""
    while True:
        await asyncio.sleep(3600)  # 1 hour
        stats = analyzer.get_stats()
        message = f"<b>📊 TXMD5 Predictor Hourly Report</b>\n\n{stats}"
        logger.info(f"Sending hourly report: {stats}")
        await send_telegram_message(message)

async def main():
    analyzer = Analyzer()

    # Disable SSL verification as per requirements
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        logger.info("Starting initial backtesting and priming...")

        # Initial fetch to prime the analyzer
        initial_data = await fetch_sessions(session)
        if initial_data:
            # Parse in reverse (oldest to newest) to build history naturally
            for item in reversed(initial_data):
                analyzer.update_history(item)
            logger.info(f"Primed with {len(initial_data)} historical records.")
            # Run an initial optimization
            analyzer._simulate_and_optimize()

        logger.info("Starting prediction loop...")

        # Start background reporting task
        asyncio.create_task(report_task(analyzer))

        last_processed_id = None

        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            logger.info("Test mode completed successfully.")
            return

        while True:
            try:
                data = await fetch_sessions(session)
                if data and len(data) >= 2:
                    # Index 0 is the currently rolling session
                    # Index 1 is the latest finished session
                    latest_finished = data[1]
                    current_rolling = data[0]

                    # Update history with the latest finished session
                    analyzer.update_history(latest_finished)

                    # If this is a new finished session, evaluate our last prediction
                    if latest_finished.get('id') != last_processed_id:
                        analyzer.evaluate_last_prediction()
                        last_processed_id = latest_finished.get('id')

                        # Generate a new prediction for the current rolling session
                        prediction = await analyzer.get_prediction_async(skip_llm=False)
                        analyzer.last_prediction = prediction
                        analyzer.last_prediction_session_id = current_rolling.get('id')

                        logger.info(f"New Session: {current_rolling.get('id')}. Predicted: {prediction}")

            except Exception as e:
                logger.error(f"Error in main loop: {e}")

            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
