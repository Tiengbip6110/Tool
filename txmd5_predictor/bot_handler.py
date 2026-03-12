import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Cấu hình logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class TelegramBotHandler:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

        # Biến trạng thái chia sẻ với main loop
        self.is_collecting = False
        self.is_predicting = False

        # Tham chiếu callback để gọi report từ main
        self.get_report_callback = None

        # Khởi tạo Application (Bot)
        self.app = ApplicationBuilder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("stop", self.stop_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("report", self.report_command))
        self.app.add_handler(CommandHandler("startpredicting", self.start_predicting_command))
        self.app.add_handler(CommandHandler("stoppredicting", self.stop_predicting_command))

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.message.chat_id) != self.chat_id: return

        help_text = (
            "🤖 *TXMD5 AI Predictor Bot - Menu Lệnh* 🤖\n\n"
            "🔹 `/help` : Hiện danh sách menu lệnh\n"
            "🔹 `/start` : Bắt đầu thu thập dữ liệu (Start collecting data)\n"
            "🔹 `/stop` : Dừng thu thập dữ liệu (Stop data collection)\n"
            "🔹 `/report` : Báo cáo thống kê, tỷ lệ % và tham số các thuật toán/AI hiện tại\n"
            "🔹 `/startpredicting` : Bật tự động gửi dự đoán khi có phiên mới\n"
            "🔹 `/stoppredicting` : Tắt tính năng tự động gửi dự đoán"
        )
        await context.bot.send_message(chat_id=self.chat_id, text=help_text, parse_mode="Markdown")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.message.chat_id) != self.chat_id: return
        self.is_collecting = True
        await context.bot.send_message(chat_id=self.chat_id, text="✅ Hệ thống *ĐÃ BẮT ĐẦU* thu thập dữ liệu và phân tích AI liên tục.", parse_mode="Markdown")

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.message.chat_id) != self.chat_id: return
        self.is_collecting = False
        await context.bot.send_message(chat_id=self.chat_id, text="⏸ Hệ thống *ĐÃ DỪNG* thu thập dữ liệu.", parse_mode="Markdown")

    async def start_predicting_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.message.chat_id) != self.chat_id: return
        self.is_predicting = True

        if not self.is_collecting:
            self.is_collecting = True
            await context.bot.send_message(chat_id=self.chat_id, text="🔮 Chế độ Auto Predict: *BẬT*. (Hệ thống cũng tự động bật thu thập dữ liệu)", parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=self.chat_id, text="🔮 Chế độ Auto Predict: *BẬT*. Sẽ gửi dự đoán mỗi khi có phiên mới.", parse_mode="Markdown")

    async def stop_predicting_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.message.chat_id) != self.chat_id: return
        self.is_predicting = False
        await context.bot.send_message(chat_id=self.chat_id, text="🔇 Chế độ Auto Predict: *TẮT*. (Thu thập dữ liệu vẫn chạy ngầm nếu chưa tắt)", parse_mode="Markdown")

    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.message.chat_id) != self.chat_id: return

        if self.get_report_callback:
            report_text = self.get_report_callback()
            await context.bot.send_message(chat_id=self.chat_id, text=report_text, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=self.chat_id, text="⏳ Hệ thống chưa sẵn sàng để báo cáo.")

    async def send_message(self, text: str):
        """Hàm sử dụng bởi Main loop để gửi tin nhắn ra bot"""
        try:
             await self.app.bot.send_message(chat_id=self.chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
             logging.error(f"Lỗi gửi tin nhắn Telegram: {e}")

    async def start_bot(self):
        """Khởi chạy Bot Polling trong background"""
        logging.info("Khởi động Telegram Bot Polling...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop_bot(self):
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
