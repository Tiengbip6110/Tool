import asyncio
import os

class LLMEnsembleAlgorithm:
    def __init__(self):
        # We perform local imports and initialization to prevent missing config errors on startup
        from openai import AsyncOpenAI
        import google.generativeai as genai
        from anthropic import AsyncAnthropic

        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None

        if os.getenv('GEMINI_API_KEY'):
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None

        self.anthropic_client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY')) if os.getenv('ANTHROPIC_API_KEY') else None

    async def predict(self, history):
        # Implement actual logic connecting multiple AIs for ensemble prediction
        # For this prototype we will demonstrate the OpenAI integration
        if not self.openai_client:
            return "TAI" # fallback if missing config

        try:
            # We construct a prompt with recent history asking for logical analysis
            recent_str = ", ".join([f"{s.get('point')} ({s.get('resultTruyenThong')})" for s in history[-10:]])
            prompt = f"Analyze these recent Sic Bo results: {recent_str}. Identify patterns and predict the next result (return ONLY 'TAI' or 'XIU')."

            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.2
            )
            prediction = response.choices[0].message.content.strip().upper()
            if 'TAI' in prediction:
                return 'TAI'
            elif 'XIU' in prediction:
                return 'XIU'
        except Exception as e:
            print(f"LLM Prediction Error: {e}")
        return "TAI"

class Analyzer:
    def __init__(self):
        self.history = []
        self.current_algorithm = 'trend' # Default
        self.llm_ensemble = LLMEnsembleAlgorithm()

    def add_session(self, session):
        """Adds a session to history without duplicates."""
        for i in range(max(0, len(self.history) - 10), len(self.history)):
            if self.history[i]['id'] == session['id']:
                self.history[i] = session
                return False

        self.history.append(session)
        # Keep history bounded if needed, but for backtesting we might keep a lot
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        return True

    def _algo_markov(self):
        if len(self.history) < 2:
            return 'TAI'
        last = self.history[-1].get('resultTruyenThong')
        # simple markov: assume it repeats
        return last

    def _algo_trend(self):
        if len(self.history) < 3:
            return 'TAI'
        recent = [s.get('resultTruyenThong') for s in self.history[-3:]]
        # if 3 same, predict same, else predict opposite of last
        if recent.count(recent[0]) == len(recent):
            return recent[0]
        return 'TAI' if recent[-1] == 'XIU' else 'XIU'

    def _algo_recent_majority(self):
        if len(self.history) < 5:
            return 'TAI'
        recent = [s.get('resultTruyenThong') for s in self.history[-5:]]
        tai_count = recent.count('TAI')
        return 'TAI' if tai_count > 2 else 'XIU'

    def _algo_sum_analysis(self):
        if len(self.history) < 1:
            return 'TAI'
        last_point = self.history[-1].get('point', 11)
        if last_point > 10:
            return 'TAI'
        return 'XIU'

    async def _algo_llm_ensemble(self, skip_llm=False):
        if skip_llm:
            return 'TAI'
        return await self.llm_ensemble.predict(self.history)

    async def predict(self, algorithm=None, skip_llm=False):
        algo = algorithm or self.current_algorithm
        if algo == 'markov':
            return self._algo_markov()
        elif algo == 'trend':
            return self._algo_trend()
        elif algo == 'recent_majority':
            return self._algo_recent_majority()
        elif algo == 'sum_analysis':
            return self._algo_sum_analysis()
        elif algo == 'llm_ensemble':
            return await self._algo_llm_ensemble(skip_llm=skip_llm)
        return 'TAI'

    async def _simulate_and_optimize(self):
        if len(self.history) < 20:
            return

        algorithms = ['markov', 'trend', 'recent_majority', 'sum_analysis', 'llm_ensemble']
        scores = {algo: 0 for algo in algorithms}

        # Test back to max 50 sessions
        test_history = self.history[-50:]

        # We must use new_history[i] as the target outcome for predictions made on new_history[:i]
        for i in range(10, len(test_history)):
            current_state_analyzer = Analyzer()
            current_state_analyzer.history = test_history[:i]

            actual_result = test_history[i].get('resultTruyenThong') or test_history[i].get('result')

            for algo in algorithms:
                pred = await current_state_analyzer.predict(algorithm=algo, skip_llm=True)
                if pred == actual_result:
                    scores[algo] += 1

        best_algo = max(scores, key=scores.get)
        self.current_algorithm = best_algo
        return best_algo, scores
