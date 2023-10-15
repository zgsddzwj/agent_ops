# Sample feature 3 - Configuration validator
import json

def validate_config(config_dict):
    """Validate agent configuration dictionary."""
    required_fields = ['name', 'type', 'endpoints']
    missing_fields = [field for field in required_fields if field not in config_dict]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    return True

def load_config_from_file(filepath):
    """Load and validate configuration from JSON file."""
    with open(filepath, 'r') as f:
        config = json.load(f)
    return validate_config(config)