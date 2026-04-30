import asyncio
from loguru import logger
from api_client import APIClient
from analyzer import Analyzer
from reporter import Reporter

async def main():
    logger.info("Starting TXMD5 Predictor System...")

    analyzer = Analyzer()
    api_client = APIClient(analyzer=analyzer)
    reporter = Reporter(analyzer=analyzer)

    # Connect the api_client's new data event to the analyzer's processing method
    api_client.add_callback(analyzer.process_new_session)

    # Run API Poller and Reporter concurrently
    poller_task = asyncio.create_task(api_client.poll())
    reporter_task = asyncio.create_task(reporter.report_loop())

    # Limit the logical search to 24 hours (86400 seconds)
    DURATION = 86400

    try:
        logger.info(f"System will run for a maximum of 24 hours ({DURATION} seconds).")
        await asyncio.wait_for(
            asyncio.gather(poller_task, reporter_task),
            timeout=DURATION
        )
    except asyncio.TimeoutError:
        logger.info("24-hour logical search duration reached. Stopping system gracefully.")
        api_client.stop()
        reporter.stop()
        # Wait for tasks to finish shutdown
        await asyncio.gather(poller_task, reporter_task, return_exceptions=True)
        logger.info("System successfully shut down after 24 hours.")
    except KeyboardInterrupt:
        logger.info("Stopping system (KeyboardInterrupt)...")
        api_client.stop()
        reporter.stop()
        await asyncio.gather(poller_task, reporter_task, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
