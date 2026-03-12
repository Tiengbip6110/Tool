from collections import Counter
import logging

class Predictor:
    """Class đại diện cho một thuật toán dự đoán."""
    def __init__(self, name: str):
        self.name = name
        self.correct_predictions = 0
        self.total_predictions = 0
        self.current_prediction = None

    def get_accuracy(self) -> float:
        if self.total_predictions == 0:
            return 0.0
        return (self.correct_predictions / self.total_predictions) * 100

    def predict(self, history: list[dict]) -> str:
        """Nhận vào danh sách lịch sử và trả về 'TAI' hoặc 'XIU'."""
        pass

    def evaluate(self, actual_result: str):
        """Đánh giá dự đoán gần nhất."""
        if self.current_prediction is None:
            return

        self.total_predictions += 1
        if self.current_prediction == actual_result:
            self.correct_predictions += 1

        # Reset sau khi đánh giá
        self.current_prediction = None

class FrequencyAnalysis(Predictor):
    """Thống kê tần suất: Dựa vào TÀI/XỈU xuất hiện nhiều nhất trong N ván gần nhất."""
    def __init__(self, window_size: int = 20):
        super().__init__(f"Tần suất ({window_size} ván)")
        self.window_size = window_size

    def predict(self, history: list[dict]) -> str:
        if not history:
            self.current_prediction = "TAI" # Default
            return self.current_prediction

        recent = history[:self.window_size]
        results = [r.get('calculated_result', r.get('resultTruyenThong')) for r in recent]
        counts = Counter(results)

        # Dự đoán ngược lại hoặc theo số đông tuỳ vào logic, ở đây ví dụ đơn giản nhất là dự đoán theo số đông
        most_common = counts.most_common(1)[0][0]
        self.current_prediction = most_common
        return self.current_prediction

class MarkovChain(Predictor):
    """Chuỗi Markov: Tính xác suất chuyển trạng thái từ quá khứ (ví dụ TAI->XIU, XIU->TAI)."""
    def __init__(self, order: int = 1):
        super().__init__(f"Markov Chain (bậc {order})")
        self.order = order

    def predict(self, history: list[dict]) -> str:
        if len(history) <= self.order:
            self.current_prediction = "XIU" # Default
            return self.current_prediction

        # Tính toán ma trận chuyển trạng thái
        transitions = {'TAI': {'TAI': 0, 'XIU': 0}, 'XIU': {'TAI': 0, 'XIU': 0}}

        # Duyệt từ cũ đến mới (do history đang là mới nhất ở index 0)
        # Để dễ, ta đảo ngược history lại để phân tích chuỗi thời gian
        time_series = [r.get('calculated_result', r.get('resultTruyenThong')) for r in reversed(history)]

        for i in range(len(time_series) - 1):
            current_state = time_series[i]
            next_state = time_series[i+1]
            if current_state in transitions and next_state in transitions[current_state]:
                transitions[current_state][next_state] += 1

        last_state = time_series[-1]

        if last_state not in transitions:
             self.current_prediction = "TAI"
             return self.current_prediction

        tai_prob = transitions[last_state]['TAI']
        xiu_prob = transitions[last_state]['XIU']

        if tai_prob > xiu_prob:
            self.current_prediction = "TAI"
        elif xiu_prob > tai_prob:
            self.current_prediction = "XIU"
        else:
            # Bằng nhau thì dự đoán bẻ cầu
            self.current_prediction = "XIU" if last_state == "TAI" else "TAI"

        return self.current_prediction

class PatternMatching(Predictor):
    """Nhận dạng mẫu: Tìm chuỗi kết quả N ván gần nhất trong toàn bộ lịch sử và xem ván tiếp theo thường là gì."""
    def __init__(self, pattern_length: int = 3):
        super().__init__(f"Nhận dạng Mẫu ({pattern_length} ván)")
        self.pattern_length = pattern_length

    def predict(self, history: list[dict]) -> str:
        if len(history) < self.pattern_length * 2:
            self.current_prediction = "TAI"
            return self.current_prediction

        time_series = [r.get('calculated_result', r.get('resultTruyenThong')) for r in reversed(history)]

        # Mẫu N ván gần nhất
        current_pattern = time_series[-self.pattern_length:]

        next_states = []
        # Tìm trong lịch sử
        for i in range(len(time_series) - self.pattern_length):
            # Cắt mẫu
            hist_pattern = time_series[i : i + self.pattern_length]
            if hist_pattern == current_pattern:
                next_states.append(time_series[i + self.pattern_length])

        if not next_states:
            self.current_prediction = "TAI"
            return self.current_prediction

        counts = Counter(next_states)
        self.current_prediction = counts.most_common(1)[0][0]
        return self.current_prediction

class InversePattern(Predictor):
    """Dự đoán ngược lại với mô hình Tần Suất (bắt cầu bẻ)."""
    def __init__(self, window_size: int = 10):
         super().__init__(f"Đánh Bẻ (Ngược TS {window_size})")
         self.window_size = window_size

    def predict(self, history: list[dict]) -> str:
        if not history:
             self.current_prediction = "XIU"
             return self.current_prediction

        recent = history[:self.window_size]
        results = [r.get('calculated_result', r.get('resultTruyenThong')) for r in recent]
        counts = Counter(results)

        most_common = counts.most_common(1)[0][0]
        # Đảo ngược
        self.current_prediction = "XIU" if most_common == "TAI" else "TAI"
        return self.current_prediction
