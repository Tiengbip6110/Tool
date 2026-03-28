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

    try:
        await asyncio.gather(poller_task, reporter_task)
    except KeyboardInterrupt:
        logger.info("Stopping system...")
        api_client.stop()
        reporter.stop()
        await asyncio.gather(poller_task, reporter_task, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
