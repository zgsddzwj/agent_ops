# Sample feature 2 - Agent monitoring tool
import time

def monitor_agent_performance(agent_id, duration=60, interval=1):
    """Monitor agent performance metrics over time.
    
    Args:
        agent_id: Unique identifier for the agent
        duration: Monitoring duration in seconds
        interval: Sampling interval in seconds
    
    Returns:
        List of metric dictionaries
    """
    metrics = []
    sample_count = duration // interval
    
    for i in range(sample_count):
        # Simulate metrics collection
        cpu_usage = 45 + (i % 20)
        memory_usage = 70 + (i % 15)
        response_time = 100 + (i % 50)
        
        metrics.append({
            'timestamp': time.time() + i * interval,
            'agent_id': agent_id,
            'cpu': cpu_usage,
            'memory': memory_usage,
            'response_time': response_time
        })
    return metrics