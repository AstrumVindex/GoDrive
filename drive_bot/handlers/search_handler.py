import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto
from telegram.ext import ContextTypes
from drive_bot.config import DB_PATH

logger = logging.getLogger(__name__)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages as image title searches."""
    title = update.message.text.strip()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT telegram_file_id, share_link FROM images WHERE title = ?",
            (title,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            await update.message.reply_text("🚫 Image not found. Try another title.")
            return

        file_id, share_link = result

        keyboard = [[InlineKeyboardButton("🔗 Get Drive Link", callback_data=f"link_{title}")]]
        await update.message.reply_photo(
            photo=file_id,
            caption=f"📌 {title}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"Served image: {title}")

    except Exception as e:
        logger.exception(f"Error serving image '{title}'")
        await update.message.reply_text("⚠️ Error retrieving image.")


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Support inline search: @botname query."""
    query = update.inline_query.query.strip().lower()
    if not query:
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, telegram_file_id, share_link FROM images WHERE title LIKE ? LIMIT 10",
            (f"%{query}%",)
        )

        results = []
        for idx, row in enumerate(cursor.fetchall()):
            title, file_id, share_link = row
            results.append(
                InlineQueryResultPhoto(
                    id=str(idx),
                    photo_file_id=file_id,
                    thumb_url=share_link,
                    title=title,
                    caption=f"📌 {title}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔗 Get Link", callback_data=f"link_{title}")]
                    ])
                )
            )

        conn.close()
        await update.inline_query.answer(results, cache_time=1)

    except Exception as e:
        logger.exception("Inline query failed")
