"""Download management module"""
import os
import queue
import threading
import time
import uuid
from typing import Dict, Callable, Optional
from datetime import datetime


class DownloadManager:
    """Yuklab olish jarayonini boshqarish"""
    
    def __init__(self, api_client, db_manager, download_path: str = './downloads'):
        """
        Initialize download manager
        
        Args:
            api_client: KemonoAPIClient instance
            db_manager: Database manager instance
            download_path: Base path for downloads
        """
        self.api_client = api_client
        self.db = db_manager
        self.download_path = download_path
        self.queue = queue.Queue()
        self.active_downloads = {}
        self.download_threads = {}
        self.lock = threading.Lock()
        
    def add_download(self, url: str, filters) -> str:
        """
        Yuklab olish qo'shish va task_id qaytarish
        
        Args:
            url: Kemono URL
            filters: Fayl turi filtrlari (list yoki dict)
                     List: ['all'] yoki ['images', 'videos']
                     Dict: {'type': 'images', 'enabled': True}
        
        Returns:
            task_id: Unique task identifier
        """
        task_id = str(uuid.uuid4())
        
        with self.lock:
            self.active_downloads[task_id] = {
                'url': url,
                'filters': filters,
                'status': 'pending',
                'total_files': 0,
                'downloaded_files': 0,
                'current_file': '',
                'progress_percent': 0,
                'error': None,
                'created_at': datetime.now(),
                'paused': False
            }
        
        return task_id
    
    def start_download(self, task_id: str):
        """
        Yuklab olishni boshlash (background thread)
        
        Args:
            task_id: Task identifier
        """
        if task_id not in self.active_downloads:
            raise ValueError(f"Task {task_id} not found")
        
        with self.lock:
            if task_id in self.download_threads and self.download_threads[task_id].is_alive():
                return  # Already running
            
            self.active_downloads[task_id]['status'] = 'downloading'
            self.active_downloads[task_id]['paused'] = False
        
        # Start download in background thread
        thread = threading.Thread(target=self._download_worker, args=(task_id,))
        thread.daemon = True
        self.download_threads[task_id] = thread
        thread.start()
    
    def pause_download(self, task_id: str):
        """
        Yuklab olishni to'xtatish
        
        Args:
            task_id: Task identifier
        """
        if task_id not in self.active_downloads:
            raise ValueError(f"Task {task_id} not found")
        
        with self.lock:
            self.active_downloads[task_id]['paused'] = True
            self.active_downloads[task_id]['status'] = 'paused'
    
    def resume_download(self, task_id: str):
        """
        Yuklab olishni davom ettirish
        
        Args:
            task_id: Task identifier
        """
        if task_id not in self.active_downloads:
            raise ValueError(f"Task {task_id} not found")
        
        with self.lock:
            self.active_downloads[task_id]['paused'] = False
            self.active_downloads[task_id]['status'] = 'downloading'
        
        # Resume in existing thread or start new one
        if task_id not in self.download_threads or not self.download_threads[task_id].is_alive():
            thread = threading.Thread(target=self._download_worker, args=(task_id,))
            thread.daemon = True
            self.download_threads[task_id] = thread
            thread.start()
    
    def cancel_download(self, task_id: str):
        """
        Yuklab olishni bekor qilish
        
        Args:
            task_id: Task identifier
        """
        if task_id not in self.active_downloads:
            raise ValueError(f"Task {task_id} not found")
        
        with self.lock:
            self.active_downloads[task_id]['status'] = 'cancelled'
            self.active_downloads[task_id]['paused'] = True
    
    def get_progress(self, task_id: str) -> Dict:
        """
        Progress ma'lumotlarini olish
        
        Args:
            task_id: Task identifier
        
        Returns:
            Progress dictionary
        """
        if task_id not in self.active_downloads:
            return {'error': 'Task not found'}
        
        with self.lock:
            download = self.active_downloads[task_id]
            return {
                'task_id': task_id,
                'status': download['status'],
                'total': download['total_files'],
                'downloaded': download['downloaded_files'],
                'percent': download['progress_percent'],
                'current_file': download['current_file'],
                'error': download['error']
            }
    
    def _download_worker(self, task_id: str):
        """
        Background worker for downloading files
        
        Args:
            task_id: Task identifier
        """
        try:
            download = self.active_downloads[task_id]
            url = download['url']
            filters = download['filters']
            
            # Parse URL to get service, user_id, post_id
            from api.url_parser import URLParser
            parser = URLParser()
            parsed = parser.parse(url)
            
            if not parsed:
                self._set_error(task_id, "Invalid URL")
                return
            
            # Get files list based on URL type
            files = []
            post_title = "Unknown"
            
            if parsed['type'] == 'post':
                # Get single post files
                post_data = self.api_client.get_post_details(
                    parsed['service'],
                    parsed['user_id'],
                    parsed['post_id']
                )
                
                # Extract title
                post_title = post_data.get('title', 'Unknown Post')
                
                # Get attachments
                attachments = post_data.get('attachments', [])
                if attachments:
                    files.extend(attachments)
                
                # Get main file
                if 'file' in post_data and post_data['file']:
                    file_info = post_data['file']
                    if isinstance(file_info, dict) and 'path' in file_info:
                        files.append(file_info)
                
            elif parsed['type'] == 'user':
                # Get all user posts
                posts = self.api_client.get_user_posts(
                    parsed['service'],
                    parsed['user_id']
                )
                
                for post in posts:
                    # Get attachments from each post
                    attachments = post.get('attachments', [])
                    if attachments:
                        files.extend(attachments)
                    
                    # Get main file
                    if 'file' in post and post['file']:
                        file_info = post['file']
                        if isinstance(file_info, dict) and 'path' in file_info:
                            files.append(file_info)
            
            # Apply filters
            if filters and isinstance(filters, list) and 'all' not in filters:
                from core.file_filter import FileFilter
                file_filter = FileFilter()
                files = file_filter.filter_files(files, filters)
            
            # Update total files count
            with self.lock:
                self.active_downloads[task_id]['total_files'] = len(files)
            
            # Update database with total files
            from models.database import Database
            db = Database()
            db.update_download_progress(task_id, 0, len(files))
            db.close()
            
            if len(files) == 0:
                self._set_error(task_id, "No files found to download")
                return
            
            # Download each file
            for idx, file_info in enumerate(files):
                # Check if paused or cancelled
                if self.active_downloads[task_id]['paused']:
                    if self.active_downloads[task_id]['status'] == 'cancelled':
                        return
                    # Wait while paused
                    while self.active_downloads[task_id]['paused']:
                        if self.active_downloads[task_id]['status'] == 'cancelled':
                            return
                        time.sleep(0.5)
                
                # Get file URL and name
                file_path = file_info.get('path', '')
                file_name = file_info.get('name') or os.path.basename(file_path)
                
                if not file_path:
                    continue
                
                # Build full URL for the file
                file_url = f"https://kemono.cr/data{file_path}"
                
                # Check if it's a ZIP file
                is_zip = file_name.lower().endswith('.zip')
                
                # For ZIP files, just save the URL to database without downloading
                if is_zip:
                    print(f"ZIP file detected, saving URL only: {file_name}")
                    
                    # Save to database with URL
                    self.db.insert_file(
                        filename=file_name,
                        filepath='',  # No local path for ZIP files
                        file_type='archive',
                        file_size=0,
                        service=parsed['service'],
                        user_id=parsed['user_id'],
                        post_id=parsed.get('post_id'),
                        post_title=post_title,
                        original_url=file_url
                    )
                    
                    # Update downloaded count
                    with self.lock:
                        self.active_downloads[task_id]['downloaded_files'] = idx + 1
                        self.active_downloads[task_id]['progress_percent'] = int((idx + 1) / len(files) * 100)
                    
                    # Update database progress
                    from models.database import Database
                    db = Database()
                    db.update_download_progress(task_id, idx + 1, len(files))
                    db.close()
                    
                    continue
                
                # Create save path
                save_dir = os.path.join(
                    self.download_path,
                    parsed['service'],
                    parsed['user_id'],
                    parsed.get('post_id', 'all_posts')
                )
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, file_name)
                
                # Skip if already exists
                if os.path.exists(save_path):
                    print(f"File already exists, skipping: {file_name}")
                    with self.lock:
                        self.active_downloads[task_id]['downloaded_files'] = idx + 1
                        self.active_downloads[task_id]['progress_percent'] = int((idx + 1) / len(files) * 100)
                    continue
                
                # Update current file
                with self.lock:
                    self.active_downloads[task_id]['current_file'] = file_name
                
                # Download file
                try:
                    self.api_client.download_file(
                        file_path,
                        save_path,
                        progress_callback=lambda p: self._update_file_progress(task_id, idx, len(files), p)
                    )
                    
                    # Save to database
                    self.db.insert_file(
                        filename=file_name,
                        filepath=save_path,
                        file_type=self._get_file_type(file_name),
                        file_size=os.path.getsize(save_path) if os.path.exists(save_path) else 0,
                        service=parsed['service'],
                        user_id=parsed['user_id'],
                        post_id=parsed.get('post_id'),
                        post_title=post_title,
                        original_url=file_url
                    )
                    
                    # Update downloaded count
                    with self.lock:
                        self.active_downloads[task_id]['downloaded_files'] = idx + 1
                        self.active_downloads[task_id]['progress_percent'] = int((idx + 1) / len(files) * 100)
                    
                    # Update database progress
                    from models.database import Database
                    db = Database()
                    db.update_download_progress(task_id, idx + 1, len(files))
                    db.close()
                
                except Exception as e:
                    # Log error but continue with next file
                    print(f"Error downloading {file_name}: {str(e)}")
            
            # Mark as completed
            with self.lock:
                self.active_downloads[task_id]['status'] = 'completed'
                self.active_downloads[task_id]['progress_percent'] = 100
            
            # Update database
            from models.database import Database
            db = Database()
            db.update_download_status(task_id, 'completed')
            db.update_download_progress(task_id, len(files), len(files))
            db.close()
        
        except Exception as e:
            print(f"Download worker error: {str(e)}")
            self._set_error(task_id, str(e))
            
            # Update database
            from models.database import Database
            db = Database()
            db.update_download_status(task_id, 'failed')
            db.close()
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        video_exts = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
        audio_exts = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
        archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz']
        
        if ext in image_exts:
            return 'image'
        elif ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'
        elif ext in archive_exts:
            return 'archive'
        else:
            return 'other'
    
    def _update_file_progress(self, task_id: str, file_idx: int, total_files: int, file_progress: float):
        """Update progress for current file"""
        with self.lock:
            if task_id in self.active_downloads:
                # Calculate overall progress
                completed_files = file_idx
                current_file_contribution = file_progress / 100.0
                overall_progress = (completed_files + current_file_contribution) / total_files * 100
                self.active_downloads[task_id]['progress_percent'] = int(overall_progress)
    
    def _set_error(self, task_id: str, error_message: str):
        """Set error status for download"""
        with self.lock:
            if task_id in self.active_downloads:
                self.active_downloads[task_id]['status'] = 'failed'
                self.active_downloads[task_id]['error'] = error_message
        
        # Update database
        from models.database import Database
        db = Database()
        db.update_download_status(task_id, 'failed')
        db.close()
    
    def get_all_downloads(self) -> Dict[str, Dict]:
        """Get all active downloads"""
        with self.lock:
            return dict(self.active_downloads)
    
    def remove_download(self, task_id: str):
        """Remove download from active list"""
        with self.lock:
            if task_id in self.active_downloads:
                del self.active_downloads[task_id]
            if task_id in self.download_threads:
                del self.download_threads[task_id]
