import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.target_chat_id = "8308036418" # User requested chat ID
        self.application = None
        self.is_running = False

    async def start_bot(self):
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot will not run.")
            return

        try:
            self.application = ApplicationBuilder().token(self.token).build()

            # Add basic command handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("status", self.cmd_status))

            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            self.is_running = True
            logger.info("Telegram Bot started.")

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")

    async def stop_bot(self):
        if self.application and self.is_running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.is_running = False
            logger.info("Telegram Bot stopped.")

    async def send_message(self, message: str, chat_id: str = None):
        if not self.application or not self.is_running:
            return

        target_id = chat_id or self.target_chat_id
        try:
            await self.application.bot.send_message(chat_id=target_id, text=message, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    # Command Handlers
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Super Project Bot is running. I will report hourly statistics here.")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Bot status: Active. Predicting and monitoring.")

    async def report_loop(self, get_stats_callback, optimize_callback):
        """Background loop to send hourly reports and trigger hourly optimizations."""
        while True:
            # Wait 1 hour (3600 seconds)
            await asyncio.sleep(3600)

            try:
                if self.is_running:
                    if optimize_callback:
                        logger.info("🕒 Triggering scheduled hourly optimization...")
                        await optimize_callback()

                    if get_stats_callback:
                        stats = get_stats_callback()
                        report_msg = self._format_report(stats)
                        await self.send_message(report_msg)
            except Exception as e:
                logger.error(f"Error in report loop: {e}")

    def _format_report(self, stats: dict) -> str:
        """Format the hourly statistics into a readable message."""
        msg = "<b>🔥 HOURLY ALGORITHM REPORT 🔥</b>\n\n"
        msg += f"<b>Total Sessions Monitored:</b> {stats.get('total_sessions', 0)}\n"
        msg += f"<b>Predicted Sessions:</b> {stats.get('predicted_sessions', 0)}\n"
        msg += f"<b>Current Logic/Algorithm:</b> {stats.get('current_algorithm', 'N/A')}\n"
        msg += f"<b>Overall Win Rate:</b> {stats.get('win_rate', 0.0):.2f}%\n"
        msg += "\n<i>Optimization completed. Monitoring continues.</i>"
        return msg
