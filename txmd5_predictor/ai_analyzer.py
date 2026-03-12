import os
import logging
from algorithms import Predictor
from dotenv import load_dotenv

from google import genai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

load_dotenv()

# Khởi tạo các clients bất đồng bộ với error handling cơ bản
class AIBasePredictor(Predictor):
    def __init__(self, name: str):
        super().__init__(name)
        # Các AI có thể trả về dự đoán chậm, vì vậy ta tách logic fetch dự đoán ra
        # self.current_prediction là kết quả được lưu tạm từ lần fetch trước

    def predict(self, history: list[dict]) -> str:
        """
        Ghi đè predict để AI không trả về ngay lập tức (tránh block loop)
        mà sử dụng kết quả dự đoán đã được cập nhật từ hàm async_predict
        """
        return self.current_prediction if self.current_prediction else "TAI"

    def format_prompt(self, history: list[dict], limit: int = 15) -> str:
        """Định dạng dữ liệu lịch sử thành chuỗi Prompt cho AI"""
        recent = history[:limit]

        prompt = "Bạn là một AI phân tích Logic của trò chơi Sic Bo (Tài Xỉu 3 viên xúc xắc). Mục tiêu của bạn là dự đoán kết quả của ván tiếp theo (chỉ trả về một chữ: 'TAI' hoặc 'XIU', không giải thích).\n"
        prompt += f"Dưới đây là lịch sử {len(recent)} ván gần nhất (từ mới nhất về cũ hơn):\n"

        for i, s in enumerate(recent):
            dices = s.get('dices', [])
            point = s.get('point', '?')
            res = s.get('calculated_result', s.get('resultTruyenThong', '?'))
            prompt += f"- Ván {len(recent)-i}: Xúc xắc {dices} = {point} ({res})\n"

        prompt += "\nDựa vào thuật toán nhận dạng mẫu, chuỗi Markov và xác suất thống kê, dự đoán ván tiếp theo là TAI (tổng 11-17) hay XIU (tổng 4-10)?"
        return prompt

class GeminiPredictor(AIBasePredictor):
    def __init__(self):
        super().__init__("AI - Google Gemini")
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    async def async_predict(self, history: list[dict]):
        if not self.client or len(history) < 5:
            return

        prompt = self.format_prompt(history)
        try:
            import asyncio
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model='gemini-2.5-flash',
                contents=prompt,
            )
            text = response.text.strip().upper()
            if "TAI" in text:
                self.current_prediction = "TAI"
            elif "XIU" in text:
                self.current_prediction = "XIU"
        except Exception as e:
            logging.error(f"Gemini API Error: {e}")

class ChatGPTPredictor(AIBasePredictor):
    def __init__(self):
        super().__init__("AI - ChatGPT (OpenAI)")
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None

    async def async_predict(self, history: list[dict]):
        if not self.client or len(history) < 5:
            return

        prompt = self.format_prompt(history)
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.3
            )
            text = response.choices[0].message.content.strip().upper()
            if "TAI" in text:
                self.current_prediction = "TAI"
            elif "XIU" in text:
                self.current_prediction = "XIU"
        except Exception as e:
            logging.error(f"ChatGPT API Error: {e}")

class ClaudePredictor(AIBasePredictor):
    def __init__(self):
        super().__init__("AI - Claude (Anthropic)")
        api_key = os.getenv("CLAUDE_API_KEY")
        if api_key:
            self.client = AsyncAnthropic(api_key=api_key)
        else:
            self.client = None

    async def async_predict(self, history: list[dict]):
        if not self.client or len(history) < 5:
            return

        prompt = self.format_prompt(history)
        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip().upper()
            if "TAI" in text:
                self.current_prediction = "TAI"
            elif "XIU" in text:
                self.current_prediction = "XIU"
        except Exception as e:
            logging.error(f"Claude API Error: {e}")

class GrokPredictor(AIBasePredictor):
    def __init__(self):
        super().__init__("AI - Grok (xAI)")
        api_key = os.getenv("GROK_API_KEY")
        # Grok sử dụng format tương thích OpenAI
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        else:
            self.client = None

    async def async_predict(self, history: list[dict]):
        if not self.client or len(history) < 5:
            return

        prompt = self.format_prompt(history)
        try:
            response = await self.client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.3
            )
            text = response.choices[0].message.content.strip().upper()
            if "TAI" in text:
                self.current_prediction = "TAI"
            elif "XIU" in text:
                self.current_prediction = "XIU"
        except Exception as e:
            logging.error(f"Grok API Error: {e}")

class DeepSeekPredictor(AIBasePredictor):
    def __init__(self):
        super().__init__("AI - DeepSeek")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        else:
            self.client = None

    async def async_predict(self, history: list[dict]):
        if not self.client or len(history) < 5:
            return

        prompt = self.format_prompt(history)
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.3
            )
            text = response.choices[0].message.content.strip().upper()
            if "TAI" in text:
                self.current_prediction = "TAI"
            elif "XIU" in text:
                self.current_prediction = "XIU"
        except Exception as e:
            logging.error(f"DeepSeek API Error: {e}")
