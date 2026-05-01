import collections
import logging

class Analyzer:
    def __init__(self):
        self.history = []
        self.algorithms = ['markov', 'trend', 'recent_majority', 'sum_analysis']
        self.best_algorithm = 'recent_majority'
        self.accuracy_stats = {alg: 0.0 for alg in self.algorithms}
        self.total_simulations = 0
        self.correct_simulations = {alg: 0 for alg in self.algorithms}

    def add_history(self, session_data):
        self.history.append(session_data)

    def set_history(self, history):
        self.history = history

    def predict(self, session_id=None):
        if not self.history:
            return "UNKNOWN"

        if self.best_algorithm == 'markov':
            return self._predict_markov()
        elif self.best_algorithm == 'trend':
            return self._predict_trend()
        elif self.best_algorithm == 'recent_majority':
            return self._predict_recent_majority()
        elif self.best_algorithm == 'sum_analysis':
            return self._predict_sum_analysis()
        else:
            return self._predict_recent_majority()

    def _predict_markov(self, history=None):
        hist = history if history is not None else self.history
        if len(hist) < 2:
            return "TAI"

        last_result = hist[-1].get('resultTruyenThong')
        if not last_result:
            return "TAI"

        # Count transitions
        transitions = {'TAI': {'TAI': 0, 'XIU': 0}, 'XIU': {'TAI': 0, 'XIU': 0}}
        for i in range(len(hist) - 1):
            current = hist[i].get('resultTruyenThong')
            next_res = hist[i+1].get('resultTruyenThong')
            if current in transitions and next_res in transitions[current]:
                transitions[current][next_res] += 1

        tai_prob = transitions[last_result]['TAI']
        xiu_prob = transitions[last_result]['XIU']

        if tai_prob > xiu_prob:
            return "TAI"
        elif xiu_prob > tai_prob:
            return "XIU"
        else:
            return "TAI"  # default

    def _predict_trend(self, history=None):
        hist = history if history is not None else self.history
        if not hist:
            return "TAI"

        # Look at last 3 to find a trend
        recent = [s.get('resultTruyenThong') for s in hist[-3:]]
        if len(recent) >= 2 and recent[-1] == recent[-2]:
            return recent[-1]  # Continue trend

        # Or switch
        last = recent[-1]
        return "XIU" if last == "TAI" else "TAI"

    def _predict_recent_majority(self, history=None):
        hist = history if history is not None else self.history
        if not hist:
            return "TAI"

        # Look at last 5
        recent = [s.get('resultTruyenThong') for s in hist[-5:] if s.get('resultTruyenThong')]
        tai_count = recent.count('TAI')
        xiu_count = recent.count('XIU')

        if tai_count > xiu_count:
            return 'TAI'
        elif xiu_count > tai_count:
            return 'XIU'
        else:
            return 'TAI'

    def _predict_sum_analysis(self, history=None):
        hist = history if history is not None else self.history
        if not hist:
            return "TAI"

        # Look at recent sums
        recent_sums = [s.get('point') for s in hist[-3:] if s.get('point') is not None]
        if not recent_sums:
            return "TAI"

        # Simple logic: if sum is increasing, predict TAI
        if len(recent_sums) >= 2 and recent_sums[-1] > recent_sums[-2]:
            return "TAI"
        # If decreasing predict XIU
        elif len(recent_sums) >= 2 and recent_sums[-1] < recent_sums[-2]:
            return "XIU"
        else:
            # Look at dice directly as an alternate strategy
            last_session = hist[-1]
            dices = last_session.get('dices', [])
            if len(dices) == 3:
                # E.g., if there are 6s, more likely TAI
                if 6 in dices: return "TAI"
                if 1 in dices: return "XIU"
            return "TAI"

    def _simulate_and_optimize(self):
        if len(self.history) < 20:
            return

        self.total_simulations += 1

        # Test each algorithm against the last N steps of history
        for alg in self.algorithms:
            correct = 0
            test_size = min(len(self.history) - 10, 50) # use last 50 transitions for backtest

            for i in range(len(self.history) - test_size, len(self.history)):
                sub_history = self.history[:i]
                actual = self.history[i].get('resultTruyenThong')

                if alg == 'markov':
                    pred = self._predict_markov(sub_history)
                elif alg == 'trend':
                    pred = self._predict_trend(sub_history)
                elif alg == 'sum_analysis':
                    pred = self._predict_sum_analysis(sub_history)
                else:
                    pred = self._predict_recent_majority(sub_history)

                if pred == actual:
                    correct += 1

            # Update overall correctness
            self.correct_simulations[alg] += correct
            self.accuracy_stats[alg] = self.correct_simulations[alg] / (self.total_simulations * test_size)

        # Select best algorithm
        best_alg = max(self.accuracy_stats, key=self.accuracy_stats.get)
        if self.accuracy_stats[best_alg] > 0:
            self.best_algorithm = best_alg

        logging.info(f"Optimized logic. Best algorithm: {self.best_algorithm}. Stats: {self.accuracy_stats}")
