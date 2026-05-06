import os
import json
import logging
from openai import AsyncOpenAI
import google.generativeai as genai
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

class AIClients:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

        self.openai_client = None
        if self.openai_api_key and self.openai_api_key != 'your_openai_api_key':
            try:
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        self.gemini_configured = False
        if self.gemini_api_key and self.gemini_api_key != 'your_gemini_api_key':
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_configured = True
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")

        self.anthropic_client = None
        if self.anthropic_api_key and self.anthropic_api_key != 'your_anthropic_api_key':
            try:
                self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

    async def get_openai_suggestion(self, history: list) -> str:
        if not self.openai_client:
            return ""
        try:
            prompt = self._build_prompt(history)
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return ""

    # Gemini doesn't have a standard official fully async client wrapper yet,
    # but we can try to wrap its sync call if necessary, or just use the sync version in an executor if needed.
    # For now, we will return an empty string to avoid blocking or if not implemented.
    async def get_gemini_suggestion(self, history: list) -> str:
        if not self.gemini_configured:
            return ""
        try:
            # We would use asyncio.to_thread if we want to run synchronous gemini call async
            prompt = self._build_prompt(history)
            import asyncio
            model = genai.GenerativeModel('gemini-pro')
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return ""

    async def get_anthropic_suggestion(self, history: list) -> str:
        if not self.anthropic_client:
            return ""
        try:
            prompt = self._build_prompt(history)
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return ""

    def _build_prompt(self, history: list) -> str:
        return (
            "Analyze the following Sic Bo (Tài Xỉu) game history.\n"
            "Each item contains result sums and dice values.\n"
            "History (oldest to newest): " + json.dumps(history[-20:]) + "\n"
            "What is the most likely next outcome (Tài - over 10, or Xỉu - 10 and under)? "
            "Please briefly explain the algorithm/logic you used."
        )

    async def get_all_suggestions(self, history: list) -> dict:
        import asyncio
        results = await asyncio.gather(
            self.get_openai_suggestion(history),
            self.get_gemini_suggestion(history),
            self.get_anthropic_suggestion(history),
            return_exceptions=True
        )

        # Format results
        suggestions = {}
        names = ['openai', 'gemini', 'anthropic']
        for name, res in zip(names, results):
            if isinstance(res, Exception):
                logger.error(f"Error from {name}: {res}")
                suggestions[name] = ""
            else:
                suggestions[name] = res
        return suggestions
