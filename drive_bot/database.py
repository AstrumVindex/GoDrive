import sqlite3
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from drive_bot.config import DB_PATH
import logging

logger = logging.getLogger(__name__)


def init_db():
    """Initialize the database with enhanced schema and error handling"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        conn.execute("PRAGMA foreign_keys=ON")   # Enable foreign keys
        
        cursor = conn.cursor()
        
        # Main images table with improved schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                telegram_file_id TEXT NOT NULL,
                drive_file_id TEXT NOT NULL UNIQUE,
                share_link TEXT NOT NULL,
                direct_link TEXT,
                mime_type TEXT DEFAULT 'image/jpeg',
                file_size INTEGER,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                uploader_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                CONSTRAINT title_unique UNIQUE (title)
            )
        ''')
        
        # Create optimized indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_drive_file_id ON images(drive_file_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_upload_time ON images(upload_time)
        ''')
        
        # Metadata table for future expansion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Insert initial metadata if needed
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value) 
            VALUES ('schema_version', '1.1')
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
            
# Add this to your database.py
def migrate_database(conn):
    """Handle future schema migrations automatically"""
    cursor = conn.cursor()
    
    # Check current schema version
    cursor.execute("PRAGMA user_version")
    version = cursor.fetchone()[0]
    
    # Migration from version 0 to 1
    if version == 0:
        try:
            cursor.executescript('''
                ALTER TABLE images ADD COLUMN uploader_id INTEGER;
                ALTER TABLE images ADD COLUMN last_accessed TIMESTAMP;
                PRAGMA user_version = 1;
            ''')
            conn.commit()
            logger.info("Database migrated to version 1")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Migration failed: {e}")
            raise

def db_operation(func):
    """Enhanced decorator for safe database operations with retry logic"""
    async def wrapper(*args, **kwargs):
        conn = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row  # Return dict-like rows
                conn.execute("PRAGMA busy_timeout=5000")  # 5s timeout
                kwargs['conn'] = conn
                result = await func(*args, **kwargs)
                conn.commit()
                return result
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5
                    logger.warning(f"Database locked, retry {attempt + 1} in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Database operation failed (attempt {attempt + 1}): {e}")
                if 'update' in kwargs:
                    await kwargs['update'].message.reply_text("⚠️ Database busy, please try again")
                return None
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                if conn:
                    conn.rollback()
                if 'update' in kwargs:
                    await kwargs['update'].message.reply_text("⚠️ Database error occurred")
                return None
            finally:
                if conn:
                    conn.close()
        return None
    return wrapper

@db_operation
async def add_image(
    title: str,
    telegram_file_id: str,
    drive_file_id: str,
    share_link: str,
    direct_link: str = "",
    file_size: Optional[int] = None,
    uploader_id: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None
) -> bool:
    """Add a new image record with complete metadata"""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO images (
                title, telegram_file_id, drive_file_id,
                share_link, direct_link, file_size,
                uploader_id, last_accessed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, telegram_file_id, drive_file_id,
            share_link, direct_link, file_size,
            uploader_id, datetime.now()
        ))
        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"Duplicate image: {e}")
        return False

@db_operation
async def get_image_by_title(
    title: str,
    conn: Optional[sqlite3.Connection] = None
) -> Optional[Dict]:
    """Retrieve image details by title"""
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE images SET last_accessed = ? 
        WHERE title = ?
    ''', (datetime.now(), title))
    cursor.execute('''
        SELECT * FROM images 
        WHERE title = ? AND is_active = 1
        LIMIT 1
    ''', (title,))
    return cursor.fetchone()

@db_operation
async def list_images(
    limit: int = 100,
    offset: int = 0,
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict]:
    """List all active images with pagination"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, share_link, upload_time 
        FROM images 
        WHERE is_active = 1
        ORDER BY upload_time DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    return cursor.fetchall()

@db_operation
async def delete_image(
    title: str,
    conn: Optional[sqlite3.Connection] = None
) -> bool:
    """Soft-delete an image by title"""
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE images SET is_active = 0 
        WHERE title = ?
    ''', (title,))
    return cursor.rowcount > 0

@db_operation
async def search_images(
    query: str,
    limit: int = 20,
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict]:
    """Search images by title with fuzzy matching"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, share_link 
        FROM images 
        WHERE title LIKE ? AND is_active = 1
        LIMIT ?
    ''', (f'%{query}%', limit))
    return cursor.fetchall()

@db_operation
async def get_stats(
    conn: Optional[sqlite3.Connection] = None
) -> Dict:
    """Get database statistics"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total_images,
            SUM(file_size) as total_size,
            MIN(upload_time) as oldest_upload,
            MAX(upload_time) as newest_upload
        FROM images
        WHERE is_active = 1
    ''')
    return cursor.fetchone()