from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from drive_bot.database import db_operation
import logging

logger = logging.getLogger(__name__)

@db_operation
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE, conn):
    """Handle text messages as image title searches"""
    title = update.message.text.strip()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT telegram_file_id, share_link FROM images WHERE title = ?', 
            (title,))
        result = cursor.fetchone()

        if not result:
            await update.message.reply_text("🚫 Image not found. Try another title.")
            return

        keyboard = [[InlineKeyboardButton("🔗 Get Drive Link", callback_data=f"link_{title}")]]
        await update.message.reply_photo(
            photo=result['telegram_file_id'],
            caption=f"📌 {title}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"Served image: {title}")

    except Exception as e:
        logger.exception(f"Error serving image '{title}'")
        await update.message.reply_text("⚠️ Error retrieving image.")