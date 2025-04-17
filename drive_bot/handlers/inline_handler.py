from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineQueryResultPhoto
from telegram.ext import ContextTypes
import sqlite3
from drive_bot.config import DB_PATH
import logging

logger = logging.getLogger(__name__)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    if not query:
        return
    
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
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔗 Get Link", callback_data=f"link_{title}")
                ]])
            )
        )
    
    conn.close()
    await update.inline_query.answer(results, cache_time=1)