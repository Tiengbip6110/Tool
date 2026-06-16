import asyncio
import aiohttp
import os
import time
from dotenv import load_dotenv

# Ensure dotenv is loaded before local imports
load_dotenv()

from analyzer import Analyzer
from bot import TelegramBot

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

async def fetch_initial_history(session: aiohttp.ClientSession) -> list:
    """Fetches the initial batch of historical sessions."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        # ssl=False is required for this specific API as per memory
        async with session.get(API_URL, headers=headers, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('list', [])
            else:
                print(f"Failed to fetch initial history: {response.status}")
                return []
    except Exception as e:
        print(f"Error fetching initial history: {e}")
        return []

async def train_initial_analyzer(analyzer: Analyzer, history_list: list):
    """Parses historical sessions in reverse order to train the analyzer."""
    if not history_list:
        return

    print(f"Training analyzer on {len(history_list)} historical sessions...")
    # The API returns list in descending order. We need to process oldest to newest.
    for session_data in reversed(history_list):
        analyzer.update_history(session_data)

    print("Initial history loaded. Running initial backtesting optimization...")
    best_algo = await analyzer._simulate_and_optimize()
    print(f"Initial optimization complete. Best algorithm: {best_algo}")

async def poll_api():
    """Main polling loop running every 500ms."""
    analyzer = Analyzer()
    bot = TelegramBot()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Track stats for hourly report
    prediction_stats = {
        'best_algorithm': 'N/A',
        'total': 0,
        'correct': 0
    }

    last_report_time = time.time()
    last_session_id = None
    current_prediction = None

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as http_session:
        # Initial training
        initial_history = await fetch_initial_history(http_session)
        await train_initial_analyzer(analyzer, initial_history)
        prediction_stats['best_algorithm'] = analyzer.best_algorithm

        while True:
            try:
                async with http_session.get(API_URL, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        sessions = data.get('list', [])

                        if len(sessions) >= 2:
                            # The most recently finished session is at index 1
                            finished_session = sessions[1]
                            current_session = sessions[0]

                            # Check if a new session has finished
                            if finished_session['id'] != last_session_id:
                                last_session_id = finished_session['id']
                                analyzer.update_history(finished_session)

                                actual_result = finished_session.get('result') or finished_session.get('resultTruyenThong')

                                # Evaluate previous prediction
                                if current_prediction:
                                    prediction_stats['total'] += 1
                                    if current_prediction == actual_result:
                                        prediction_stats['correct'] += 1
                                    else:
                                        # Prediction failed, re-optimize
                                        print("Prediction failed. Re-optimizing algorithms...")
                                        prediction_stats['best_algorithm'] = await analyzer._simulate_and_optimize()

                                # Generate new prediction for the current session
                                if analyzer.best_algorithm == 'markov':
                                    current_prediction = analyzer.calculate_markov_chain()
                                elif analyzer.best_algorithm == 'trend':
                                    current_prediction = analyzer.calculate_trend_analysis()
                                elif analyzer.best_algorithm == 'recent':
                                    current_prediction = analyzer.calculate_recent_majority()
                                elif analyzer.best_algorithm == 'sum':
                                    current_prediction = analyzer.calculate_sum_analysis()
                                elif analyzer.best_algorithm == 'llm_ensemble':
                                    current_prediction = await analyzer._algo_llm_ensemble(skip_llm=False)
                                else:
                                    current_prediction = analyzer.calculate_recent_majority() # Default fallback

                                print(f"New Session: {current_session['id']} | Best Algo: {analyzer.best_algorithm} | Prediction: {current_prediction}")

                    else:
                        print(f"API Error: {response.status}")
            except Exception as e:
                print(f"Polling loop error: {e}")

            # Hourly report check
            current_time = time.time()
            if current_time - last_report_time >= 3600:
                print("Sending hourly report...")
                await bot.format_and_send_hourly_report(prediction_stats)
                last_report_time = current_time
                # Reset stats for next hour
                prediction_stats['total'] = 0
                prediction_stats['correct'] = 0

            await asyncio.sleep(0.5)

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    try:
        asyncio.run(poll_api())
    except KeyboardInterrupt:
        print("Stopping predictor.")
