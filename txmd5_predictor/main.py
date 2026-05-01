import asyncio
import logging
import os
from api_client import Txmd5ApiClient
from analyzer import Analyzer
from telegram_reporter import TelegramReporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    api_client = Txmd5ApiClient()
    await api_client.init_session()
    analyzer = Analyzer()

    # Optional token from env var to actually send messages
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "DUMMY_TOKEN")
    reporter = TelegramReporter(token=bot_token)

    # Initial Backtesting
    logging.info("Starting initial backtesting...")
    initial_sessions = await api_client.fetch_sessions()
    if initial_sessions:
        # Reverse to process oldest to newest
        initial_sessions.reverse()
        for session in initial_sessions:
            analyzer.add_history(session)

        # Initial optimization run
        analyzer._simulate_and_optimize()
        logging.info("Initial backtesting complete.")

    # Start Reporter Task
    asyncio.create_task(reporter.report_loop(analyzer))

    last_session_id = None

    logging.info("Entering active polling loop...")
    while True:
        try:
            sessions = await api_client.fetch_sessions()
            if sessions:
                latest_session = sessions[0] # assuming index 0 is newest
                current_id = latest_session.get('id')

                if current_id != last_session_id:
                    if last_session_id is not None:
                        # New session resulted, verify previous prediction and update history
                        analyzer.add_history(latest_session)

                        # Just optimize on new session for continuous learning
                        analyzer._simulate_and_optimize()

                    last_session_id = current_id

                    prediction = analyzer.predict()
                    logging.info(f"New session {current_id}. Predicted next: {prediction}. Best Alg: {analyzer.best_algorithm}")

        except Exception as e:
            logging.error(f"Error in polling loop: {e}")

        await asyncio.sleep(0.5)  # 500ms polling

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
