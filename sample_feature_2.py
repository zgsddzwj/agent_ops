# Sample feature 2 - Agent monitoring tool
import time

def monitor_agent_performance(agent_id, duration=60):
    """Monitor agent performance metrics over time."""
    metrics = []
    for i in range(duration):
        # Simulate metrics collection
        cpu_usage = 45 + (i % 20)
        memory_usage = 70 + (i % 15)
        metrics.append({
            'timestamp': time.time() + i,
            'cpu': cpu_usage,
            'memory': memory_usage
        })
    return metrics