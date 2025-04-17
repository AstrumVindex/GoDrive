# drive_bot/logger.py
import logging
import os
from pathlib import Path
from drive_bot.config import LOG_FILE

def setup_logging():
    """Configure logging for the entire application"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Ensure log directory exists
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    # Set higher level for noisy libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)