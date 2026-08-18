import logging

logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self):
        self.history = []
        self.best_algorithm = None
        self.accuracy_stats = {}

    async def _simulate_and_optimize(self):
        """
        Backtests all algorithms on historical data to find the most accurate one.
        Triggers upon prediction failure to dynamically re-evaluate.
        """
        if len(self.history) < 20:
            return

        logger.info("Starting backtesting and optimization...")
        algorithms = ['markov_chain', 'trend_analysis', 'recent_majority', 'sum_analysis', 'llm_ensemble']
        scores = {algo: {'correct': 0, 'total': 0} for algo in algorithms}

        # Test on the last 50 available sessions
        test_range = min(50, len(self.history) - 20)
        start_idx = len(self.history) - test_range - 1

        original_history = list(self.history)

        for i in range(start_idx, len(original_history) - 1):
            # Target is at i+1 based on state at i
            # However, when calculating against sub_history at i, we look at the result AT i+1?
            # Wait, memory says:
            # "when simulating predictions using a specific sub_history index (e.g., `sub_history = self.history[:i]`), the actual result to evaluate the prediction against must correspond to the current index `i` (i.e., using `new_history[i].get('result') or new_history[i].get('resultTruyenThong')`), not `i+1`, to prevent skipping a step"
            # Let's adjust to exactly what memory says.

            sub_history = original_history[:i]
            target_session = original_history[i]
            actual_result = target_session.get('resultTruyenThong') or target_session.get('result')

            if not actual_result:
                continue

            self.history = sub_history

            # Get predictions
            preds = {
                'markov_chain': self._algo_markov_chain(),
                'trend_analysis': self._algo_trend_analysis(),
                'recent_majority': self._algo_recent_majority(),
                'sum_analysis': self._algo_sum_analysis(),
                'llm_ensemble': await self._algo_llm_ensemble(skip_llm=True)
            }

            for algo, pred in preds.items():
                if pred:
                    scores[algo]['total'] += 1
                    if pred == actual_result:
                        scores[algo]['correct'] += 1

        # Restore history
        self.history = original_history

        best_algo = None
        best_acc = 0.0

        for algo, stats in scores.items():
            if stats['total'] > 0:
                acc = stats['correct'] / stats['total']
                self.accuracy_stats[algo] = acc * 100
                if acc > best_acc:
                    best_acc = acc
                    best_algo = algo

        self.best_algorithm = best_algo
        logger.info(f"Optimization complete. Best algorithm: {self.best_algorithm} with {best_acc*100:.2f}% accuracy")

    async def predict_next(self):
        """
        Gets the prediction for the next outcome using the best found algorithm.
        """
        if not self.best_algorithm:
            await self._simulate_and_optimize()

        if not self.best_algorithm:
             return None

        if self.best_algorithm == 'markov_chain':
            return self._algo_markov_chain()
        elif self.best_algorithm == 'trend_analysis':
            return self._algo_trend_analysis()
        elif self.best_algorithm == 'recent_majority':
            return self._algo_recent_majority()
        elif self.best_algorithm == 'sum_analysis':
            return self._algo_sum_analysis()
        elif self.best_algorithm == 'llm_ensemble':
            return await self._algo_llm_ensemble(skip_llm=False)

        return None

    def _algo_markov_chain(self):
        """
        Simple Markov Chain based on transition probabilities of TAI/XIU.
        """
        if len(self.history) < 20:
            return None

        transitions = {'TAI': {'TAI': 0, 'XIU': 0}, 'XIU': {'TAI': 0, 'XIU': 0}}
        last_result = None

        for session in self.history[-50:]:
            res = session.get('resultTruyenThong') or session.get('result')
            if res not in ['TAI', 'XIU']:
                continue

            if last_result:
                transitions[last_result][res] += 1
            last_result = res

        if not last_result:
            return None

        counts = transitions[last_result]
        total = sum(counts.values())
        if total == 0:
            return None

        prob_tai = counts['TAI'] / total
        prob_xiu = counts['XIU'] / total

        return 'TAI' if prob_tai > prob_xiu else 'XIU'

    def _algo_trend_analysis(self):
        """
        Identify recent streaks/trends in results.
        """
        if len(self.history) < 5:
            return None

        recent = []
        for session in reversed(self.history[-10:]):
            res = session.get('resultTruyenThong') or session.get('result')
            if res in ['TAI', 'XIU']:
                recent.append(res)

        if len(recent) < 3:
            return None

        # If the last 3 are the same, bet against the trend (or follow it, depending on strategy)
        # Let's use a strategy: if 3 in a row, predict the same (trend following)
        if recent[0] == recent[1] == recent[2]:
            return recent[0]

        # Alternating trend (e.g. TAI, XIU, TAI)
        if recent[0] != recent[1] and recent[1] != recent[2] and recent[0] == recent[2]:
            # Expect next to be recent[1]
            return recent[1]

        return None

    def _algo_recent_majority(self):
        """
        Predicts based on the most frequent result in the recent window.
        """
        if len(self.history) < 10:
            return None

        counts = {'TAI': 0, 'XIU': 0}
        for session in self.history[-15:]:
            res = session.get('resultTruyenThong') or session.get('result')
            if res in counts:
                counts[res] += 1

        if counts['TAI'] > counts['XIU']:
            return 'TAI'
        elif counts['XIU'] > counts['TAI']:
            return 'XIU'
        return None

    def _algo_sum_analysis(self):
        """
        Analyzes the moving average of dice sum points.
        """
        if len(self.history) < 10:
            return None

        points = []
        for session in self.history[-10:]:
            point = session.get('point')
            if point is not None:
                points.append(point)

        if not points:
            return None

        avg_point = sum(points) / len(points)
        # 10.5 is the middle point (3-18 range)
        return 'TAI' if avg_point > 10.5 else 'XIU'

    async def _algo_llm_ensemble(self, skip_llm=False):
        """
        Calls various LLM APIs to predict the next outcome.
        Respects skip_llm flag to avoid API spam during backtesting.
        """
        if skip_llm:
            return None

        # In a real scenario, this would gather context (recent history)
        # and query OpenAI/Gemini/Anthropic asynchronously.
        # Stub implementation:
        return 'TAI'  # Default stub return for LLM

    def add_session(self, session_data):
        """
        Add a session safely avoiding duplicates.
        Searches the last 10 entries to update if the ID exists.
        Returns True if a new session was added, False if an existing one was updated.
        """
        session_id = session_data.get('id')
        if not session_id:
            return False

        # Look backwards in the last 10 entries for this id
        search_range = min(10, len(self.history))
        for i in range(len(self.history) - 1, len(self.history) - 1 - search_range, -1):
            if self.history[i].get('id') == session_id:
                # Update existing session
                self.history[i].update(session_data)
                return False

        # If not found, add as a new session
        self.history.append(session_data)
        return True
