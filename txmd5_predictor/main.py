import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

from analyzer import Analyzer
from reporter import TelegramReporter

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

async def fetch_data(session):
    try:
        # User requested explicitly disable SSL verification by passing ssl=False
        async with session.get(API_URL, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print(f"API Error: Status {response.status}")
                return None
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

async def main():
    analyzer = Analyzer()
    reporter = TelegramReporter()

    # Start the reporter loop in the background
    asyncio.create_task(reporter.report_loop(analyzer))

    last_session_id = None

    # Disable SSL verification to prevent connection failure
    connector = aiohttp.TCPConnector(ssl=False)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        print("Starting TXMD5 Predictor...")

        is_first_run = True

        while True:
            data = await fetch_data(session)
            if data and 'list' in data and data['list']:

                if is_first_run:
                    # Backtesting requirement: rewind the farthest (old) history to analyze it gradually
                    # Assuming data['list'] is ordered from newest to oldest
                    historical_sessions = data['list'][::-1]
                    print(f"Performing initial backtesting with {len(historical_sessions)} historical sessions...")

                    for sess in historical_sessions:
                        analyzer.process_new_session(sess)
                        last_session_id = sess.get('id') or sess.get('session_id')

                    print(f"Backtesting complete. Current Best Algorithm: {analyzer.current_best_algorithm}")
                    print(f"Initial Stats: {analyzer.correct_predictions}/{analyzer.total_predictions}")
                    is_first_run = False

                else:
                    # After first run, only process the newest session
                    latest_session = data['list'][0]
                    current_id = latest_session.get('id') or latest_session.get('session_id')

                    if current_id and current_id != last_session_id:
                        print(f"\nNew Session Detected: {current_id}")
                        result = analyzer.process_new_session(latest_session)
                        print(f"Prediction for next: {result['prediction']} (Algo: {result['algorithm']})")
                        print(f"Stats: {result['correct_predictions']}/{result['total_predictions']}")

                        last_session_id = current_id

            # Reset page continuously 500 milliseconds/1 reset
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
