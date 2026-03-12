import asyncio
import aiohttp
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from algorithms import FrequencyAnalysis, MarkovChain, PatternMatching, InversePattern
from ai_analyzer import GeminiPredictor, ChatGPTPredictor, ClaudePredictor, GrokPredictor, DeepSeekPredictor
from bot_handler import TelegramBotHandler

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
        self.bot_handler = TelegramBotHandler(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.bot_handler.get_report_callback = self.generate_report_text

        self.history = []
        self.last_session_id = None

        # Danh sách thuật toán logic cổ điển
        self.logic_algorithms = [
            FrequencyAnalysis(10),
            FrequencyAnalysis(50),
            MarkovChain(1),
            PatternMatching(3),
            PatternMatching(5),
            InversePattern(15)
        ]

        # Danh sách AI Algorithms
        self.ai_algorithms = []
        if os.getenv("GEMINI_API_KEY"): self.ai_algorithms.append(GeminiPredictor())
        if os.getenv("OPENAI_API_KEY"): self.ai_algorithms.append(ChatGPTPredictor())
        if os.getenv("CLAUDE_API_KEY"): self.ai_algorithms.append(ClaudePredictor())
        if os.getenv("GROK_API_KEY"): self.ai_algorithms.append(GrokPredictor())
        if os.getenv("DEEPSEEK_API_KEY"): self.ai_algorithms.append(DeepSeekPredictor())

        self.algorithms = self.logic_algorithms + self.ai_algorithms

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

    async def async_process_ai_predictions(self):
        """Khởi chạy bất đồng bộ gọi API tới các AI model"""
        tasks = []
        for ai in self.ai_algorithms:
            tasks.append(ai.async_predict(self.history))
        if tasks:
             await asyncio.gather(*tasks, return_exceptions=True)

    def process_new_session(self, session_data: dict) -> dict:
        """Xử lý khi phát hiện phiên mới từ API."""
        new_result = self.get_result_from_dices(session_data)

        # Thêm kết quả chuẩn hóa vào data để các thuật toán dùng thống nhất
        session_data['calculated_result'] = new_result

        logging.info(f"Phát hiện kết quả mới: Phiên {session_data.get('id', 'Unknown')} - {new_result} - Xúc xắc: {session_data.get('dices', [])} Điểm: {session_data.get('point', 'N/A')}")

        if new_result == "UNKNOWN":
            logging.warning("Không thể xác định kết quả (Tài/Xỉu) từ dữ liệu API.")
            return {}

        # Lấy thuật toán tốt nhất ở ván HIỆN TẠI (trước khi đánh giá) để gửi báo cáo nếu cần
        best_algo_before_eval = self.get_best_algorithm()
        prediction_result = best_algo_before_eval.current_prediction if best_algo_before_eval else "TAI"
        prediction_accuracy = best_algo_before_eval.get_accuracy() if best_algo_before_eval else 0

        # Đánh giá dự đoán của ván trước đối với mọi thuật toán
        for algo in self.algorithms:
            if algo.current_prediction:
                correct = (algo.current_prediction == new_result)
                algo.total_predictions += 1
                if correct:
                    algo.correct_predictions += 1
                logging.info(f" - {algo.name}: Dự đoán {algo.current_prediction} -> {'ĐÚNG' if correct else 'SAI'} ({algo.get_accuracy():.2f}%)")
            algo.current_prediction = None # Reset

        # Cập nhật lịch sử (thêm vào đầu mảng)
        self.history.insert(0, session_data)

        # Giữ mảng lịch sử ở mức độ tối đa khoảng 5000 ván
        if len(self.history) > 5000:
            self.history = self.history[:5000]

        # Trả về thông tin đánh giá phiên VỪA RA để tạo mẫu gửi message
        return {
            "session_data": session_data,
            "prediction_made": prediction_result,
            "accuracy": prediction_accuracy,
            "best_algo": best_algo_before_eval
        }

    def trigger_next_predictions(self):
        """Yêu cầu các thuật toán logic thông thường (sync) dự đoán ván kế"""
        for algo in self.logic_algorithms:
            prediction = algo.predict(self.history)
            algo.current_prediction = prediction

    def get_best_algorithm(self):
        """Trả về thuật toán đang có tỷ lệ chính xác cao nhất (đã đoán >= 5 lần)"""
        valid_algos = [algo for algo in self.algorithms if algo.total_predictions >= 5]
        if not valid_algos:
             if not self.algorithms: return None
             return max(self.algorithms, key=lambda a: a.get_accuracy())

        return max(valid_algos, key=lambda a: a.get_accuracy())

    def format_predict_message(self, eval_data: dict, current_session_id: int) -> str:
         # Xử lý thông tin ván cũ (ván vừa ra)
         old_session = eval_data['session_data']
         old_id = old_session.get('id', 'N/A')
         dices = old_session.get('dices', [])
         dice_str = "-".join(map(str, dices)) if dices else "?-?-?"
         point = old_session.get('point', '?')
         actual_res = old_session.get('calculated_result', 'N/A')

         # Kết quả dự đoán ở phiên cũ của thuật toán xịn nhất
         pred = eval_data['prediction_made']
         algo = eval_data['best_algo']

         is_correct = "True ✅" if pred == actual_res else "False ❌"

         # Xử lý thông tin ván hiện tại (ván đang dự đoán)
         # Lấy the best algorithm AFTER updates and predictions for the new session
         best_algo_now = self.get_best_algorithm()
         next_pred = best_algo_now.current_prediction if best_algo_now and best_algo_now.current_prediction else "Đang phân tích..."
         acc_ratio = f"{best_algo_now.get_accuracy():.0f}%" if best_algo_now else "0%"
         algo_name = best_algo_now.name if best_algo_now else "N/A"

         total_acc = best_algo_now.correct_predictions if best_algo_now else 0
         total_sess = best_algo_now.total_predictions if best_algo_now else 0

         msg = (
             "🔮 *ADVANCED SIC BO MODEL* 🔮\n"
             f"SESSION OLD 🧩: #{old_id}\n"
             f"Dice 🎲: {dice_str} = {point} | {actual_res}🎯\n"
             f"Result: {is_correct} (Bởi: {algo.name if algo else 'Default'})\n\n"
             "————————————————————————\n\n"
             f"CURRENT SESSION 🧩: #{current_session_id}\n"
             f"Verdict 🎯: {next_pred} | Accuracy Ratio: {acc_ratio} 🔥 (Bởi: {algo_name})\n\n"
             f"Total Sessions: {total_sess} sessions | Sum Accuracy 📃: {total_acc}/{total_sess} | Accuracy Rate: {acc_ratio} 💎"
         )
         return msg

    def generate_report_text(self) -> str:
        """Tạo báo cáo chi tiết cho lệnh /report"""
        best_algo = self.get_best_algorithm()
        total_tracked = len(self.history)

        report = f"📊 *BÁO CÁO HỆ THỐNG AI & LOGIC* 📊\n"
        report += f"🎲 Tổng số phiên đã lưu: `{total_tracked}`\n\n"

        if best_algo:
             report += f"🏆 *Mô hình tốt nhất:*\n"
             report += f"   Tên: `{best_algo.name}`\n"
             report += f"   Chính xác: `{best_algo.get_accuracy():.2f}%` ({best_algo.correct_predictions}/{best_algo.total_predictions})\n"
             report += f"   Dự đoán ván kế ({self.last_session_id + 1 if self.last_session_id else 'N/A'}): `{best_algo.current_prediction}`\n\n"

        report += f"📉 *Chi tiết các mô hình khác:*\n"
        for algo in sorted(self.algorithms, key=lambda a: a.get_accuracy(), reverse=True):
             report += f" - {algo.name}: {algo.get_accuracy():.2f}% ({algo.correct_predictions}/{algo.total_predictions})\n"

        report += f"\n⚙️ Trạng thái Thu thập: {'🟢 Chạy' if self.bot_handler.is_collecting else '🔴 Dừng'}\n"
        report += f"⚙️ Trạng thái Tự Động Gửi Dự đoán: {'🟢 Bật' if self.bot_handler.is_predicting else '🔴 Tắt'}"
        return report

    async def fetch_data_loop(self):
         """Vòng lặp lấy dữ liệu không giới hạn, xử lý exception để luôn retry"""
         async with aiohttp.ClientSession() as session:
             # Khởi tạo dữ liệu
             initial_data = await self.fetch_data(session)
             if initial_data and 'data' in initial_data:
                  self.history = initial_data['data']
                  if self.history:
                      self.last_session_id = self.history[0]['id']
                      logging.info(f"Đã tải {len(self.history)} phiên. Mới nhất: {self.last_session_id}")
                      self.trigger_next_predictions()
                      asyncio.create_task(self.async_process_ai_predictions())

             while True:
                 try:
                     # Chỉ gọi API và phân tích nếu cờ is_collecting bật
                     if self.bot_handler.is_collecting:
                         data = await self.fetch_data(session)
                         if data and 'data' in data and data['data']:
                             latest_session = data['data'][0]
                             current_id = latest_session['id']

                             if self.last_session_id is None:
                                 self.last_session_id = current_id

                             elif current_id > self.last_session_id:
                                 # 1. Đánh giá và cập nhật phiên MỚI RA (Vừa kết thúc)
                                 eval_data = self.process_new_session(latest_session)

                                 # 2. Tạo dự đoán cho ván KẾ TIẾP (Session hiện tại)
                                 self.last_session_id = current_id
                                 next_session_id = current_id + 1

                                 # Logic cổ điển (chạy ngay)
                                 self.trigger_next_predictions()

                                 # AI gọi API (chạy background không block loop chính)
                                 asyncio.create_task(self.async_process_ai_predictions())

                                 # 3. Gửi dự đoán lên Telegram nếu cờ is_predicting bật
                                 if self.bot_handler.is_predicting and eval_data:
                                      msg = self.format_predict_message(eval_data, next_session_id)
                                      await self.bot_handler.send_message(msg)

                         # Gửi report định kỳ hàng giờ (Chỉ khi đang thu thập)
                         now = datetime.now()
                         if (now - self.last_report_time).total_seconds() >= self.report_interval_hours * 3600:
                              report_text = self.generate_report_text()
                              await self.bot_handler.send_message(report_text)
                              self.last_report_time = now

                 except Exception as e:
                     logging.error(f"Lỗi trong vòng lặp API (Sẽ tiếp tục thử lại): {e}")

                 await asyncio.sleep(0.5)

    async def run(self):
        logging.info("Bắt đầu khởi chạy hệ thống...")

        # Vòng lặp tái khởi động Bot + Loop chính nếu có lỗi nghiêm trọng crash luồng
        while True:
            try:
                # Khởi động Telegram Bot (chạy nền)
                await self.bot_handler.start_bot()

                # Gửi tin nhắn khởi động
                await self.bot_handler.send_message("🚀 *Khởi động Server thành công!* Gõ `/help` để xem menu điều khiển.")

                # Chạy loop API (Loop này có tự xử lý error nhưng nếu lọt exception thì sẽ restart toàn bộ)
                await self.fetch_data_loop()

            except Exception as e:
                 logging.critical(f"Lỗi NGHIÊM TRỌNG làm văng hệ thống: {e}. Đang KHỞI ĐỘNG LẠI sau 5s...")
                 try:
                     await self.bot_handler.stop_bot()
                 except: pass
                 await asyncio.sleep(5)


if __name__ == "__main__":
    app = MainApp()
    try:
        # Cần một event loop dài hạn, asyncio.run sẽ quản lý app.run()
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logging.info("Hệ thống đã dừng thủ công.")
        # Dừng bot gọn gàng
        try: asyncio.run(app.bot_handler.stop_bot())
        except: pass
