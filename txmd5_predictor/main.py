import asyncio
import aiohttp
import ssl
import time
import logging
import os
from analyzer import PredictorAnalyzer

# Configuration
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
POLL_INTERVAL = 0.5 # 500ms
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8308036418")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

analyzer = PredictorAnalyzer()

async def send_telegram_message(session, message):
    logging.info(f"TELEGRAM REPORT:\n{message}")
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                logging.error(f"Failed to send telegram message: {await response.text()}")
    except Exception as e:
        logging.error(f"Error sending telegram message: {e}")

async def poll_api(session):
    try:
        async with session.get(API_URL) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("list", [])
    except Exception as e:
        logging.error(f"Error fetching API: {e}")
    return []

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}) as session:
        last_session_id = None
        current_prediction = None
        history = []

        last_report_time = time.time()

        while True:
            sessions_list = await poll_api(session)
            if sessions_list:
                # API returns list in descending order, we want ascending for history
                sessions_list.sort(key=lambda x: x["id"])

                latest_session = sessions_list[-1]
                latest_id = latest_session["id"]

                if last_session_id is None:
                    last_session_id = latest_id
                    history = sessions_list
                    current_prediction = analyzer.predict(history)
                    logging.info(f"Initial setup. Last session: {latest_id}, Next prediction: {current_prediction} (Logic: {analyzer.best_logic})")
                elif latest_id > last_session_id:
                    # New result
                    new_sessions = [s for s in sessions_list if s["id"] > last_session_id]
                    history.extend(new_sessions)

                    actual_result = latest_session.get("resultTruyenThong")
                    logging.info(f"New session {latest_id} ended. Result: {actual_result}")

                    prediction_failed = False
                    if current_prediction:
                        if current_prediction == actual_result:
                            logging.info(f"Prediction WON! Expected {current_prediction}, got {actual_result}.")
                        else:
                            logging.info(f"Prediction LOST! Expected {current_prediction}, got {actual_result}.")
                            prediction_failed = True

                    last_session_id = latest_id

                    # Make new prediction
                    current_prediction = analyzer.predict(history, prediction_failed=prediction_failed)
                    logging.info(f"Next prediction: {current_prediction} (Logic: {analyzer.best_logic})")

            # Check if it's time for hourly report and optimization
            current_time = time.time()
            if current_time - last_report_time >= 3600:
                # User requested: every 1 hour the algorithm will optimize all the predicted sessions
                logging.info("Performing hourly full history optimization.")
                analyzer._simulate_and_optimize(history)

                stats = "\n".join([f"{k}: {v:.2f}%" for k, v in analyzer.accuracy_stats.items()])
                report = f"Hourly Report:\nBest Logic: {analyzer.best_logic}\nStats:\n{stats}"
                await send_telegram_message(session, report)
                last_report_time = current_time

            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
