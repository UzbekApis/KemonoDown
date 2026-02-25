"""Library management module"""
import os
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime


class LibraryManager:
    """Kutubxonani boshqarish"""
    
    def __init__(self, library_path: str, db_manager, thumb_generator=None):
        """
        Initialize library manager
        
        Args:
            library_path: Path to library directory
            db_manager: Database manager instance
            thumb_generator: ThumbnailGenerator instance (optional)
        """
        self.library_path = library_path
        self.db = db_manager
        self.thumb_generator = thumb_generator
        self.thumbs_path = os.path.join(library_path, 'thumbs')
        
        # Create directories if they don't exist
        os.makedirs(self.library_path, exist_ok=True)
        os.makedirs(self.thumbs_path, exist_ok=True)
    
    def scan_library(self) -> List[Dict]:
        """
        Kutubxonani skanerlash va fayllar ro'yxatini qaytarish
        
        Returns:
            List of file dictionaries with metadata
        """
        # Get all files from database
        self.db.connect()
        
        self.db.cursor.execute("""
            SELECT id, filename, filepath, file_type, file_size,
                   service, user_id, post_id, post_title, 
                   thumbnail_path, downloaded_at
            FROM files
            ORDER BY downloaded_at DESC
        """)
        
        rows = self.db.cursor.fetchall()
        files = []
        
        for row in rows:
            file_dict = {
                'id': row[0],
                'filename': row[1],
                'filepath': row[2],
                'file_type': row[3],
                'file_size': row[4],
                'service': row[5],
                'user_id': row[6],
                'post_id': row[7],
                'post_title': row[8],
                'thumbnail_path': row[9],
                'downloaded_at': row[10],
                'exists': os.path.exists(row[2]) if row[2] else False
            }
            files.append(file_dict)
        
        self.db.close()
        return files
    
    def get_by_artist(self, artist_id: str, service: str = None) -> List[Dict]:
        """
        Artist bo'yicha fayllar
        
        Args:
            artist_id: Artist/user ID
            service: Service name (optional filter)
        
        Returns:
            List of files for the artist
        """
        self.db.connect()
        
        if service:
            self.db.cursor.execute("""
                SELECT id, filename, filepath, file_type, file_size,
                       service, user_id, post_id, post_title,
                       thumbnail_path, downloaded_at
                FROM files
                WHERE user_id = ? AND service = ?
                ORDER BY downloaded_at DESC
            """, (artist_id, service))
        else:
            self.db.cursor.execute("""
                SELECT id, filename, filepath, file_type, file_size,
                       service, user_id, post_id, post_title,
                       thumbnail_path, downloaded_at
                FROM files
                WHERE user_id = ?
                ORDER BY downloaded_at DESC
            """, (artist_id,))
        
        rows = self.db.cursor.fetchall()
        files = []
        
        for row in rows:
            file_dict = {
                'id': row[0],
                'filename': row[1],
                'filepath': row[2],
                'file_type': row[3],
                'file_size': row[4],
                'service': row[5],
                'user_id': row[6],
                'post_id': row[7],
                'post_title': row[8],
                'thumbnail_path': row[9],
                'downloaded_at': row[10],
                'exists': os.path.exists(row[2]) if row[2] else False
            }
            files.append(file_dict)
        
        self.db.close()
        return files
    
    def get_by_post(self, post_id: str) -> List[Dict]:
        """
        Post bo'yicha fayllar
        
        Args:
            post_id: Post ID
        
        Returns:
            List of files for the post, sorted by filename
        """
        self.db.connect()
        
        try:
            self.db.cursor.execute("""
                SELECT id, filename, filepath, file_type, file_size,
                       service, user_id, post_id, post_title,
                       thumbnail_path, downloaded_at, original_url
                FROM files
                WHERE post_id = ?
                ORDER BY filename ASC
            """, (post_id,))
            
            rows = self.db.cursor.fetchall()
            files = []
            
            for row in rows:
                file_dict = {
                    'id': row[0],
                    'filename': row[1],
                    'filepath': row[2],
                    'file_type': row[3],
                    'file_size': row[4],
                    'service': row[5],
                    'user_id': row[6],
                    'post_id': row[7],
                    'post_title': row[8],
                    'thumbnail_path': row[9],
                    'downloaded_at': row[10],
                    'original_url': row[11] if len(row) > 11 else None,
                    'exists': os.path.exists(row[2]) if row[2] else False
                }
                files.append(file_dict)
            
            return files
        except Exception as e:
            print(f"Error in get_by_post: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self.db.close()
    
    def delete_file(self, file_id: int) -> bool:
        """
        Faylni o'chirish
        
        Args:
            file_id: File ID in database
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get file info
            cursor.execute("""
                SELECT filepath, thumbnail_path
                FROM files
                WHERE id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            filepath, thumbnail_path = row
            
            # Delete physical file
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
            
            # Delete thumbnail
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            # Delete from database
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            conn.commit()
            
            return True
        
        except Exception as e:
            print(f"Error deleting file {file_id}: {str(e)}")
            return False
    
    def add_file(self, filepath: str, metadata: Dict) -> Optional[int]:
        """
        Add file to library
        
        Args:
            filepath: Path to the file
            metadata: File metadata (service, user_id, post_id, etc.)
        
        Returns:
            File ID if successful, None otherwise
        """
        try:
            if not os.path.exists(filepath):
                return None
            
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            
            # Determine file type
            from core.file_filter import FileFilter
            file_filter = FileFilter()
            file_type = file_filter.get_file_type(filename)
            
            # Generate thumbnail if it's an image
            thumbnail_path = None
            if file_type == 'images' and self.thumb_generator:
                thumbnail_path = self.thumb_generator.generate_thumbnail(
                    filepath,
                    self.thumbs_path
                )
            
            # Insert into database
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO files (
                    filename, filepath, file_type, file_size,
                    service, user_id, post_id, post_title,
                    thumbnail_path, downloaded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                filename,
                filepath,
                file_type,
                file_size,
                metadata.get('service'),
                metadata.get('user_id'),
                metadata.get('post_id'),
                metadata.get('post_title'),
                thumbnail_path,
                datetime.now()
            ))
            
            conn.commit()
            return cursor.lastrowid
        
        except Exception as e:
            print(f"Error adding file to library: {str(e)}")
            return None
    
    def generate_thumbnails(self):
        """Barcha rasmlar uchun thumbnail yaratish"""
        if not self.thumb_generator:
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all image files without thumbnails
        cursor.execute("""
            SELECT id, filepath
            FROM files
            WHERE file_type = 'images' AND thumbnail_path IS NULL
        """)
        
        rows = cursor.fetchall()
        
        for file_id, filepath in rows:
            if not os.path.exists(filepath):
                continue
            
            try:
                thumbnail_path = self.thumb_generator.generate_thumbnail(
                    filepath,
                    self.thumbs_path
                )
                
                if thumbnail_path:
                    cursor.execute("""
                        UPDATE files
                        SET thumbnail_path = ?
                        WHERE id = ?
                    """, (thumbnail_path, file_id))
            
            except Exception as e:
                print(f"Error generating thumbnail for {filepath}: {str(e)}")
        
        conn.commit()
    
    def get_statistics(self) -> Dict:
        """
        Get library statistics
        
        Returns:
            Dictionary with statistics
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Total files
        cursor.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]
        
        # Total size
        cursor.execute("SELECT SUM(file_size) FROM files")
        total_size = cursor.fetchone()[0] or 0
        
        # Files by type
        cursor.execute("""
            SELECT file_type, COUNT(*)
            FROM files
            GROUP BY file_type
        """)
        files_by_type = dict(cursor.fetchall())
        
        # Unique artists
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM files")
        unique_artists = cursor.fetchone()[0]
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'files_by_type': files_by_type,
            'unique_artists': unique_artists
        }
