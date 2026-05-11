import asyncio
import aiohttp
import logging
import os
from dotenv import load_dotenv

# Load env before importing local modules per memory constraints
load_dotenv()

from analyzer import SicBoAnalyzer
from bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

class MainApp:
    def __init__(self):
        self.analyzer = SicBoAnalyzer()
        self.bot = TelegramBot()
        self.is_running = False

    async def fetch_data(self, session: aiohttp.ClientSession):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            async with session.get(API_URL, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('list', [])
                else:
                    logger.error(f"API Error: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
        return []

    async def main_loop(self):
        self.is_running = True

        # Start bot and report loop
        await self.bot.start_bot()
        report_task = asyncio.create_task(
            self.bot.report_loop(
                self.analyzer.get_stats,
                self.analyzer._simulate_and_optimize
            )
        )

        # Use TCPConnector with ssl=False per memory constraints
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Initial Backtest Phase
            logger.info("Fetching initial data for backtesting...")
            initial_data = await self.fetch_data(session)
            if initial_data:
                # History is returned newest to oldest, reverse it to oldest to newest for training
                self.analyzer.add_history(initial_data[::-1])
                await self.analyzer._simulate_and_optimize()

            # Continuous polling phase
            while self.is_running:
                data = await self.fetch_data(session)
                if data:
                    # Look at the most recent session
                    latest_session = data[0] # assuming index 0 is newest

                    if not self.analyzer.history or str(latest_session['id']) != str(self.analyzer.history[-1]['id']):
                        # We have a new session! Verify previous prediction
                        self.analyzer.verify_prediction(latest_session)

                        # Add to history and predict next
                        self.analyzer.add_history([latest_session])
                        next_pred = await self.analyzer.predict_next()
                        logger.info(f"🔮 Predicted NEXT session will be: {next_pred}")

                await asyncio.sleep(0.5) # 500ms reset

    async def run(self):
        try:
            await self.main_loop()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.is_running = False
            await self.bot.stop_bot()

if __name__ == "__main__":
    app = MainApp()
    asyncio.run(app.run())
