# Advanced Agent Ops Usage

## API Reference

### Performance Monitoring
- `monitor_agent_performance(agent_id, duration=60)`
- Returns real-time metrics for CPU and memory usage

### Configuration
- `validate_config(config_dict)` - Validates agent configuration
- `load_config_from_file(filepath)` - Loads config from JSON file

## Best Practices
1. Always validate configurations before deployment
2. Monitor performance metrics regularly
3. Set up alerts for critical thresholds