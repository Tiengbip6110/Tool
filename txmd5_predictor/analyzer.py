import collections

class Analyzer:
    def __init__(self):
        self.history = []
        self.best_algo = "recent_majority"
        self.algorithms = {
            "markov_chain": self._algo_markov_chain,
            "trend_analysis": self._algo_trend_analysis,
            "recent_majority": self._algo_recent_majority,
            "sum_analysis": self._algo_sum_analysis,
            "llm_ensemble": self._algo_llm_ensemble
        }

    def _simulate_and_optimize(self):
        """
        Backtesting loop that iterates over historical data to find the best algorithm.
        """
        if len(self.history) < 20:
            return # Need more data to optimize

        algo_scores = {algo_name: 0 for algo_name in self.algorithms.keys() if algo_name != "llm_ensemble"}

        # Test algorithms on historical data
        for i in range(10, len(self.history)):
            sub_history = self.history[:i]
            # The actual result to evaluate against must correspond to the current index i
            actual_result = self.history[i].get('result') or self.history[i].get('resultTruyenThong')

            if not actual_result:
                continue

            for algo_name, algo_func in self.algorithms.items():
                if algo_name == "llm_ensemble":
                    continue # Skip LLM in bulk simulation to save cost

                prediction = algo_func(sub_history)
                if prediction == actual_result:
                    algo_scores[algo_name] += 1

        # Find the best algorithm
        best_algo_name = max(algo_scores, key=algo_scores.get)
        self.best_algo = best_algo_name
        return best_algo_name, algo_scores[best_algo_name] / (len(self.history) - 10)

    def add_session(self, session):
        self.history.append(session)
        # Keep history bounded if needed, but for backtesting we might keep a lot
        if len(self.history) > 10000:
            self.history.pop(0)

    def get_prediction(self, skip_llm=False):
        if not self.history:
            return "TAI" # Default fallback

        if not skip_llm and self.best_algo == "llm_ensemble":
            algo_func = self.algorithms.get("llm_ensemble")
            return algo_func(self.history, skip_llm=skip_llm)
        else:
            # If skipping LLM or best is not LLM, use standard logic
            algo_func = self.algorithms.get(self.best_algo, self._algo_recent_majority)
            if self.best_algo == "llm_ensemble" and skip_llm:
               algo_func = self._algo_recent_majority # Fallback if skipping

            return algo_func(self.history)

    def _algo_llm_ensemble(self, history, skip_llm=False):
        if skip_llm:
            return self._algo_recent_majority(history)

        # Mock LLM Logic for now, can be extended later
        # In a real scenario, this would format the history and query the APIs
        return self._algo_trend_analysis(history)

    def _algo_markov_chain(self, history):
        if len(history) < 2:
            return "TAI"

        # Build simple 1st order Markov Chain
        transitions = {'TAI': {'TAI': 0, 'XIU': 0}, 'XIU': {'TAI': 0, 'XIU': 0}}
        for i in range(len(history) - 1):
            curr_state = history[i].get('result') or history[i].get('resultTruyenThong')
            next_state = history[i+1].get('result') or history[i+1].get('resultTruyenThong')
            if curr_state and next_state:
                transitions[curr_state][next_state] += 1

        last_state = history[-1].get('result') or history[-1].get('resultTruyenThong')
        if not last_state:
            return "TAI"

        tai_prob = transitions[last_state]['TAI']
        xiu_prob = transitions[last_state]['XIU']

        return "TAI" if tai_prob >= xiu_prob else "XIU"

    def _algo_trend_analysis(self, history):
        # Look for alternating trends or streaks
        if len(history) < 3:
            return "TAI"

        recent = [s.get('result') or s.get('resultTruyenThong') for s in history[-3:]]
        if None in recent:
            return "TAI"

        if recent[0] == recent[1] == recent[2]:
            # Streak of 3, assume it continues
            return recent[-1]
        elif recent[0] != recent[1] and recent[1] != recent[2]:
            # Alternating, assume it continues alternating
            return "TAI" if recent[-1] == "XIU" else "XIU"
        else:
            return self._algo_recent_majority(history)

    def _algo_recent_majority(self, history):
        if not history:
            return "TAI"
        # Look at last 10 games
        recent = [s.get('result') or s.get('resultTruyenThong') for s in history[-10:] if s.get('result') or s.get('resultTruyenThong')]
        if not recent:
            return "TAI"

        counts = collections.Counter(recent)
        # Predict the one that appeared most often recently
        if counts['TAI'] >= counts['XIU']:
            return "TAI"
        else:
            return "XIU"

    def _algo_sum_analysis(self, history):
        if not history:
            return "TAI"

        recent = history[-5:]
        avg_sum = sum(s.get('point', 11) for s in recent) / len(recent)

        # If the average sum is high, assume reversion to mean (XIU)
        # If the average sum is low, assume reversion to mean (TAI)
        if avg_sum > 10.5:
            return "XIU"
        else:
            return "TAI"
