from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from drive_bot.database import db_operation
import logging

logger = logging.getLogger(__name__)

@db_operation
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, conn):
    """Handle inline button clicks for drive links"""
    query = update.callback_query
    await query.answer()
    title = query.data.replace("link_", "")
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT share_link FROM images WHERE title = ?', (title,))
        result = cursor.fetchone()

        if not result:
            await query.edit_message_caption(caption="❌ Link not found.")
            return

        await query.edit_message_caption(
            caption=f"📌 {title}\n🔗 {result['share_link']}",
            reply_markup=None
        )
        logger.info(f"Served link for: {title}")

    except Exception as e:
        logger.exception(f"Error handling callback for '{title}'")
        await query.edit_message_caption(caption="⚠️ Error retrieving link.")