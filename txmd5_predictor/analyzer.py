from typing import List, Dict, Any, Optional
import os
import asyncio

class LLMEnsembleAlgorithm:
    def __init__(self):
        # Local imports of config API keys and LLM clients to prevent circular/early import errors
        try:
            from openai import AsyncOpenAI
            api_key = os.environ.get('OPENAI_API_KEY')
            self.openai_client = AsyncOpenAI(api_key=api_key) if api_key else None
        except ImportError:
            self.openai_client = None

        try:
            from google.generativeai import configure
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                configure(api_key=api_key)
                import google.generativeai as genai
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            else:
                self.gemini_model = None
        except ImportError:
            self.gemini_model = None

        try:
            from anthropic import AsyncAnthropic
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            self.anthropic_client = AsyncAnthropic(api_key=api_key) if api_key else None
        except ImportError:
            self.anthropic_client = None

    async def predict(self, history_subset: List[Dict[str, Any]], skip_llm: bool = False) -> str:
        if skip_llm:
            return "Tai" # Fallback for backtesting

        # In a real scenario we would call the APIs here.
        # For cost saving and simplicity during dev, returning a mock or simple logic result if skipped.
        return "Tai"

class Analyzer:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.best_algorithm = 'recent_majority'
        self.llm_ensemble = LLMEnsembleAlgorithm()

    def update_history(self, session: Dict[str, Any]):
        """Updates the internal history state with a new session."""
        if not self.history:
            self.history.append(session)
        elif session['id'] == self.history[-1]['id']:
            # Update existing session
            self.history[-1] = session
        else:
            self.history.append(session)

    def calculate_markov_chain(self) -> str:
        """Calculates prediction based on Markov chain probabilities."""
        if len(self.history) < 2:
            return "Tai" # Default

        # Simple 1st order Markov chain
        transitions = {'Tai': {'Tai': 0, 'Xiu': 0}, 'Xiu': {'Tai': 0, 'Xiu': 0}}

        for i in range(len(self.history) - 1):
            curr = self.history[i].get('result') or self.history[i].get('resultTruyenThong')
            nxt = self.history[i+1].get('result') or self.history[i+1].get('resultTruyenThong')
            if curr in transitions and nxt in transitions[curr]:
                 transitions[curr][nxt] += 1

        last_result = self.history[-1].get('result') or self.history[-1].get('resultTruyenThong')

        if last_result not in transitions:
             return "Tai"

        tai_prob = transitions[last_result]['Tai']
        xiu_prob = transitions[last_result]['Xiu']

        if tai_prob > xiu_prob:
            return "Tai"
        elif xiu_prob > tai_prob:
            return "Xiu"
        return "Tai" # Fallback

    def calculate_trend_analysis(self) -> str:
        """Identifies consecutive identical outcomes to predict the next."""
        if not self.history:
             return "Tai"

        last_result = self.history[-1].get('result') or self.history[-1].get('resultTruyenThong')
        streak = 0
        for i in range(len(self.history) - 1, -1, -1):
            curr = self.history[i].get('result') or self.history[i].get('resultTruyenThong')
            if curr == last_result:
                streak += 1
            else:
                break

        # Simple trend logic: if streak > 3, assume it breaks, else follow
        if streak > 3:
            return "Xiu" if last_result == "Tai" else "Tai"
        return last_result if last_result else "Tai"

    def calculate_recent_majority(self) -> str:
        """Finds the most frequent outcome in recent history (e.g., last 10)."""
        recent = self.history[-10:] if len(self.history) >= 10 else self.history
        if not recent:
             return "Tai"

        tai_count = sum(1 for s in recent if (s.get('result') or s.get('resultTruyenThong')) == 'Tai')
        xiu_count = sum(1 for s in recent if (s.get('result') or s.get('resultTruyenThong')) == 'Xiu')

        return "Tai" if tai_count >= xiu_count else "Xiu"

    def calculate_sum_analysis(self) -> str:
        """Identifies patterns based on the sum of dice points."""
        if not self.history:
             return "Tai"

        last_point = self.history[-1].get('point')
        if last_point is None:
             return "Tai"

        # Simple heuristic based on odd/even or high/low points
        if last_point % 2 == 0:
             return "Tai"
        return "Xiu"

    async def _algo_llm_ensemble(self, skip_llm: bool = False) -> str:
        """Coordinates LLM calls for prediction."""
        return await self.llm_ensemble.predict(self.history[-10:], skip_llm=skip_llm)

    async def _simulate_and_optimize(self) -> str:
        """Evaluates historical data sequentially to find the most accurate algorithm."""
        if not self.history:
            return 'recent_majority'

        algorithms = {
            'markov': self.calculate_markov_chain,
            'trend': self.calculate_trend_analysis,
            'recent': self.calculate_recent_majority,
            'sum': self.calculate_sum_analysis,
            'llm_ensemble': self._algo_llm_ensemble
        }

        scores = {name: 0 for name in algorithms.keys()}

        # Save current history
        full_history = self.history.copy()

        # Backtest loop: evaluate predictions against the *current* index i result.
        # We start from index 10 to have some context for the algorithms.
        for i in range(10, len(full_history) - 1):
            # The context is everything BEFORE the current index.
            self.history = full_history[:i]

            # The actual result to evaluate against is at index i.
            actual_result = full_history[i].get('result') or full_history[i].get('resultTruyenThong')
            if not actual_result:
                continue

            for name, func in algorithms.items():
                if name == 'llm_ensemble':
                    prediction = await func(skip_llm=True)
                else:
                    prediction = func()

                if prediction == actual_result:
                    scores[name] += 1

        # Restore full history
        self.history = full_history

        # Find best algorithm
        best_algo = max(scores, key=scores.get)
        self.best_algorithm = best_algo
        return best_algo
