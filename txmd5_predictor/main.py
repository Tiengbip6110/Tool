import asyncio
import aiohttp
import logging
import time
from dotenv import load_dotenv

# Load env before local imports
load_dotenv()

from analyzer import Analyzer
from bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

class MainApp:
    def __init__(self):
        self.analyzer = Analyzer()
        self.bot = TelegramBot()
        self.last_id = None
        self.last_prediction = None
        self.last_report_time = time.time()
        self.total_predictions = 0
        self.correct_predictions = 0

    async def fetch_sessions(self, session):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            async with session.get(API_URL, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('list', [])
                else:
                    logger.error(f"API returned status: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching API: {e}")
            return []

    async def hourly_report_loop(self):
        while True:
            await asyncio.sleep(60)
            now = time.time()
            if now - self.last_report_time >= 3600:
                self.last_report_time = now

                acc = 0
                if self.total_predictions > 0:
                    acc = self.correct_predictions / self.total_predictions * 100

                msg = (
                    f"🤖 <b>Báo cáo hệ thống (1 giờ)</b>\n\n"
                    f"📊 <b>Tổng số dự đoán:</b> {self.total_predictions}\n"
                    f"✅ <b>Chính xác:</b> {self.correct_predictions} ({acc:.2f}%)\n"
                    f"🧠 <b>Thuật toán hiện tại:</b> {self.analyzer.best_algo}\n"
                    f"🎯 <b>Độ chính xác thuật toán:</b> {self.analyzer.best_algo_accuracy*100:.2f}%"
                )
                await self.bot.send_message(msg)

                # Reset counters after report
                self.total_predictions = 0
                self.correct_predictions = 0

    async def run(self):
        # Use a single aiohttp session for connection pooling
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:

            # Initial load and backtest
            logger.info("Fetching initial history for backtesting...")
            initial_sessions = await self.fetch_sessions(session)
            if initial_sessions:
                # Add in reverse (oldest first) for proper training
                for s in reversed(initial_sessions):
                    self.analyzer.add_session(s)

                await self.analyzer.simulate_and_optimize()
                if self.analyzer.history:
                    self.last_id = self.analyzer.history[0].get('id')
                    self.last_prediction = await self.analyzer.predict_next()
                    logger.info(f"Initial prediction for next session: {self.last_prediction}")

            # Start report loop
            asyncio.create_task(self.hourly_report_loop())

            # Send startup message
            await self.bot.send_message("🚀 Hệ thống Super Project đã khởi động và đang phân tích!")

            logger.info("Entering live polling loop...")
            while True:
                sessions = await self.fetch_sessions(session)
                if sessions and len(sessions) > 1:
                    latest = sessions[0]
                    latest_finished = sessions[1] # The one that just finished

                    curr_id = latest.get('id')

                    if curr_id != self.last_id:
                        # New session started!
                        logger.info(f"New session detected: {curr_id}")

                        # Evaluate last prediction using latest_finished
                        if self.last_prediction and self.last_id == latest_finished.get('id'):
                            actual_point = latest_finished.get('point', 0)
                            actual_result = latest_finished.get('result') or latest_finished.get('resultTruyenThong')
                            if not actual_result:
                                actual_result = "Tài" if actual_point >= 11 else "Xỉu"

                            self.total_predictions += 1
                            if self.last_prediction == actual_result:
                                self.correct_predictions += 1
                                logger.info(f"Prediction CORRECT! (Predicted: {self.last_prediction}, Actual: {actual_result})")
                            else:
                                logger.info(f"Prediction WRONG! (Predicted: {self.last_prediction}, Actual: {actual_result})")
                                # Trigger re-optimization on failure
                                await self.analyzer.simulate_and_optimize()

                        # Update history
                        self.analyzer.add_session(latest_finished)
                        self.analyzer.add_session(latest)

                        self.last_id = curr_id

                        # Generate new prediction
                        self.last_prediction = await self.analyzer.predict_next()
                        logger.info(f"New Prediction for {curr_id}: {self.last_prediction}")
                    else:
                        # Update current session info
                        self.analyzer.add_session(latest)

                await asyncio.sleep(0.5) # Poll every 500ms

if __name__ == "__main__":
    app = MainApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")