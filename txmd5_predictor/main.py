import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

from analyzer import Analyzer
from bot import TelegramBot

async def poll_api(analyzer, bot):
    url = 'https://wtxmd52.tele68.com/v1/txmd5/sessions'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    # We maintain the aiohttp ClientSession outside the loop
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:

        # Initial History Fetch
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'list' in data:
                        # Process in reverse (oldest first)
                        for s in reversed(data['list']):
                            analyzer.add_session(s)
                        print(f"Loaded {len(data['list'])} initial sessions.")
        except Exception as e:
            print(f"Error fetching initial history: {e}")

        await analyzer._simulate_and_optimize()

        print("Starting active polling loop...")
        last_prediction = None
        last_session_id = None

        while True:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'list' in data and len(data['list']) > 1:
                            current_completed_session = data['list'][1]
                            current_id = current_completed_session['id']

                            is_new = analyzer.add_session(current_completed_session)

                            if is_new and last_prediction and last_session_id == current_id:
                                actual_result = current_completed_session.get('resultTruyenThong') or current_completed_session.get('result')
                                if actual_result:
                                    print(f"Session {current_id} finished: Actual={actual_result}, Predicted={last_prediction}")
                                    if last_prediction != actual_result:
                                        print("Prediction incorrect. Triggering optimization...")
                                        await analyzer._simulate_and_optimize()

                            # Make a new prediction for the current active session
                            active_session = data['list'][0]
                            last_session_id = active_session['id']
                            last_prediction = await analyzer.predict()
                            # print(f"Predicting {last_prediction} for session {last_session_id}")
            except Exception as e:
                print(f"Polling error: {e}")

            await asyncio.sleep(0.5)

async def main():
    analyzer = Analyzer()
    bot = TelegramBot()

    # Run polling and reporting loops concurrently
    await asyncio.gather(
        poll_api(analyzer, bot),
        bot.run_hourly_reporting(analyzer)
    )

if __name__ == '__main__':
    asyncio.run(main())
