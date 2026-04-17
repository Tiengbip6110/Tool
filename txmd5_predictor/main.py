import asyncio
import aiohttp
import time
from analyzer import Analyzer
from bot import send_hourly_report

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

async def fetch_data(session):
    try:
        async with session.get(API_URL, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                # Based on investigation, the API returns a 'list' key
                if "list" in data and len(data["list"]) > 0:
                     return data["list"]
            else:
                print(f"API returned status {response.status}")
    except Exception as e:
        print(f"Error fetching API: {e}")
    return None

async def send_periodic_reports(analyzer: Analyzer):
    while True:
        # Sleep for 1 hour (3600 seconds)
        await asyncio.sleep(3600)
        print("Sending hourly report...")
        accuracy = analyzer.get_current_logic_accuracy()
        await send_hourly_report(
            logic_name=analyzer.current_best_algorithm,
            logic_percentage=accuracy,
            sessions_predicted=analyzer.sessions_predicted,
            correct_predictions=analyzer.correct_predictions
        )

async def poll_api(analyzer: Analyzer):
    # Setup connector to explicitly disable SSL verification to prevent connection failures
    connector = aiohttp.TCPConnector(ssl=False)
    last_processed_id = None
    predicted_next = None

    async with aiohttp.ClientSession(connector=connector) as session:
        # Initially, let's load some history
        data = await fetch_data(session)
        if data:
            # Data is returned from newest to oldest. We want to feed oldest to newest for history
            history_data = reversed(data)
            for item in history_data:
                analyzer.add_record(item["resultTruyenThong"], item["dices"], item["point"])
            if len(data) > 0:
                last_processed_id = data[0]["id"]
                predicted_next = analyzer.predict()
                print(f"Loaded {len(data)} historical records. Predicted next: {predicted_next}")

        while True:
            data = await fetch_data(session)
            if data and len(data) > 0:
                latest_item = data[0]
                if latest_item["id"] != last_processed_id:
                    # We have a new session result!
                    actual_result = latest_item["resultTruyenThong"]
                    print(f"New session {latest_item['id']} finished! Result: {actual_result}")

                    if predicted_next:
                        analyzer.evaluate_prediction(actual_result, predicted_next)

                    analyzer.add_record(actual_result, latest_item["dices"], latest_item["point"])

                    last_processed_id = latest_item["id"]
                    predicted_next = analyzer.predict()

                    print(f"Current Best Algorithm: {analyzer.current_best_algorithm} (Accuracy: {analyzer.get_current_logic_accuracy():.2f}%)")
                    print(f"Predicted next session: {predicted_next}")

            await asyncio.sleep(0.5)

async def main_loop():
    analyzer = Analyzer()

    # Run API poller and Reporter concurrently
    await asyncio.gather(
        poll_api(analyzer),
        send_periodic_reports(analyzer)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
