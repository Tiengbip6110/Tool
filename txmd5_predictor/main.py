import asyncio
import aiohttp
import logging
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from algorithms import Predictor, FrequencyAnalysis, MarkovChain, PatternMatching, InversePattern
from telegram_reporter import TelegramReporter

# Load biến môi trường
load_dotenv()

# Cấu hình logging chi tiết
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logging.warning("TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID chưa được cấu hình trong .env!")
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"

class MainApp:
    def __init__(self):
        self.reporter = TelegramReporter(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.history = []
        self.last_session_id = None
        self.algorithms = [
            FrequencyAnalysis(10),
            FrequencyAnalysis(50),
            MarkovChain(1),
            PatternMatching(3),
            PatternMatching(5),
            InversePattern(15)
        ]
        self.report_interval_hours = 1
        self.last_report_time = datetime.now()

    async def fetch_data(self, session: aiohttp.ClientSession) -> dict:
        try:
            async with session.get(API_URL, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
        except Exception as e:
            logging.error(f"Lỗi khi gọi API: {e}")
        return None

    def get_result_from_dices(self, session_data: dict) -> str:
        """Lấy kết quả từ tổng 3 xúc xắc nếu không có sẵn resultTruyenThong"""
        if 'resultTruyenThong' in session_data:
            return session_data['resultTruyenThong']

        if 'dices' in session_data and isinstance(session_data['dices'], list) and len(session_data['dices']) == 3:
             point = sum(session_data['dices'])
             return "TAI" if point >= 11 else "XIU"

        # Fallback to point field if it exists
        if 'point' in session_data:
            return "TAI" if session_data['point'] >= 11 else "XIU"

        return "UNKNOWN"

    def process_new_session(self, session_data: dict):
        """Xử lý khi phát hiện phiên mới từ API."""
        new_result = self.get_result_from_dices(session_data)

        # Thêm kết quả chuẩn hóa vào data để các thuật toán dùng thống nhất
        session_data['calculated_result'] = new_result

        logging.info(f"Phát hiện kết quả mới: Phiên {session_data.get('id', 'Unknown')} - {new_result} - Xúc xắc: {session_data.get('dices', [])} Điểm: {session_data.get('point', 'N/A')}")

        if new_result == "UNKNOWN":
            logging.warning("Không thể xác định kết quả (Tài/Xỉu) từ dữ liệu API.")
            return

        # 1. Đánh giá dự đoán của ván trước đối với mọi thuật toán
        for algo in self.algorithms:
            if algo.current_prediction:
                correct = (algo.current_prediction == new_result)
                algo.total_predictions += 1
                if correct:
                    algo.correct_predictions += 1
                logging.info(f" - {algo.name}: Dự đoán {algo.current_prediction} -> {'ĐÚNG' if correct else 'SAI'} ({algo.get_accuracy():.2f}%)")
            algo.current_prediction = None # Reset

        # 2. Cập nhật lịch sử (thêm vào đầu mảng)
        self.history.insert(0, session_data)

        # Giữ mảng lịch sử ở mức độ tối đa khoảng 5000 ván để tránh tràn RAM theo thời gian
        if len(self.history) > 5000:
            self.history = self.history[:5000]

        # 3. Yêu cầu các thuật toán dự đoán cho ván tiếp theo
        for algo in self.algorithms:
            prediction = algo.predict(self.history)
            algo.current_prediction = prediction

    def get_best_algorithm(self):
        """Trả về thuật toán đang có tỷ lệ chính xác cao nhất và đã dự đoán ít nhất 5 ván."""
        valid_algos = [algo for algo in self.algorithms if algo.total_predictions >= 5]
        if not valid_algos:
            return max(self.algorithms, key=lambda a: a.get_accuracy())

        return max(valid_algos, key=lambda a: a.get_accuracy())

    async def send_hourly_report(self):
        """Gửi báo cáo tổng hợp qua Telegram."""
        best_algo = self.get_best_algorithm()

        report = f"📊 *BÁO CÁO DỰ ĐOÁN TXMD5 MỖI GIỜ* 📊\n\n"
        report += f"⏱ Thời gian: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        report += f"🎲 Tổng số phiên đã theo dõi: `{len(self.history)}`\n\n"

        report += f"🏆 *Thuật toán tốt nhất hiện tại:*\n"
        report += f"   Tên: `{best_algo.name}`\n"
        report += f"   Độ chính xác: `{best_algo.get_accuracy():.2f}%` ({best_algo.correct_predictions}/{best_algo.total_predictions})\n"
        report += f"   Dự đoán ván tiếp theo ({self.last_session_id + 1 if self.last_session_id else 'N/A'}): `{best_algo.current_prediction}`\n\n"

        report += f"📉 *Hiệu suất các thuật toán khác:*\n"
        for algo in sorted(self.algorithms, key=lambda a: a.get_accuracy(), reverse=True):
            if algo.name != best_algo.name:
                report += f" - {algo.name}: {algo.get_accuracy():.2f}% ({algo.correct_predictions}/{algo.total_predictions})\n"

        await self.reporter.send_message(report)

    async def run(self):
        logging.info("Bắt đầu khởi chạy hệ thống theo dõi TXMD5...")

        # Khởi tạo phiên lấy dữ liệu 1 lần đầu để lấy lịch sử
        async with aiohttp.ClientSession() as session:
            initial_data = await self.fetch_data(session)
            if initial_data and 'data' in initial_data:
                 # API trả về mảng 'data' với [0] là mới nhất
                 self.history = initial_data['data']
                 if self.history:
                     self.last_session_id = self.history[0]['id']
                     logging.info(f"Đã tải {len(self.history)} phiên lịch sử. Phiên mới nhất: {self.last_session_id}")

                     # Khởi tạo dự đoán ban đầu
                     for algo in self.algorithms:
                          algo.predict(self.history)

            # Gửi tin nhắn bắt đầu
            await self.reporter.send_message("🚀 *Hệ thống AI theo dõi TXMD5 đã khởi động!* 🚀\nĐang thu thập dữ liệu và chạy mô phỏng thuật toán...")

            # Vòng lặp chính mỗi 500ms
            while True:
                try:
                    data = await self.fetch_data(session)
                    if data and 'data' in data and data['data']:
                        latest_session = data['data'][0]
                        current_id = latest_session['id']

                        if self.last_session_id is None:
                            self.last_session_id = current_id
                        elif current_id > self.last_session_id:
                            # Có phiên mới
                            self.process_new_session(latest_session)
                            self.last_session_id = current_id

                    # Kiểm tra gửi báo cáo hàng giờ
                    now = datetime.now()
                    if (now - self.last_report_time).total_seconds() >= self.report_interval_hours * 3600:
                         await self.send_hourly_report()
                         self.last_report_time = now

                except Exception as e:
                    logging.error(f"Lỗi trong vòng lặp chính: {e}")

                await asyncio.sleep(0.5)

if __name__ == "__main__":
    app = MainApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logging.info("Hệ thống đã bị dừng bởi người dùng.")