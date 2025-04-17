# drive_bot/__init__.py
import logging
from drive_bot.logger import setup_logging
from drive_bot.database import init_db

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)

# Then initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")
    raise

__version__ = "1.2.0"

# Import handlers (now using absolute imports)
from drive_bot.handlers.start_handler import start
from drive_bot.handlers.upload_handler import upload_image
# Import other handlers as needed

__all__ = [
    'start',
    'upload_image',
    # Add other handlers here
]