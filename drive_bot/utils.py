# utils.py
import os
import asyncio
from drive_bot.config import MAX_RETRIES, DOWNLOADS_DIR
import logging

logger = logging.getLogger(__name__)

async def safe_delete_file(file_path: str, retries: int = MAX_RETRIES):
    """Safely delete a file with retries"""
    # ... existing implementation ...

def ensure_downloads_dir():
    """Ensure downloads directory exists"""
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Only export utils-specific functions
__all__ = ['safe_delete_file', 'ensure_downloads_dir']