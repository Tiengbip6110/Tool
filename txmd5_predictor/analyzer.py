import random
from collections import defaultdict
import os
import asyncio

# The analyzer class is responsible for determining the best predicting algorithm
# based on historical data.
class Analyzer:
    def __init__(self):
        self.history = []
        self.best_algo_name = 'random'
        self.win_rate = 0.0
        self.total_predictions = 0
        self.correct_predictions = 0
        self.algorithms = {
            'random': self._algo_random,
            'recent_majority': self._algo_recent_majority,
            'markov_chain': self._algo_markov_chain,
            'trend': self._algo_trend,
            'sum_analysis': self._algo_sum_analysis,
            'llm_ensemble': self._algo_llm_ensemble
        }

    def update_history(self, session_data):
        """Adds or updates a session in the history."""
        if not self.history:
            self.history.append(session_data)
        elif self.history[-1]['id'] == session_data['id']:
            # Update the latest session (e.g. when it finishes and gets a result)
            self.history[-1] = session_data
        else:
            self.history.append(session_data)

    def predict_next(self, skip_llm=False):
        """Predicts the next outcome based on the currently best selected algorithm."""
        if not self.history:
            return random.choice(['TAI', 'XIU'])

        algo = self.algorithms.get(self.best_algo_name, self._algo_random)

        # Pass skip_llm flag if calling llm_ensemble to save costs
        if self.best_algo_name == 'llm_ensemble':
             return algo(self.history, skip_llm=skip_llm)
        else:
             # Most algorithms don't take skip_llm
             return algo(self.history)

    def _simulate_and_optimize(self, new_history):
        """
        Backtests all algorithms on the provided history (from oldest to newest)
        to find the one with the highest accuracy.
        """
        if len(new_history) < 10:
            self.history = new_history
            return

        algo_scores = {name: 0 for name in self.algorithms.keys()}
        total_evaluations = 0

        # Start evaluation from index 5 to have at least some context
        for i in range(5, len(new_history)):
            sub_history = new_history[:i]
            actual_result = new_history[i].get('result') or new_history[i].get('resultTruyenThong')

            if not actual_result:
                continue

            total_evaluations += 1

            for name, algo_func in self.algorithms.items():
                try:
                    if name == 'llm_ensemble':
                        pred = algo_func(sub_history, skip_llm=True) # Always skip LLM in backtesting to save costs and time
                    else:
                        pred = algo_func(sub_history)

                    if pred == actual_result:
                        algo_scores[name] += 1
                except Exception as e:
                    pass

        if total_evaluations > 0:
            best_algo = max(algo_scores, key=algo_scores.get)
            best_score = algo_scores[best_algo]

            self.best_algo_name = best_algo
            self.win_rate = (best_score / total_evaluations) * 100

            # Print for debug
            print(f"[Optimization] Best Algorithm: {best_algo} with {self.win_rate:.2f}% Win Rate")

        self.history = new_history


    # --- Algorithms ---

    def _algo_random(self, sub_history):
        return random.choice(['TAI', 'XIU'])

    def _algo_recent_majority(self, sub_history):
        """Predicts based on the most frequent result in the last 5 sessions."""
        recent = sub_history[-5:]
        tais = sum(1 for s in recent if (s.get('result') or s.get('resultTruyenThong')) == 'TAI')
        xius = sum(1 for s in recent if (s.get('result') or s.get('resultTruyenThong')) == 'XIU')
        return 'TAI' if tais > xius else 'XIU'

    def _algo_markov_chain(self, sub_history):
        """Uses a simple first-order Markov chain."""
        if len(sub_history) < 2:
            return random.choice(['TAI', 'XIU'])

        transitions = defaultdict(lambda: {'TAI': 0, 'XIU': 0})
        for i in range(len(sub_history) - 1):
            curr = sub_history[i].get('result') or sub_history[i].get('resultTruyenThong')
            nxt = sub_history[i+1].get('result') or sub_history[i+1].get('resultTruyenThong')
            if curr and nxt:
                transitions[curr][nxt] += 1

        last_result = sub_history[-1].get('result') or sub_history[-1].get('resultTruyenThong')
        if not last_result or last_result not in transitions:
             return random.choice(['TAI', 'XIU'])

        tai_prob = transitions[last_result]['TAI']
        xiu_prob = transitions[last_result]['XIU']

        return 'TAI' if tai_prob > xiu_prob else 'XIU'

    def _algo_trend(self, sub_history):
        """Checks if there's a strong trend (streak) currently."""
        if not sub_history:
             return random.choice(['TAI', 'XIU'])

        last_result = sub_history[-1].get('result') or sub_history[-1].get('resultTruyenThong')
        streak = 1
        for i in range(len(sub_history) - 2, -1, -1):
            if (sub_history[i].get('result') or sub_history[i].get('resultTruyenThong')) == last_result:
                streak += 1
            else:
                break

        # If the streak is long (>=3), assume it will break soon (reversion).
        # If it's short, assume it continues.
        # This is a basic heuristic, can be adjusted.
        if streak >= 3:
            return 'TAI' if last_result == 'XIU' else 'XIU'
        else:
            return last_result

    def _algo_sum_analysis(self, sub_history):
        """Analyzes the relationship between the sum of dice (point) and the next outcome."""
        if len(sub_history) < 2:
            return random.choice(['TAI', 'XIU'])

        # Map sum to next outcome
        sum_to_next = defaultdict(lambda: {'TAI': 0, 'XIU': 0})
        for i in range(len(sub_history) - 1):
            point = sub_history[i].get('point')
            nxt_result = sub_history[i+1].get('result') or sub_history[i+1].get('resultTruyenThong')
            if point is not None and nxt_result:
                sum_to_next[point][nxt_result] += 1

        last_point = sub_history[-1].get('point')
        if last_point is not None and last_point in sum_to_next:
             t = sum_to_next[last_point]['TAI']
             x = sum_to_next[last_point]['XIU']
             if t > x:
                 return 'TAI'
             elif x > t:
                 return 'XIU'

        return random.choice(['TAI', 'XIU'])

    def _algo_llm_ensemble(self, sub_history, skip_llm=False):
        """
        Uses LLM APIs (OpenAI, Gemini, Anthropic) to make an ensemble prediction.
        Since LLMs are slow and cost money, we skip them during backtesting.
        """
        if skip_llm:
            # Fallback to sum_analysis during backtesting to represent this algo
            return self._algo_sum_analysis(sub_history)

        # Try to call APIs asynchronously to get votes
        # Since this method is currently called synchronously in predict_next,
        # we will use asyncio.run to execute the async code. If an event loop is
        # already running, we need a nested mechanism or refactor to make predict_next async.
        # However, due to the complexity and rate limits, we provide a basic implementation.

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # In a running loop context, we might block. But let's assume we can create a task
            # or for simplicity run it directly if we refactored.
            # For this patch, we'll try to run the async calls and wait.
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(self._async_llm_ensemble(sub_history))
        else:
            return loop.run_until_complete(self._async_llm_ensemble(sub_history))

    async def _async_llm_ensemble(self, sub_history):
        # Format recent history for prompt
        recent = sub_history[-10:]
        history_text = ", ".join([f"{s.get('id')}: {s.get('result') or s.get('resultTruyenThong')}" for s in recent])
        prompt = f"Analyze the following Sic Bo game history and predict the next outcome (TAI or XIU). History: {history_text}. Respond only with 'TAI' or 'XIU'."

        votes = []
        tasks = [
            self._call_openai(prompt),
            self._call_gemini(prompt),
            self._call_anthropic(prompt)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, str) and res in ['TAI', 'XIU']:
                votes.append(res)

        if not votes:
            return self._algo_markov_chain(sub_history) # Fallback

        tais = votes.count('TAI')
        xius = votes.count('XIU')
        return 'TAI' if tais > xius else 'XIU'

    async def _call_openai(self, prompt):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            return response.choices[0].message.content.strip().upper()
        except Exception:
            return None

    async def _call_gemini(self, prompt):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            # The gemini client is not fully async out of the box in older versions,
            # but we run it in a way that doesn't completely block if possible, or use sync fallback.
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text.strip().upper()
        except Exception:
            return None

    async def _call_anthropic(self, prompt):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key)
            message = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            # Accessing content text from Anthropic response structure
            return message.content[0].text.strip().upper()
        except Exception as e:
            return None
