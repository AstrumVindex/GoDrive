# drive_service.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from drive_bot.config import SCOPES, SERVICE_ACCOUNT_FILE
import logging

logger = logging.getLogger(__name__)

try:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    logger.info("Google Drive service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Google Drive service: {e}")
    raise

# Explicitly export drive_service
__all__ = ['drive_service']