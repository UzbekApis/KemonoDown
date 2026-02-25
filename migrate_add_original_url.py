"""
Migration script to add original_url column to files table
"""
import sqlite3
import os

def migrate():
    db_path = "data/webapp.db"
    
    if not os.path.exists(db_path):
        print("Database not found. No migration needed.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(files)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'original_url' in columns:
            print("Column 'original_url' already exists. No migration needed.")
            return
        
        # Add the column
        print("Adding 'original_url' column to files table...")
        cursor.execute("ALTER TABLE files ADD COLUMN original_url TEXT")
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
