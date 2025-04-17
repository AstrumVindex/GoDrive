import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    InlineQueryHandler
)
from drive_bot.handlers.start_handler import start
from drive_bot.handlers.upload_handler import upload_image
from drive_bot.handlers.delete_handler import delete_image
from drive_bot.handlers.text_handler import handle_text
from drive_bot.handlers.button_handler import button_callback
from drive_bot.handlers.inline_handler import inline_query
from drive_bot.config import TELEGRAM_BOT_TOKEN, ADMIN_ID, FOLDER_ID
from drive_bot.database import init_db
import asyncio
from telegram.ext import Application

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Configure and start the bot"""
    try:
        # Initialize database
        init_db()

        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("upload", upload_image))
        app.add_handler(CommandHandler("delete", delete_image))

        # Message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(InlineQueryHandler(inline_query))
        
        # Photo handler (for images sent without command)
        app.add_handler(MessageHandler(
            filters.PHOTO & ~filters.COMMAND, 
            lambda u, c: upload_image(u, c) if u.message.from_user.id == ADMIN_ID 
            else u.message.reply_text("🚫 Only admin can upload images.")
        ))

        # Get port and app URL from environment variables
        port = int(os.environ.get('PORT', 5000))
        app_url = os.environ.get('RENDER_EXTERNAL_URL')
        
        logger.info(f"Starting bot on port {port}...")
        
        # Run both polling and webhook for Render compatibility
        if app_url:
            # Webhook mode for Render
            webhook_url = f"{app_url}/{TELEGRAM_BOT_TOKEN}"
            logger.info(f"Setting webhook URL to: {webhook_url}")
            
            app.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=TELEGRAM_BOT_TOKEN,
                webhook_url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
        else:
            # Polling mode for local development
            logger.info("Running in polling mode")
            app.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        raise

if __name__ == '__main__':
    main()