import time

class LLMMetrics:
    def __init__(self):
        self.metrics_history = []

    def start_timer(self):
        return time.time()

    def stop_timer(self, start_time):
        return time.time() - start_time

    def record_metrics(self, prompt_tokens, completion_tokens, latency, provider):
        """Ghi nhận hiệu năng và tính toán chi phí ước tính"""
        rates = {
            "gemini": {"input": 0.075, "output": 0.30},
            "local": {"input": 0.0, "output": 0.0}
        }
        
        rate = rates.get(provider.lower(), {"input": 0.0, "output": 0.0})
        cost = ((prompt_tokens / 1_000_000) * rate["input"]) + ((completion_tokens / 1_000_000) * rate["output"])
        
        # Tính toán Token Ratio (Tỷ lệ sinh chữ so với độ dài của Prompt)
        token_ratio = round(completion_tokens / prompt_tokens, 2) if prompt_tokens > 0 else 0
        
        metric_data = {
            "provider": provider,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "token_ratio": token_ratio,
            "latency_seconds": round(latency, 3),
            "estimated_cost_usd": round(cost, 6)
        }
        self.metrics_history.append(metric_data)
        return metric_data

# QUAN TRỌNG NHẤT LÀ DÒNG NÀY: Khởi tạo biến để agent.py có thể import
metrics_tracker = LLMMetrics()