import os
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/"

    async def send_message(self, text):
        if not self.token or not self.chat_id:
            logger.warning("Telegram token or chat_id not set, skipping message.")
            return

        url = self.api_url + "sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send Telegram message: {await response.text()}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")

    async def report_loop(self, analyzer, get_stats_callback):
        while True:
            await asyncio.sleep(3600)  # Every 1 hour

            stats = get_stats_callback()
            sessions_predicted = stats.get('sessions_predicted', 0)

            if sessions_predicted == 0:
                continue

            best_algo = analyzer.best_algorithm
            perf = analyzer.algorithm_performance
            total_evals = sum(perf.values()) if perf else 0

            # Simple success percentage calculation (mocked based on optimization score / total evals)
            # In a real scenario, this would track actual prediction success vs real outcome
            success_pct = 0
            if total_evals > 0 and best_algo in perf:
                 # This is an approximation. Optimization score is max (N-10).
                 success_pct = (perf[best_algo] / (len(analyzer.history) - 10)) * 100 if len(analyzer.history) > 10 else 0

            msg = (
                f"📊 <b>HOURLY PREDICTION REPORT</b> 📊\n"
                f"Total Sessions Predicted: {sessions_predicted}\n"
                f"Current Best Algorithm: <b>{best_algo}</b>\n"
                f"Algorithm Performance (Simulation): {success_pct:.2f}%\n\n"
                f"<i>System continues to monitor and optimize.</i>"
            )
            await self.send_message(msg)

    # Simplified polling for slash commands (e.g. /status)
    async def poll_commands(self, get_stats_callback):
        if not self.token: return

        offset = 0
        url = self.api_url + "getUpdates"

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(f"{url}?offset={offset}&timeout=30") as response:
                        if response.status == 200:
                            data = await response.json()
                            for result in data.get('result', []):
                                offset = result['update_id'] + 1
                                message = result.get('message', {})
                                text = message.get('text', '')
                                chat_id = message.get('chat', {}).get('id')

                                if text == '/status':
                                    stats = get_stats_callback()
                                    reply = f"Status: Running\nPredicted: {stats.get('sessions_predicted', 0)}"

                                    send_url = self.api_url + "sendMessage"
                                    await session.post(send_url, json={"chat_id": chat_id, "text": reply})

                except Exception as e:
                    logger.error(f"Error polling Telegram commands: {e}")
                await asyncio.sleep(2)
