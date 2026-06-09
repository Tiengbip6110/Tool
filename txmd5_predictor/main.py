import asyncio
import logging
from dotenv import load_dotenv

# Load env variables before other local imports
load_dotenv()

import aiohttp
from analyzer import SicBoAnalyzer
from bot import start_reporting_loop

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

async def fetch_sessions(analyzer):
    connector = aiohttp.TCPConnector(ssl=False)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        # Initial backtesting fetch
        try:
            async with session.get(API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    sessions_list = data.get('list', [])
                    for s in reversed(sessions_list):
                        analyzer.add_session(s)

                    # initial optimization
                    analyzer._simulate_and_optimize()
                    logger.info(f"Initial backtesting completed. Initial Best Algo: {analyzer.best_algo} ({analyzer.best_accuracy:.2f}%)")
        except Exception as e:
            logger.error(f"Error during initial fetch: {e}")

        # Polling loop
        while True:
            try:
                async with session.get(API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        sessions_list = data.get('list', [])
                        if sessions_list:
                            latest_session = sessions_list[0]
                            if analyzer.add_session(latest_session):
                                logger.info(f"New session added: {latest_session['id']} - Point: {latest_session['point']}")

                                # if previous prediction failed, we could re-optimize here.
                                # We'll just call _simulate_and_optimize to keep it simple and continuously re-evaluating.
                                analyzer._simulate_and_optimize()

                                prediction = analyzer.get_prediction()
                                logger.info(f"Next prediction: {prediction} (using {analyzer.best_algo})")
            except Exception as e:
                logger.error(f"Error during polling: {e}")

            await asyncio.sleep(0.5)

async def main():
    analyzer = SicBoAnalyzer()

    # run polling and reporting loops concurrently
    await asyncio.gather(
        fetch_sessions(analyzer),
        start_reporting_loop(analyzer)
    )

if __name__ == "__main__":
    asyncio.run(main())
