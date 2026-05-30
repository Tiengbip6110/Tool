import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self):
        self.history = []
        self.algorithms = {
            'markov': self._algo_markov,
            'trend': self._algo_trend,
            'majority': self._algo_majority,
            'sum_analysis': self._algo_sum_analysis,
            'llm_ensemble': self._algo_llm_ensemble
        }
        self.best_algorithm = 'trend'
        self.algorithm_performance = {k: 0 for k in self.algorithms.keys()}

    def add_session(self, session_data):
        self.history.append(session_data)
        # Keep history bounded if needed, but since we rewind, we might want to keep a lot.
        if len(self.history) > 1000:
            self.history.pop(0)

    def predict(self, skip_llm=False):
        if not self.history:
            return None

        # Use the best algorithm found so far
        if self.best_algorithm == 'llm_ensemble' and skip_llm:
            # Fallback if LLM is skipped during backtest but was best
            algo = self._algo_trend
        else:
            algo = self.algorithms[self.best_algorithm]

        prediction = algo(self.history, skip_llm=skip_llm) if self.best_algorithm == 'llm_ensemble' else algo(self.history)

        if prediction is None:
             # Fallback
             prediction = self._algo_trend(self.history)
        return prediction

    def _algo_markov(self, history):
        if len(history) < 2:
            return random.choice([1, 2]) # 1: Tài, 2: Xỉu (or whichever representation we use, let's assume 1 is Tai, 2 is Xiu or strings)

        # Simplified Markov: P(Next | Current)
        transitions = defaultdict(lambda: {'Tai': 0, 'Xiu': 0})
        for i in range(len(history) - 1):
            current = self._get_result(history[i])
            next_res = self._get_result(history[i+1])
            transitions[current][next_res] += 1

        last_res = self._get_result(history[-1])
        tai_count = transitions[last_res]['Tai']
        xiu_count = transitions[last_res]['Xiu']

        if tai_count > xiu_count: return 'Tai'
        if xiu_count > tai_count: return 'Xiu'
        return 'Tai' if random.random() > 0.5 else 'Xiu'

    def _algo_trend(self, history):
        if len(history) < 3:
            return 'Tai'
        recent = [self._get_result(h) for h in history[-3:]]
        if recent == ['Tai', 'Tai', 'Tai']: return 'Tai'
        if recent == ['Xiu', 'Xiu', 'Xiu']: return 'Xiu'
        return recent[-1] # Follow last

    def _algo_majority(self, history):
        if not history: return 'Tai'
        recent = [self._get_result(h) for h in history[-10:]]
        tai = recent.count('Tai')
        xiu = recent.count('Xiu')
        return 'Tai' if tai > xiu else 'Xiu'

    def _algo_sum_analysis(self, history):
         if not history: return 'Tai'
         last_sum = history[-1].get('point', 0)
         if last_sum > 10:
             return 'Xiu' # basic mean reversion logic for example
         return 'Tai'

    def _algo_llm_ensemble(self, history, skip_llm=False):
        if skip_llm:
            return self._algo_trend(history)
        # Mock LLM API calls integration (OpenAI, Gemini, Anthropic, Grok, DeepSeek)
        # In a real scenario, this would make async calls. Here we simulate.
        logger.debug("Calling LLMs for prediction...")
        return random.choice(['Tai', 'Xiu'])

    def _get_result(self, session):
        point = session.get('point', 0)
        return 'Tai' if point >= 11 else 'Xiu'

    def _simulate_and_optimize(self):
        logger.info("Starting simulation and optimization...")
        if len(self.history) < 20:
            return

        scores = {k: 0 for k in self.algorithms.keys()}

        for i in range(10, len(self.history) - 1):
            sub_history = self.history[:i]
            actual_result = self._get_result(self.history[i])

            for name, algo in self.algorithms.items():
                try:
                    if name == 'llm_ensemble':
                        pred = algo(sub_history, skip_llm=True)
                    else:
                        pred = algo(sub_history)

                    if pred == actual_result:
                        scores[name] += 1
                except Exception as e:
                    logger.error(f"Error in algo {name}: {e}")

        best_algo = max(scores, key=scores.get)
        self.best_algorithm = best_algo
        self.algorithm_performance = scores
        logger.info(f"Optimization complete. Best algorithm: {best_algo}. Scores: {scores}")
