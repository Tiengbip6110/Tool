import logging

logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self):
        self.history = []
        self.best_algorithm = "recent_majority"
        self.algorithms = ["markov_chain", "trend_analysis", "recent_majority", "sum_analysis"]
        self.algorithm_accuracy = {algo: 0.0 for algo in self.algorithms}
        self.total_predictions = {algo: 0 for algo in self.algorithms}
        self.correct_predictions = {algo: 0 for algo in self.algorithms}

    def add_session(self, session_data):
        self.history.append(session_data)
        # Keep history manageable if needed, though backtesting needs it
        # if len(self.history) > 1000:
        #     self.history.pop(0)

    def _get_result_from_point(self, point):
        return "Tai" if point >= 11 else "Xiu"

    def markov_chain_predict(self, history):
        if len(history) < 2:
            return "Tai"

        transitions = {"Tai": {"Tai": 0, "Xiu": 0}, "Xiu": {"Tai": 0, "Xiu": 0}}
        for i in range(len(history) - 1):
            curr_res = self._get_result_from_point(history[i]['point'])
            next_res = self._get_result_from_point(history[i+1]['point'])
            transitions[curr_res][next_res] += 1

        last_res = self._get_result_from_point(history[-1]['point'])

        tai_prob = transitions[last_res]["Tai"]
        xiu_prob = transitions[last_res]["Xiu"]

        if tai_prob > xiu_prob:
            return "Tai"
        elif xiu_prob > tai_prob:
            return "Xiu"
        else:
            return "Tai" # Default

    def trend_analysis_predict(self, history):
        if len(history) < 3:
            return "Tai"

        recent = history[-3:]
        results = [self._get_result_from_point(s['point']) for s in recent]

        if results == ["Tai", "Tai", "Tai"]:
            return "Xiu" # Expecting a break
        elif results == ["Xiu", "Xiu", "Xiu"]:
            return "Tai" # Expecting a break
        else:
            return results[-1] # Follow the last trend

    def recent_majority_predict(self, history):
        if len(history) < 5:
            return "Tai"

        recent = history[-5:]
        tai_count = sum(1 for s in recent if self._get_result_from_point(s['point']) == "Tai")
        if tai_count >= 3:
            return "Tai"
        return "Xiu"

    def sum_analysis_predict(self, history):
        if len(history) < 1:
            return "Tai"

        last_point = history[-1]['point']
        # Very rudimentary logic based on sums
        if last_point in [11, 12, 13]:
            return "Xiu" # High Tai might lead to Xiu
        elif last_point in [8, 9, 10]:
            return "Tai" # High Xiu might lead to Tai
        return self._get_result_from_point(last_point)

    async def ensemble_predict(self, ai_clients=None, history=None):
        if history is None:
            history = self.history

        if not history:
            return "Tai"

        # If we have ai_clients properly injected, let's use the best one or fallback to algo
        # For simplicity in this backtest loop we rely on algorithmic best_algorithm
        # However, we integrate a hook here for future LLM enhancements if keys are provided.
        if ai_clients:
            if ai_clients.openai_api_key and self.best_algorithm == "openai":
                res = await ai_clients.get_openai_prediction(history)
                if res: return res
            elif ai_clients.gemini_api_key and self.best_algorithm == "gemini":
                res = await ai_clients.get_gemini_prediction(history)
                if res: return res
            # Extendable to others

        if self.best_algorithm == "markov_chain":
            return self.markov_chain_predict(history)
        elif self.best_algorithm == "trend_analysis":
            return self.trend_analysis_predict(history)
        elif self.best_algorithm == "recent_majority":
            return self.recent_majority_predict(history)
        elif self.best_algorithm == "sum_analysis":
            return self.sum_analysis_predict(history)

        return self.recent_majority_predict(history)

    def _simulate_and_optimize(self):
        logger.info("Running simulation and optimization...")

        if len(self.history) < 20:
            logger.info("Not enough history to optimize.")
            return

        # Reset stats
        self.total_predictions = {algo: 0 for algo in self.algorithms}
        self.correct_predictions = {algo: 0 for algo in self.algorithms}

        # Simulate over history
        for i in range(10, len(self.history) - 1):
            sub_history = self.history[:i]
            actual_next_result = self._get_result_from_point(self.history[i]['point'])

            preds = {
                "markov_chain": self.markov_chain_predict(sub_history),
                "trend_analysis": self.trend_analysis_predict(sub_history),
                "recent_majority": self.recent_majority_predict(sub_history),
                "sum_analysis": self.sum_analysis_predict(sub_history)
            }

            for algo, pred in preds.items():
                self.total_predictions[algo] += 1
                if pred == actual_next_result:
                    self.correct_predictions[algo] += 1

        # Calculate accuracy and update best
        best_acc = -1
        best_algo = self.algorithms[0]

        for algo in self.algorithms:
            if self.total_predictions[algo] > 0:
                acc = self.correct_predictions[algo] / self.total_predictions[algo]
                self.algorithm_accuracy[algo] = acc
                if acc > best_acc:
                    best_acc = acc
                    best_algo = algo

        self.best_algorithm = best_algo
        logger.info(f"Optimization complete. Best algorithm: {self.best_algorithm} with {best_acc*100:.2f}% accuracy.")

    def get_stats(self):
        stats = "Algorithm Stats:\n"
        for algo in self.algorithms:
            acc = self.algorithm_accuracy.get(algo, 0.0) * 100
            stats += f"- {algo}: {acc:.2f}%\n"
        stats += f"Current Best: {self.best_algorithm}"
        return stats
