import asyncio
import aiohttp
from dotenv import load_dotenv
import time

# Load env vars before importing our modules
load_dotenv()

from analyzer import Analyzer
from bot import TelegramBot

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
POLL_INTERVAL = 0.5  # 500ms

async def fetch_sessions(session):
    """Fetches the latest session data from the API."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        async with session.get(API_URL, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('list', [])
            else:
                print(f"[API] Error {response.status}: {await response.text()}")
    except Exception as e:
        print(f"[API] Exception during fetch: {e}")
    return []

async def hourly_reporter(bot, analyzer):
    """Background task to report every hour."""
    while True:
        await asyncio.sleep(3600)  # 1 hour
        total_sessions = len(analyzer.history)
        await bot.report_hourly(analyzer, total_sessions)
        print(f"[Reporter] Sent hourly report. Total tracked sessions: {total_sessions}")

async def main():
    print("[Main] Starting TXMD5 Predictor...")
    analyzer = Analyzer()
    bot = TelegramBot()

    # Disable SSL verification for this specific API as required
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as http_session:
        # 1. Initial Fetch to train the analyzer
        print("[Main] Fetching initial history to train analyzer...")
        initial_data = await fetch_sessions(http_session)

        if not initial_data:
            print("[Main] Failed to fetch initial data. Retrying in 5 seconds...")
            await asyncio.sleep(5)
            return await main() # Restart

        # The API returns list descending (newest first).
        # We need to process from oldest to newest for backtesting.
        history_asc = list(reversed(initial_data))

        # Ensure we map the results correctly based on what API gives ('resultTruyenThong')
        for item in history_asc:
             item['result'] = item.get('resultTruyenThong')

        analyzer._simulate_and_optimize(history_asc)
        print(f"[Main] Initial training complete. Best algo: {analyzer.best_algo_name} ({analyzer.win_rate:.2f}%)")

        # Start the background reporter
        asyncio.create_task(hourly_reporter(bot, analyzer))

        # 2. Continuous Polling Loop
        last_processed_id = None
        current_prediction = None

        # Determine the last finished session ID from the initial fetch
        if len(initial_data) > 1:
             last_processed_id = initial_data[1]['id'] # initial_data[0] is usually ongoing

        print("[Main] Entering active polling loop...")

        while True:
            start_time = time.time()
            sessions = await fetch_sessions(http_session)

            if sessions and len(sessions) > 1:
                # The most recently finished session is at index 1
                latest_finished_session = sessions[1]
                latest_finished_session['result'] = latest_finished_session.get('resultTruyenThong')

                if last_processed_id != latest_finished_session['id']:
                    # New session finished!
                    print(f"\n[Session {latest_finished_session['id']}] Finished. Result: {latest_finished_session['result']}, Dice: {latest_finished_session.get('dices')}, Point: {latest_finished_session.get('point')}")

                    # Update our history
                    analyzer.update_history(latest_finished_session)

                    # Evaluate our previous prediction
                    if current_prediction:
                        if current_prediction == latest_finished_session['result']:
                            print("✅ Prediction CORRECT!")
                        else:
                            print("❌ Prediction INCORRECT! Triggering re-optimization...")
                            # Re-optimize since prediction was wrong
                            analyzer._simulate_and_optimize(analyzer.history)
                            print(f"[Optimizer] New best algo: {analyzer.best_algo_name} ({analyzer.win_rate:.2f}%)")

                    # Make a new prediction for the next session
                    current_prediction = analyzer.predict_next()
                    ongoing_session_id = sessions[0]['id']
                    print(f"[Prediction] Next session {ongoing_session_id}: Predicted {current_prediction} (using {analyzer.best_algo_name})")

                    last_processed_id = latest_finished_session['id']

            # Calculate sleep time to maintain exactly 500ms intervals
            elapsed = time.time() - start_time
            sleep_time = max(0, POLL_INTERVAL - elapsed)
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Main] Stopping...")
