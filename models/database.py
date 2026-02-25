"""
SQLite database schema and initialization
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
import json


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = "data/webapp.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.ensure_data_directory()
        self.conn = None
        self.cursor = None
        
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def create_tables(self):
        """Create all database tables"""
        self.connect()
        
        # Downloads table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                service TEXT,
                user_id TEXT,
                post_id TEXT,
                status TEXT DEFAULT 'pending',
                total_files INTEGER DEFAULT 0,
                downloaded_files INTEGER DEFAULT 0,
                filters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Artists table (cache)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                user_id TEXT NOT NULL,
                name TEXT,
                metadata TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(service, user_id)
            )
        """)
        
        # Files table (library)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                service TEXT,
                user_id TEXT,
                post_id TEXT,
                post_title TEXT,
                thumbnail_path TEXT,
                original_url TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Settings table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
        self.create_indexes()
    
    def create_indexes(self):
        """Create database indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)",
            "CREATE INDEX IF NOT EXISTS idx_downloads_task_id ON downloads(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_artists_service_user ON artists(service, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_service_user ON files(service, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_post ON files(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type)"
        ]
        
        for index_sql in indexes:
            self.cursor.execute(index_sql)
        
        self.conn.commit()
    
    def drop_tables(self):
        """Drop all tables (for testing/reset)"""
        self.connect()
        tables = ['downloads', 'artists', 'files', 'settings']
        for table in tables:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
        self.conn.commit()
    
    # Downloads CRUD operations
    def insert_download(self, task_id: str, url: str, service: str = None, 
                       user_id: str = None, post_id: str = None, 
                       filters: Any = None) -> int:
        """Insert new download record"""
        self.connect()
        # Convert filters to JSON (can be list or dict)
        filters_json = json.dumps(filters) if filters else None
        
        self.cursor.execute("""
            INSERT INTO downloads (task_id, url, service, user_id, post_id, filters)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, url, service, user_id, post_id, filters_json))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_download(self, task_id: str) -> Optional[Dict]:
        """Get download by task_id"""
        self.connect()
        self.cursor.execute("SELECT * FROM downloads WHERE task_id = ?", (task_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def update_download_status(self, task_id: str, status: str, 
                               downloaded_files: int = None):
        """Update download status"""
        self.connect()
        if downloaded_files is not None:
            self.cursor.execute("""
                UPDATE downloads 
                SET status = ?, downloaded_files = ?, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            """, (status, downloaded_files, task_id))
        else:
            self.cursor.execute("""
                UPDATE downloads 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            """, (status, task_id))
        self.conn.commit()
    
    def update_download_progress(self, task_id: str, total_files: int, 
                                 downloaded_files: int):
        """Update download progress"""
        self.connect()
        self.cursor.execute("""
            UPDATE downloads 
            SET total_files = ?, downloaded_files = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        """, (total_files, downloaded_files, task_id))
        self.conn.commit()
    
    def get_all_downloads(self, status: str = None) -> List[Dict]:
        """Get all downloads, optionally filtered by status"""
        self.connect()
        if status:
            self.cursor.execute("SELECT * FROM downloads WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            self.cursor.execute("SELECT * FROM downloads ORDER BY created_at DESC")
        return [dict(row) for row in self.cursor.fetchall()]
    
    def delete_download(self, task_id: str):
        """Delete download record"""
        self.connect()
        self.cursor.execute("DELETE FROM downloads WHERE task_id = ?", (task_id,))
        self.conn.commit()
    
    # Artists CRUD operations
    def insert_artist(self, service: str, user_id: str, name: str, 
                     metadata: Dict = None) -> int:
        """Insert or update artist record"""
        self.connect()
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.cursor.execute("""
            INSERT OR REPLACE INTO artists (service, user_id, name, metadata, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (service, user_id, name, metadata_json))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_artist(self, service: str, user_id: str) -> Optional[Dict]:
        """Get artist by service and user_id"""
        self.connect()
        self.cursor.execute("""
            SELECT * FROM artists WHERE service = ? AND user_id = ?
        """, (service, user_id))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_artists(self) -> List[Dict]:
        """Get all artists"""
        self.connect()
        self.cursor.execute("SELECT * FROM artists ORDER BY name")
        return [dict(row) for row in self.cursor.fetchall()]
    
    def search_artists(self, query: str) -> List[Dict]:
        """Search artists by name"""
        self.connect()
        self.cursor.execute("""
            SELECT * FROM artists WHERE name LIKE ? ORDER BY name
        """, (f"%{query}%",))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # Files CRUD operations
    def insert_file(self, filename: str, filepath: str, file_type: str = None,
                   file_size: int = None, service: str = None, user_id: str = None,
                   post_id: str = None, post_title: str = None, 
                   thumbnail_path: str = None, original_url: str = None) -> int:
        """Insert file record"""
        self.connect()
        self.cursor.execute("""
            INSERT INTO files (filename, filepath, file_type, file_size, service, 
                             user_id, post_id, post_title, thumbnail_path, original_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (filename, filepath, file_type, file_size, service, user_id, 
              post_id, post_title, thumbnail_path, original_url))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_file(self, file_id: int) -> Optional[Dict]:
        """Get file by id"""
        self.connect()
        self.cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_files_by_artist(self, service: str, user_id: str) -> List[Dict]:
        """Get all files by artist"""
        self.connect()
        self.cursor.execute("""
            SELECT * FROM files WHERE service = ? AND user_id = ? 
            ORDER BY downloaded_at DESC
        """, (service, user_id))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_files_by_post(self, post_id: str) -> List[Dict]:
        """Get all files by post"""
        self.connect()
        self.cursor.execute("""
            SELECT * FROM files WHERE post_id = ? ORDER BY downloaded_at DESC
        """, (post_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_files_by_type(self, file_type: str) -> List[Dict]:
        """Get all files by type"""
        self.connect()
        self.cursor.execute("""
            SELECT * FROM files WHERE file_type = ? ORDER BY downloaded_at DESC
        """, (file_type,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_all_files(self) -> List[Dict]:
        """Get all files"""
        self.connect()
        self.cursor.execute("SELECT * FROM files ORDER BY downloaded_at DESC")
        return [dict(row) for row in self.cursor.fetchall()]
    
    def delete_file(self, file_id: int):
        """Delete file record"""
        self.connect()
        self.cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        self.conn.commit()
    
    # Settings CRUD operations
    def set_setting(self, key: str, value: str):
        """Set or update setting"""
        self.connect()
        self.cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        self.conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get setting value"""
        self.connect()
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        return row['value'] if row else default
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings as dictionary"""
        self.connect()
        self.cursor.execute("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in self.cursor.fetchall()}
    
    def delete_setting(self, key: str):
        """Delete setting"""
        self.connect()
        self.cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
        self.conn.commit()


def init_db(db_path: str = "data/webapp.db"):
    """Initialize database with tables and indexes"""
    db = Database(db_path)
    db.create_tables()
    db.close()
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
