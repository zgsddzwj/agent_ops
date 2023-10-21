# Logging utility for Agent Ops
import logging
import json
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # File handler (if log_file specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    if log_file:
        file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

class JsonLogger:
    """JSON format logger for structured logging."""
    
    def __init__(self, log_file):
        self.log_file = log_file
    
    def log(self, level, message, **kwargs):
        """Log a message in JSON format."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'data': kwargs
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def info(self, message, **kwargs):
        """Log an info message."""
        self.log('INFO', message, **kwargs)
    
    def warning(self, message, **kwargs):
        """Log a warning message."""
        self.log('WARNING', message, **kwargs)
    
    def error(self, message, **kwargs):
        """Log an error message."""
        self.log('ERROR', message, **kwargs)