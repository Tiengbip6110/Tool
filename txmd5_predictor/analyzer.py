import logging
from collections import defaultdict
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class Txmd5Analyzer:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.algorithm_weights = {
            'markov': 1.0,
            'trend': 1.0,
            'recent_majority': 1.0,
            'sum_analysis': 1.0
        }
        self.best_logic_name = "initial_equal_weights"
        self.accuracy_stats = {k: {'correct': 0, 'total': 0} for k in self.algorithm_weights.keys()}

    def add_history(self, session_data: Dict[str, Any]):
        """Adds a new session to the history."""
        # session_data example: {'phien': 123, 'result': 14, 'dice1': 4, 'dice2': 4, 'dice3': 6}
        self.history.append(session_data)

    def process_initial_batch(self, batch_data: List[Dict[str, Any]]):
        """Processes the first API fetch (which usually contains many items). Reverse to oldest->newest."""
        # The API likely returns newest first, so we reverse it
        reversed_batch = list(reversed(batch_data))
        for item in reversed_batch:
            self.add_history(item)
        logger.info(f"Processed initial batch of {len(reversed_batch)} sessions for backtesting.")
        self._simulate_and_optimize()

    def determine_outcome(self, sum_val: int) -> str:
        """Helper: returns 'Tai' if sum > 10, else 'Xiu'."""
        return "Tai" if sum_val > 10 else "Xiu"

    def predict_markov(self) -> Tuple[str, float]:
        """Simple Markov Chain: prediction based on transition probability from current state."""
        if len(self.history) < 2:
            return "Tai", 0.5

        transitions = defaultdict(lambda: {'Tai': 0, 'Xiu': 0})
        for i in range(len(self.history) - 1):
            curr_outcome = self.determine_outcome(self.history[i]['point'])
            next_outcome = self.determine_outcome(self.history[i+1]['point'])
            transitions[curr_outcome][next_outcome] += 1

        current_state = self.determine_outcome(self.history[-1]['point'])
        t_counts = transitions[current_state]
        total_t = t_counts['Tai'] + t_counts['Xiu']

        if total_t == 0:
            return ("Tai", 0.5) if current_state == "Xiu" else ("Xiu", 0.5)

        tai_prob = t_counts['Tai'] / total_t
        if tai_prob > 0.5:
            return "Tai", tai_prob
        elif tai_prob < 0.5:
            return "Xiu", 1.0 - tai_prob
        else:
            return "Tai", 0.5

    def predict_trend(self) -> Tuple[str, float]:
        """Trend Analysis: looks for consecutive runs."""
        if not self.history:
            return "Tai", 0.5

        outcomes = [self.determine_outcome(h['point']) for h in self.history[-10:]]
        if len(outcomes) < 2:
            return "Tai", 0.5

        last = outcomes[-1]
        run_length = 1
        for i in range(len(outcomes)-2, -1, -1):
            if outcomes[i] == last:
                run_length += 1
            else:
                break

        # Simple heuristic: runs of 3+ often break, runs of 1-2 often continue
        if run_length >= 4:
            predicted = "Tai" if last == "Xiu" else "Xiu"
            return predicted, min(0.6 + (run_length * 0.05), 0.95)
        else:
            return last, 0.55

    def predict_recent_majority(self) -> Tuple[str, float]:
        """Recent Majority: prediction based on the most frequent outcome in last N games."""
        if not self.history:
            return "Tai", 0.5

        recent = [self.determine_outcome(h['point']) for h in self.history[-15:]]
        tai_count = recent.count("Tai")
        xiu_count = recent.count("Xiu")

        if tai_count > xiu_count:
            return "Tai", tai_count / len(recent)
        elif xiu_count > tai_count:
            return "Xiu", xiu_count / len(recent)
        else:
            return "Tai", 0.5

    def predict_sum_analysis(self) -> Tuple[str, float]:
        """Sum Analysis: Uses average sum to predict momentum."""
        if not self.history:
            return "Tai", 0.5

        recent_sums = [h['point'] for h in self.history[-5:]]
        avg_sum = sum(recent_sums) / len(recent_sums)

        # If the average sum is trending high, predict Tai
        if avg_sum > 10.5:
            return "Tai", min(0.5 + (avg_sum - 10.5)*0.05, 0.9)
        else:
            return "Xiu", min(0.5 + (10.5 - avg_sum)*0.05, 0.9)

    def ensemble_predict(self) -> Tuple[str, float, str]:
        """Combines predictions based on dynamically adjusted weights."""
        preds = {
            'markov': self.predict_markov(),
            'trend': self.predict_trend(),
            'recent_majority': self.predict_recent_majority(),
            'sum_analysis': self.predict_sum_analysis()
        }

        tai_score = 0.0
        xiu_score = 0.0
        total_weight = sum(self.algorithm_weights.values())

        if total_weight == 0:
            self.algorithm_weights = {k: 1.0 for k in self.algorithm_weights}
            total_weight = len(self.algorithm_weights)

        for alg, (pred_outcome, conf) in preds.items():
            weight = self.algorithm_weights[alg]
            normalized_weight = weight / total_weight

            if pred_outcome == "Tai":
                tai_score += conf * normalized_weight
            else:
                xiu_score += conf * normalized_weight

        if tai_score > xiu_score:
            return "Tai", tai_score, "ensemble_tai_heavy"
        elif xiu_score > tai_score:
            return "Xiu", xiu_score, "ensemble_xiu_heavy"
        else:
            return "Tai", 0.5, "ensemble_neutral"

    def _simulate_and_optimize(self):
        """Re-evaluates history to adjust algorithm weights based on recent accuracy."""
        if len(self.history) < 20:
            return

        # Reset stats
        for k in self.accuracy_stats.keys():
            self.accuracy_stats[k] = {'correct': 0, 'total': 0}

        # Simulate last 50 games (or less if not enough history)
        sim_start = max(10, len(self.history) - 50)

        for i in range(sim_start, len(self.history)):
            # State of history just before this game
            temp_history = self.history[:i]
            actual_outcome = self.determine_outcome(self.history[i]['point'])

            # Temporary replace history to use predict methods
            original_history = self.history
            self.history = temp_history

            try:
                p_markov, _ = self.predict_markov()
                p_trend, _ = self.predict_trend()
                p_recent, _ = self.predict_recent_majority()
                p_sum, _ = self.predict_sum_analysis()

                preds = {
                    'markov': p_markov,
                    'trend': p_trend,
                    'recent_majority': p_recent,
                    'sum_analysis': p_sum
                }

                for alg, pred in preds.items():
                    self.accuracy_stats[alg]['total'] += 1
                    if pred == actual_outcome:
                        self.accuracy_stats[alg]['correct'] += 1
            finally:
                # Restore history
                self.history = original_history

        # Update weights based on accuracy
        best_alg = None
        best_acc = -1.0

        for alg, stats in self.accuracy_stats.items():
            if stats['total'] > 0:
                accuracy = stats['correct'] / stats['total']
                # Base weight is accuracy, squared to punish low accuracy more
                self.algorithm_weights[alg] = max(0.1, accuracy ** 2)

                if accuracy > best_acc:
                    best_acc = accuracy
                    best_alg = alg

        if best_alg:
            self.best_logic_name = best_alg
            logger.info(f"Optimized weights: {self.algorithm_weights}. Best logic: {best_alg} ({best_acc*100:.1f}%)")

    def get_stats_summary(self) -> dict:
        return {
            'best_logic': self.best_logic_name,
            'weights': self.algorithm_weights,
            'total_history_analyzed': len(self.history)
        }
