import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv() # Load variables before importing local modules that might rely on them

from analyzer import EnsembleAnalyzer
from bot import send_telegram_message, start_hourly_reporting_loop

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
POLL_INTERVAL = 0.5  # 500 ms

analyzer = EnsembleAnalyzer()
predicted_count = 0
last_session_id = None
current_prediction = None

async def fetch_sessions(session: aiohttp.ClientSession):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        async with session.get(API_URL, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("list", [])
            else:
                return None
    except Exception as e:
        return None

async def initialize_analyzer(session: aiohttp.ClientSession):
    print("Fetching initial data for backtesting...")
    data = await fetch_sessions(session)
    if not data:
        print("Failed to fetch initial data.")
        return None

    # Reverse to process oldest first
    historical_data = list(reversed(data))

    for item in historical_data:
        analyzer.feed_data(item)

    analyzer.simulate_and_optimize()
    print("Initialization complete.")

    if historical_data:
        return historical_data[-1].get("id")
    return None

def get_prediction_count():
    global predicted_count
    return predicted_count

async def main():
    global last_session_id, current_prediction, predicted_count

    print("Starting TXMD5 Predictor...")
    await send_telegram_message("🚀 <b>TXMD5 Predictor Bot Started</b>\nInitializing and backtesting...")

    # Configure connector to skip SSL verification (ssl=False)
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        last_session_id = await initialize_analyzer(session)

        # Start the hourly reporting task in the background
        asyncio.create_task(start_hourly_reporting_loop(analyzer, get_prediction_count))

        print("Entering polling loop...")

        # Make the first prediction
        current_prediction = analyzer.get_prediction()
        print(f"Initial Prediction for next session: {current_prediction} (Logic: {analyzer.best_logic})")

        while True:
            data_list = await fetch_sessions(session)

            if data_list and len(data_list) > 0:
                latest_session = data_list[0]
                latest_id = latest_session.get("id")

                # If a new session has appeared
                if latest_id != last_session_id:
                    actual_result = latest_session.get("resultTruyenThong")
                    point = latest_session.get("point")

                    if actual_result:
                        print(f"New Session Completed! ID: {latest_id} | Result: {actual_result} ({point})")

                        # Check prediction
                        if current_prediction:
                            predicted_count += 1
                            if current_prediction == actual_result:
                                print("✅ Prediction Correct!")
                            else:
                                print("❌ Prediction Incorrect. Simulating and optimizing...")
                                # Feed the new data and optimize because we failed
                                analyzer.feed_data(latest_session)
                                analyzer.simulate_and_optimize()
                        else:
                            # Just feed data if we didn't have a prediction
                            analyzer.feed_data(latest_session)

                        # Update last session ID
                        last_session_id = latest_id

                        # Generate prediction for the *next* session
                        current_prediction = analyzer.get_prediction()
                        print(f"-> Prediction for next session: {current_prediction} (Logic: {analyzer.best_logic})")

            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
