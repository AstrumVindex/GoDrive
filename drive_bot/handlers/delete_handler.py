import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes
from drive_bot.config import ADMIN_ID, DB_PATH
from drive_bot.drive_service import drive_service

logger = logging.getLogger(__name__)

async def delete_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete an image by title (admin only)."""
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only command.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /delete <title>")
        return

    title = " ".join(context.args).strip()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT drive_file_id FROM images WHERE title = ?",
            (title,)
        )
        result = cursor.fetchone()

        if not result:
            await update.message.reply_text("🚫 Image not found.")
            return

        drive_file_id = result[0]

        # Delete from Google Drive
        drive_service.files().delete(fileId=drive_file_id).execute()

        # Delete from database
        cursor.execute("DELETE FROM images WHERE title = ?", (title,))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"🗑️ '{title}' deleted successfully.")
        logger.info(f"Deleted image: {title}")

    except Exception as e:
        logger.exception(f"Error deleting image '{title}'")
        await update.message.reply_text(f"❌ Error: {e}")
