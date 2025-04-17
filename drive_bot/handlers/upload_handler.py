import logging
import sqlite3
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from googleapiclient.http import MediaIoBaseUpload
from drive_bot.config import ADMIN_ID, FOLDER_ID, DB_PATH
from drive_bot.drive_service import drive_service

logger = logging.getLogger(__name__)

def is_valid_title(title: str) -> bool:
    """Validate image title format"""
    if not title or len(title) > 100:
        return False
    return all(c.isalnum() or c in ' -_.,' for c in title)

async def upload_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced upload handler with duplicate checking and better error handling"""
    conn = None
    file_stream = None
    
    try:
        # Authentication check
        if update.message.from_user.id != ADMIN_ID:
            await update.message.reply_text("🚫 Only admin can upload images.")
            return

        # Photo validation
        if not update.message.photo:
            await update.message.reply_text("❌ Please send an image file.")
            return
            
        photo = update.message.photo[-1]  # Highest resolution

        # Title extraction and validation
        title = (
            " ".join(context.args).strip() 
            if context.args 
            else update.message.caption.strip() 
            if update.message.caption 
            else None
        )
        
        if not title:
            await update.message.reply_text(
                "⚠️ Please provide a title either:\n"
                "1. As command argument: /upload <title>\n"
                "2. Or as image caption"
            )
            return
            
        if not is_valid_title(title):
            await update.message.reply_text(
                "⚠️ Invalid title format. Please use:\n"
                "- Letters, numbers, spaces\n"
                "- Max 100 characters\n"
                "- Only these special characters: - _ . ,"
            )
            return

        # Database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Duplicate check
        cursor.execute('SELECT 1 FROM images WHERE title = ?', (title,))
        if cursor.fetchone():
            await update.message.reply_text(
                f"⚠️ Title '{title}' already exists.\n"
                "Use /list to see existing images or choose a different title."
            )
            return

        # Download image from Telegram
        await update.message.reply_text(f"⏳ Downloading image '{title}'...")
        tg_file = await context.bot.get_file(photo.file_id)
        file_stream = BytesIO()
        await tg_file.download_to_memory(out=file_stream)
        file_stream.seek(0)

        # Prepare Drive upload
        file_metadata = {
            'name': f"{title}.jpg",
            'parents': [FOLDER_ID],
            'description': f"Uploaded via Telegram by {update.message.from_user.full_name}",
            'contentHints': {
                'indexableText': title  # Improves searchability in Drive
            }
        }
        media = MediaIoBaseUpload(
            file_stream,
            mimetype='image/jpeg',
            resumable=True
        )

        # Upload to Drive
        await update.message.reply_text(f"⏳ Uploading to Google Drive...")
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink,webContentLink',
            supportsAllDrives=True
        ).execute()

        # Set public permission
        drive_service.permissions().create(
            fileId=uploaded_file['id'],
            body={'role': 'reader', 'type': 'anyone'},
            supportsAllDrives=True
        ).execute()

        # Store metadata in database
        cursor.execute('''
            INSERT INTO images (
                title, 
                telegram_file_id, 
                drive_file_id, 
                share_link,
                direct_link
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            title,
            photo.file_id,
            uploaded_file['id'],
            uploaded_file['webViewLink'],
            uploaded_file.get('webContentLink', '')
        ))
        conn.commit()

        await update.message.reply_text(
            f"✅ Successfully uploaded '{title}'\n\n"
            f"🔗 Share link: {uploaded_file['webViewLink']}"
        )
        logger.info(f"Uploaded: {title} (Drive ID: {uploaded_file['id']})")

    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        await update.message.reply_text("⚠️ Database error. Please try again.")
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Upload failed. Possible reasons:\n"
            "- Google Drive quota exceeded\n"
            "- Network issues\n"
            "- Invalid file format\n\n"
            "Please try again later."
        )
    finally:
        # Cleanup resources
        if conn:
            conn.close()
        if file_stream:
            file_stream.close()