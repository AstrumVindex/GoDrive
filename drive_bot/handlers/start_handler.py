from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with bot instructions"""
    try:
        await update.message.reply_text(
            "👋 Welcome to the Drive Bot!\n\n"
            "📤 Admin Upload: /upload <title> + image\n"
            "🔍 Search: Type any image title\n"
            "🗑️ Admin Delete: /delete <title>\n\n"
            "📝 Note: Upload images with captions to set titles"
        )
    except Exception as e:
        logger.error(f"Error in start handler: {e}")